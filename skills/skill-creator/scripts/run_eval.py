#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md
from scripts.structured_logging import (
    StructuredLogger,
    EvalError,
    ErrorCategory,
    RunEvalException,
)


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
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.
    
    Implements exponential backoff with jitter on transient failures.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

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
            command_file.write_text(command_content)

            cmd = [
                "claude",
                "-p", query,
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root,
                env=env,
            )

            triggered = False
            buffer = ""
            stderr_data = ""
            # Track state for stream event detection
            pending_tool_name = None
            accumulated_json = ""

            try:
                while time.time() - start_time < timeout:
                    if process.poll() is not None:
                        remaining = process.stdout.read()
                        if remaining:
                            buffer += remaining.decode("utf-8", errors="replace")
                        break

                    ready, _, _ = select.select([process.stdout], [], [], 1.0)
                    if not ready:
                        continue

                    chunk = os.read(process.stdout.fileno(), 8192)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Early detection via stream events
                        if event.get("type") == "stream_event":
                            se = event.get("event", {})
                            se_type = se.get("type", "")

                            if se_type == "content_block_start":
                                cb = se.get("content_block", {})
                                if cb.get("type") == "tool_use":
                                    tool_name = cb.get("name", "")
                                    if tool_name in ("Skill", "Read"):
                                        pending_tool_name = tool_name
                                        accumulated_json = ""
                                    else:
                                        return False

                            elif se_type == "content_block_delta" and pending_tool_name:
                                delta = se.get("delta", {})
                                if delta.get("type") == "input_json_delta":
                                    accumulated_json += delta.get("partial_json", "")
                                    if clean_name in accumulated_json:
                                        return True

                            elif se_type in ("content_block_stop", "message_stop"):
                                if pending_tool_name:
                                    return clean_name in accumulated_json
                                if se_type == "message_stop":
                                    return False

                        # Fallback: full assistant message
                        elif event.get("type") == "assistant":
                            message = event.get("message", {})
                            for content_item in message.get("content", []):
                                if content_item.get("type") != "tool_use":
                                    continue
                                tool_name = content_item.get("name", "")
                                tool_input = content_item.get("input", {})
                                if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                                    triggered = True
                                elif tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                                    triggered = True
                                return triggered

                        elif event.get("type") == "result":
                            return triggered
                        
                elapsed = time.time() - start_time
                
                # Timeout: attempt retry
                if elapsed >= timeout:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + (uuid.uuid4().random() * 0.1)
                        if logger:
                            logger.warning(
                                f"Query timeout ({elapsed:.1f}s), retrying in {wait_time:.1f}s",
                                context={"query": query[:70], "attempt": attempt + 1}
                            )
                        time.sleep(wait_time)
                        continue
                    else:
                        error = EvalError(
                            category=ErrorCategory.TIMEOUT,
                            query=query,
                            message=f"Query timed out after {timeout}s (attempt {attempt + 1}/{max_retries + 1})",
                            elapsed_seconds=elapsed,
                        )
                        if logger:
                            logger.error_eval(error)
                        return False
                
                return triggered
                
            finally:
                # Clean up process on any exit path (return, exception, timeout)
                if process.poll() is None:
                    process.kill()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                
                # Capture stderr if available
                if process.stderr:
                    try:
                        stderr_data = process.stderr.read().decode("utf-8", errors="replace")
                    except Exception:
                        pass

        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            error = EvalError(
                category=ErrorCategory.SUBPROCESS_CRASH,
                query=query,
                message=f"Subprocess crashed: {e}",
                elapsed_seconds=elapsed,
                returncode=e.returncode,
                stderr=stderr_data,
            )
            if logger:
                logger.error_eval(error)
            
            if attempt < max_retries:
                wait_time = (2 ** attempt) + (uuid.uuid4().random() * 0.1)
                if logger:
                    logger.warning(
                        f"Subprocess error, retrying in {wait_time:.1f}s",
                        context={"query": query[:70], "attempt": attempt + 1}
                    )
                time.sleep(wait_time)
                continue
            return False
            
        except Exception as e:
            elapsed = time.time() - start_time
            error = EvalError(
                category=ErrorCategory.UNKNOWN,
                query=query,
                message=f"Unexpected error: {e}",
                elapsed_seconds=elapsed,
                stderr=stderr_data,
            )
            if logger:
                logger.error_eval(error)
            return False
            
        finally:
            if command_file.exists():
                command_file.unlink()
    
    return False


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
    results = []

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

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                if logger:
                    logger.warning(f"Query failed with exception: {e}", context={"query": query[:70]})
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
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

    eval_set = json.loads(Path(args.eval_set).read_text())
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


if __name__ == "__main__":
    main()
