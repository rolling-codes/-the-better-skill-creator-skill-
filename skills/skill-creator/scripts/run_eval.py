#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import random
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md
from scripts.structured_logging import (
    StructuredLogger,
    EvalError,
    ErrorCategory,
    QueryOutcome,
    RunEvalException,
)

# stderr fragments that indicate the CLI could not authenticate / is out of
# allowance — these are infrastructure failures, not a real "did not trigger".
_AUTH_MARKERS = (
    "not logged in",
    "please log in",
    "authentication",
    "unauthorized",
    "invalid api key",
    "no api key",
    "credit balance",
    "usage limit",
    "rate limit",
    "quota",
)


def _looks_like_auth_failure(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in _AUTH_MARKERS)


def _stdout_reader(stream, q: "queue.Queue") -> None:
    """Read a subprocess stdout pipe line-by-line onto a queue.

    Runs on a background thread so we never block on a pipe — the portable
    replacement for select.select(), which does not work on Windows pipes.
    A None sentinel signals EOF.
    """
    try:
        for raw in iter(stream.readline, b""):
            q.put(raw)
    except Exception:
        pass
    finally:
        q.put(None)


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
    max_retries: int = 2,
    logger: StructuredLogger | None = None,
) -> QueryOutcome:
    """Run a single query and return a categorized QueryOutcome.

    Creates a synthetic command file in .claude/commands/ so the skill appears
    in Claude's available_skills list, sends the query to `claude -p` over
    stdin, and streams stream-json output to decide whether the skill was
    triggered. Cross-platform: a background reader thread feeds a queue, so we
    never call select.select() on a pipe (unsupported on Windows).

    Retries only transient infrastructure failures (timeout, crash), never a
    clean trigger/non-trigger or an authentication failure.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    def _jitter(n: int) -> float:
        return (2 ** n) + (random.random() * 0.1)

    last_failure = QueryOutcome.failure(ErrorCategory.UNKNOWN, "no attempt ran")

    for attempt in range(max_retries + 1):
        start_time = time.time()
        try:
            project_commands_dir.mkdir(parents=True, exist_ok=True)
            # Use YAML block scalar to avoid breaking on quotes in description
            indented_desc = "\n  ".join(skill_description.split("\n"))
            command_content = (
                f"---\n"
                f"description: |\n"
                f"  {indented_desc}\n"
                f"---\n\n"
                f"# {skill_name}\n\n"
                f"This skill handles: {skill_description}\n"
            )
            command_file.write_text(command_content, encoding="utf-8")

            # Prompt is delivered over stdin (not argv), per portable design.
            cmd = [
                "claude",
                "-p",
                "--output-format", "stream-json",
                "--verbose",
                "--include-partial-messages",
            ]
            if model:
                cmd.extend(["--model", model])

            # Remove CLAUDECODE env var to allow nesting claude -p inside a
            # Claude Code session. The guard is for interactive terminal conflicts;
            # programmatic subprocess usage is safe.
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root,
                env=env,
            )

            outcome: QueryOutcome | None = None
            buffer = ""
            stderr_data = ""
            saw_valid_event = False
            saw_result = False
            pending_tool_name: str | None = None
            accumulated_json = ""

            def handle_line(text: str) -> QueryOutcome | None:
                """Classify one stream-json line; return a decisive outcome or None."""
                nonlocal saw_valid_event, saw_result, pending_tool_name, accumulated_json
                text = text.strip()
                if not text:
                    return None
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    return None
                saw_valid_event = True
                etype = event.get("type")

                if etype == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")
                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool_name = tool_name
                                accumulated_json = ""
                            # Unrelated tool event: keep reading, do not conclude.
                    elif se_type == "content_block_delta" and pending_tool_name:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            if clean_name in accumulated_json:
                                return QueryOutcome.triggered_ok()
                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool_name:
                            if clean_name in accumulated_json:
                                return QueryOutcome.triggered_ok()
                            # A Skill/Read of something else — reset and keep reading.
                            pending_tool_name = None
                            accumulated_json = ""

                elif etype == "assistant":
                    for content_item in event.get("message", {}).get("content", []):
                        if content_item.get("type") != "tool_use":
                            continue
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        if tool_name == "Skill" and clean_name in str(tool_input.get("skill", "")):
                            return QueryOutcome.triggered_ok()
                        if tool_name == "Read" and clean_name in str(tool_input.get("file_path", "")):
                            return QueryOutcome.triggered_ok()
                    # Unrelated tools in this message: keep reading.

                elif etype == "result":
                    saw_result = True
                    if event.get("is_error") or str(event.get("subtype", "")).startswith("error"):
                        return QueryOutcome.failure(
                            ErrorCategory.SUBPROCESS_CRASH,
                            f"result event reported error: {event.get('subtype', 'is_error')}",
                        )
                    return QueryOutcome.not_triggered_ok()
                return None

            # Deliver the prompt over stdin, then close it.
            try:
                if process.stdin:
                    process.stdin.write(query.encode("utf-8"))
                    process.stdin.close()
            except (BrokenPipeError, OSError):
                pass

            outq: queue.Queue = queue.Queue()
            reader = threading.Thread(
                target=_stdout_reader, args=(process.stdout, outq), daemon=True
            )
            reader.start()

            try:
                while time.time() - start_time < timeout:
                    try:
                        raw = outq.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    if raw is None:  # EOF sentinel
                        break
                    buffer += raw.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        one, buffer = buffer.split("\n", 1)
                        outcome = handle_line(one)
                        if outcome is not None:
                            break
                    if outcome is not None:
                        break

                # Drain a trailing line that never got a newline.
                if outcome is None and buffer.strip():
                    outcome = handle_line(buffer)

                timed_out = outcome is None and (time.time() - start_time >= timeout)
            finally:
                if process.poll() is None:
                    process.kill()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.wait()
                if process.stderr:
                    try:
                        stderr_data = process.stderr.read().decode("utf-8", errors="replace")
                    except Exception:
                        pass
                reader.join(timeout=1)

            returncode = process.poll()
            elapsed = time.time() - start_time

            if outcome is not None and outcome.ok:
                return outcome
            if outcome is not None:  # decisive in-stream failure
                last_failure = outcome
            elif timed_out:
                last_failure = QueryOutcome.failure(
                    ErrorCategory.TIMEOUT, f"query timed out after {timeout}s"
                )
            elif _looks_like_auth_failure(stderr_data):
                last_failure = QueryOutcome.failure(
                    ErrorCategory.AUTHENTICATION, "authentication or allowance failure"
                )
            elif returncode not in (0, None):
                last_failure = QueryOutcome.failure(
                    ErrorCategory.SUBPROCESS_CRASH,
                    f"claude exited {returncode}: {stderr_data[:200]}",
                )
            elif saw_result or saw_valid_event:
                # Clean completion, no trigger seen.
                return QueryOutcome.not_triggered_ok()
            else:
                last_failure = QueryOutcome.failure(
                    ErrorCategory.PARSING, "no parseable stream-json output"
                )

            if logger:
                logger.error_eval(EvalError(
                    category=last_failure.category,
                    query=query,
                    message=last_failure.detail,
                    elapsed_seconds=elapsed,
                    returncode=returncode,
                    stderr=stderr_data or None,
                ))

            # Retry only transient infrastructure failures.
            if (last_failure.category in (ErrorCategory.TIMEOUT, ErrorCategory.SUBPROCESS_CRASH)
                    and attempt < max_retries):
                wait = _jitter(attempt)
                if logger:
                    logger.warning(
                        f"{last_failure.category.value}, retrying in {wait:.1f}s",
                        context={"query": query[:70], "attempt": attempt + 1},
                    )
                time.sleep(wait)
                continue
            return last_failure

        except FileNotFoundError as e:
            # `claude` CLI not on PATH — a hard environment failure. Not a clean
            # non-trigger, and retrying will not conjure the binary.
            if logger:
                logger.error_eval(EvalError(
                    category=ErrorCategory.SUBPROCESS_CRASH, query=query,
                    message=f"claude CLI not found: {e}",
                    elapsed_seconds=time.time() - start_time,
                ))
            return QueryOutcome.failure(ErrorCategory.SUBPROCESS_CRASH, f"claude CLI not found: {e}")

        except Exception as e:  # noqa: BLE001 — categorize, never crash the worker
            elapsed = time.time() - start_time
            last_failure = QueryOutcome.failure(ErrorCategory.UNKNOWN, f"unexpected error: {e}")
            if logger:
                logger.error_eval(EvalError(
                    category=ErrorCategory.UNKNOWN, query=query, message=str(e),
                    elapsed_seconds=elapsed,
                ))
            if attempt < max_retries:
                time.sleep(_jitter(attempt))
                continue
            return last_failure

        finally:
            # Remove the synthetic command file on every exit path.
            if command_file.exists():
                try:
                    command_file.unlink()
                except OSError:
                    pass

    return last_failure


def _aggregate_results(
    query_outcomes: dict[str, list[QueryOutcome]],
    query_items: dict[str, dict],
    trigger_threshold: float,
) -> tuple[list[dict], dict]:
    """Turn per-query outcomes into result rows + a summary.

    Pure and side-effect-free so it can be unit-tested directly without a
    subprocess or the process pool. A run that failed to execute (timeout, auth,
    crash, malformed) is never counted as a (non-)trigger, so a failed execution
    can never satisfy a negative test case.
    """
    results: list[dict] = []
    infra_failed = False
    for query, outcomes in query_outcomes.items():
        item = query_items[query]
        should_trigger = item["should_trigger"]
        ok_runs = [o for o in outcomes if o.ok]
        fail_runs = [o for o in outcomes if not o.ok]

        # An authentication failure anywhere means the eval infrastructure is
        # broken — the whole run is untrustworthy, not just this query.
        if any(o.category == ErrorCategory.AUTHENTICATION for o in fail_runs):
            infra_failed = True

        if ok_runs:
            # Rate is computed over clean completions ONLY.
            trigger_rate = sum(1 for o in ok_runs if o.triggered) / len(ok_runs)
            did_pass = trigger_rate >= trigger_threshold if should_trigger \
                else trigger_rate < trigger_threshold
            execution_error = None
        else:
            # Every run failed: cannot judge, and never a pass.
            trigger_rate = 0.0
            did_pass = False
            execution_error = fail_runs[0].category.value if fail_runs else "unknown"

        result = {
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(1 for o in ok_runs if o.triggered),
            "runs": len(outcomes),
            "ok_runs": len(ok_runs),
            "failed_runs": len(fail_runs),
            "pass": did_pass,
        }
        if execution_error:
            result["execution_error"] = execution_error
        if fail_runs:
            result["errors"] = [o.category.value for o in fail_runs]
        results.append(result)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    errored = sum(1 for r in results if r["ok_runs"] == 0)
    if total and errored == total:
        infra_failed = True

    summary = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "errored": errored,
        "infrastructure_failed": infra_failed,
    }
    return results, summary


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
    logger: StructuredLogger | None = None,
) -> dict:
    """Run the full eval set and return results."""
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                    logger=logger,
                )
                future_to_info[future] = (item, run_idx)

        query_outcomes: dict[str, list[QueryOutcome]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_outcomes.setdefault(query, [])
            try:
                query_outcomes[query].append(future.result())
            except Exception as e:
                if logger:
                    logger.warning(f"Query failed with exception: {e}", context={"query": query[:70]})
                query_outcomes[query].append(
                    QueryOutcome.failure(ErrorCategory.UNKNOWN, str(e))
                )

    results, summary = _aggregate_results(query_outcomes, query_items, trigger_threshold)
    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    parser.add_argument("--log-file", default=None, help="Write structured logs to this file")
    args = parser.parse_args()

    try:
        eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: could not read eval set {args.eval_set}: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(eval_set, list) or not eval_set:
        print("Error: eval set must be a non-empty JSON list", file=sys.stderr)
        sys.exit(1)
    for i, item in enumerate(eval_set):
        if not isinstance(item, dict) or "query" not in item or "should_trigger" not in item:
            print(f"Error: eval set item {i} is malformed (needs query + should_trigger)",
                  file=sys.stderr)
            sys.exit(1)

    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    # Initialize structured logger
    log_file = Path(args.log_file) if args.log_file else None
    logger = StructuredLogger("run_eval", log_file=log_file)

    if args.verbose:
        logger.info(f"Evaluating: {description}")

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
        logger=logger,
    )

    if args.verbose:
        summary = output["summary"]
        logger.info(f"Results: {summary['passed']}/{summary['total']} passed")
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            logger.info(
                f"[{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}",
                context={"rule": "result", "status": status}
            )

    print(json.dumps(output, indent=2))

    # Exit codes: 0 = all expectations passed, 1 = execution/input/infra error,
    # 2 = checks completed but some expectations failed.
    summary = output["summary"]
    if summary.get("infrastructure_failed"):
        sys.exit(1)
    if summary["total"] and summary.get("errored", 0) == summary["total"]:
        sys.exit(1)
    sys.exit(0 if summary["passed"] == summary["total"] else 2)


if __name__ == "__main__":
    main()
