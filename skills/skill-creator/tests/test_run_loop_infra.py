"""run_loop.py must stop optimizing when the eval infrastructure fails —
it must not call improve_description on untrustworthy signal.
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_PATH))

from scripts import run_loop as RL


def test_infrastructure_failure_stops_optimization(monkeypatch, tmp_path):
    eval_set = [
        {"query": "q1", "should_trigger": True},
        {"query": "q2", "should_trigger": False},
    ]
    canned = {
        "results": [
            {"query": "q1", "should_trigger": True, "pass": False,
             "triggers": 0, "runs": 1, "trigger_rate": 0.0},
            {"query": "q2", "should_trigger": False, "pass": False,
             "triggers": 0, "runs": 1, "trigger_rate": 0.0},
        ],
        "summary": {"total": 2, "passed": 0, "failed": 2,
                    "errored": 2, "infrastructure_failed": True},
    }

    monkeypatch.setattr(RL, "run_eval", lambda **kw: canned)
    monkeypatch.setattr(RL, "parse_skill_md", lambda p: ("demo", "desc", "content"))

    calls = {"improve": 0}

    def spy_improve(**kw):
        calls["improve"] += 1
        return "SHOULD NOT BE USED"

    monkeypatch.setattr(RL, "improve_description", spy_improve)

    out = RL.run_loop(
        eval_set=eval_set, skill_path=tmp_path, description_override=None,
        num_workers=1, timeout=5, max_iterations=3, runs_per_query=1,
        trigger_threshold=0.5, holdout=0, model="x", verbose=False,
        live_report_path=None, log_dir=None,
    )

    assert out["exit_reason"].startswith("infrastructure_failed")
    assert calls["improve"] == 0, "must not optimize on infrastructure failure"
