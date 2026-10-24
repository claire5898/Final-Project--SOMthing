"""Live evaluation of SOMbot: accuracy + token cost, optimized vs. unoptimized settings.

Run from the repo root (uses real gpt-6-luna calls on the course key, roughly 60-80k tokens total):
    python evals/run_eval.py

Writes evals/results/eval_<timestamp>.json and prints a summary table.
"""

from __future__ import annotations

import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from somthing import agents, config  # noqa: E402
from somthing.safety import RateLimiter, TokenBudget  # noqa: E402
from somthing.store import Store  # noqa: E402
from somthing.usage import UsageLog  # noqa: E402

# Each case: the request, listings that must appear, listings that must NOT appear, and expected no_match.
CASES = [
    {"q": "Find a desk under $100", "must": ["L001", "L003"], "never": ["L002"], "no_match": False},
    {"q": "I need help with Excel", "must": ["L034", "L036"], "never": [], "no_match": False},
    {"q": "I'm moving in: I need a desk, a chair and a lamp for under $200 total", "bundle_max": 200, "bundle_size": 3, "must": [], "never": [], "no_match": False},
    {"q": "Someone to fix my bike this week", "must": ["L042"], "never": [], "no_match": False},
    {"q": "LinkedIn headshots", "must": ["L044"], "never": [], "no_match": False},
    {"q": "A car under $5,000", "must": [], "never": [], "no_match": True},
    {"q": "Find me a laptop", "must": [], "never": ["L053"], "no_match": True},
    {"q": "French conversation lessons", "must": ["L051"], "never": [], "no_match": False},
    {"q": "Warm winter coat under $400", "must": ["L024"], "never": [], "no_match": False},
    {"q": "Help preparing for consulting case interviews", "must": ["L048"], "never": [], "no_match": False},
]

CONFIGS = {
    # What the app ships with: compact tool results (short descriptions, 6 results) + low reasoning effort.
    "optimized": {"compact": True, "effort": "low", "result_limit": config.SEARCH_RESULT_LIMIT},
    # Unoptimized baseline: full listing text and tags, more results, medium reasoning effort.
    "unoptimized": {"compact": False, "effort": "medium", "result_limit": 12},
}


def grade(case: dict, r: dict) -> tuple[bool, str]:
    ids = [l["id"] for l in r.get("listings", [])]
    if r.get("blocked") or r.get("error"):
        return False, "blocked/error"
    missing = [i for i in case["must"] if i not in ids]
    forbidden = [i for i in case["never"] if i in ids]
    if missing:
        return False, f"missing {missing}"
    if forbidden:
        return False, f"showed forbidden {forbidden}"
    if bool(r.get("no_match")) != case["no_match"]:
        return False, f"no_match={r.get('no_match')}"
    if "bundle_max" in case:
        b = r.get("bundle")
        if not b or b["total"] > case["bundle_max"] or len(b["items"]) != case["bundle_size"]:
            return False, f"bad bundle {b and (b['total'], len(b['items']))}"
    if r.get("warnings"):
        return False, f"guardrail warning: {r['warnings']}"
    return True, "ok"


def run_config(name: str, settings: dict, client) -> dict:
    tmp = Path(tempfile.mkdtemp())
    store = Store(runtime_dir=tmp / "runtime")
    rows = []
    for i, case in enumerate(CASES):
        guards = agents.Guards(limiter=RateLimiter(max_requests=1000), budget=TokenBudget(10**9, 10**9), log=UsageLog(tmp / "log.jsonl"))
        started = time.monotonic()
        r = agents.chat(case["q"], session_key=f"eval-{name}-{i}", history=[], store=store, guards=guards, client=client,
                        compact=settings["compact"], effort=settings["effort"], result_limit=settings["result_limit"])
        latency = time.monotonic() - started
        ok, why = grade(case, r)
        u = r.get("usage", {})
        rows.append({"q": case["q"], "pass": ok, "why": why, "ids": [l["id"] for l in r.get("listings", [])],
                     "input": u.get("input_tokens", 0), "cached": u.get("cached_tokens", 0), "output": u.get("output_tokens", 0),
                     "calls": u.get("model_calls", 0), "latency_s": round(latency, 1), "reply": r.get("reply", "")})
        print(f"  [{name}] {'PASS' if ok else 'FAIL'} {case['q'][:55]:<55} in={rows[-1]['input']:>5} cached={rows[-1]['cached']:>5} out={rows[-1]['output']:>4}  {why}")
    n = len(rows)
    return {
        "settings": settings,
        "accuracy": sum(r["pass"] for r in rows) / n,
        "avg_input": statistics.mean(r["input"] for r in rows),
        "avg_cached": statistics.mean(r["cached"] for r in rows),
        "avg_output": statistics.mean(r["output"] for r in rows),
        "avg_calls": statistics.mean(r["calls"] for r in rows),
        "avg_latency_s": round(statistics.mean(r["latency_s"] for r in rows), 1),
        "rows": rows,
    }


def main() -> None:
    config.load_env()
    client = agents.make_client()
    if client is None:
        sys.exit("No PORTKEY_API_KEY found (checked this folder and the parent folder).")
    results = {}
    for name, settings in CONFIGS.items():
        print(f"\n== {name}: {settings}")
        results[name] = run_config(name, settings, client)
    out_dir = ROOT / "evals" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"eval_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"model": config.MODEL_NAME, "cases": len(CASES), "results": results}, indent=2))
    print("\nconfig        accuracy  avg_in  avg_cached  avg_out  calls  latency")
    for name, r in results.items():
        print(f"{name:<13} {r['accuracy']:>7.0%}  {r['avg_input']:>6.0f}  {r['avg_cached']:>10.0f}  {r['avg_output']:>7.0f}  {r['avg_calls']:>5.1f}  {r['avg_latency_s']:>6.1f}s")
    print(f"\nSaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
