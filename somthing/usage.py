"""Token usage + safety event log (JSON lines), used for the in-app AI & Safety dashboard."""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import config


@dataclass
class Usage:
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    model_calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, raw) -> None:
        """Add one Responses API usage object."""
        if raw is None:
            return
        self.model_calls += 1
        self.input_tokens += getattr(raw, "input_tokens", 0) or 0
        self.output_tokens += getattr(raw, "output_tokens", 0) or 0
        details = getattr(raw, "input_tokens_details", None)
        self.cached_tokens += (getattr(details, "cached_tokens", 0) or 0) if details else 0
        out_details = getattr(raw, "output_tokens_details", None)
        self.reasoning_tokens += (getattr(out_details, "reasoning_tokens", 0) or 0) if out_details else 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_tokens"] = self.total_tokens
        d["cost_usd"] = config.estimate_cost(self.input_tokens, self.cached_tokens, self.output_tokens)
        return d


@dataclass
class RunRecord:
    agent: str
    session: str
    outcome: str  # ok | no_match | blocked | fallback | error
    usage: Usage = field(default_factory=Usage)
    tool_calls: list[dict] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    latency_ms: int = 0
    question: str = ""
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])


class UsageLog:
    def __init__(self, path: Path | None = None):
        self.path = path or (config.RUNTIME_DIR / "usage_log.jsonl")
        self.feedback_path = self.path.with_name(self.path.stem + "_feedback.jsonl")  # thumbs up/down on AI answers
        self._lock = threading.Lock()

    def add_feedback(self, run_id: str, session: str, rating: str, comment: str) -> dict:
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "run_id": run_id, "session": self.session_hash(session),
               "rating": rating, "comment": comment[:300]}
        with self._lock:
            self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
            with self.feedback_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return row

    def read_feedback(self) -> list[dict]:
        if not self.feedback_path.is_file():
            return []
        rows = []
        for line in self.feedback_path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    @staticmethod
    def session_hash(session_key: str) -> str:
        return hashlib.sha256(session_key.encode()).hexdigest()[:8]

    def write(self, record: RunRecord) -> dict:
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "run_id": record.run_id,
            "agent": record.agent,
            "session": self.session_hash(record.session),
            "outcome": record.outcome,
            "question": record.question[:160],
            "tool_calls": record.tool_calls,
            "guardrails": record.guardrails,
            "latency_ms": record.latency_ms,
            "model": config.MODEL_NAME,
            **record.usage.to_dict(),
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return row

    def read(self) -> list[dict]:
        if not self.path.is_file():
            return []
        rows = []
        for line in self.path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def tokens_today(self) -> int:
        today = time.strftime("%Y-%m-%d")
        return sum(r.get("total_tokens", 0) for r in self.read() if r.get("ts", "").startswith(today))

    def summary(self) -> dict:
        rows = self.read()
        ai_rows = [r for r in rows if r.get("model_calls", 0) > 0]

        def avg(key: str, subset: list[dict]) -> float:
            return round(sum(r.get(key, 0) for r in subset) / len(subset), 1) if subset else 0

        by_agent = {}
        for agent in sorted({r["agent"] for r in rows}):
            subset = [r for r in ai_rows if r["agent"] == agent]
            by_agent[agent] = {
                "runs": len([r for r in rows if r["agent"] == agent]),
                "ai_runs": len(subset),
                "avg_input_tokens": avg("input_tokens", subset),
                "avg_cached_tokens": avg("cached_tokens", subset),
                "avg_output_tokens": avg("output_tokens", subset),
                "avg_model_calls": avg("model_calls", subset),
                "avg_latency_ms": avg("latency_ms", subset),
            }
        guardrail_counts: dict[str, int] = {}
        for r in rows:
            for g in r.get("guardrails", []):
                key = g.split(":")[0]
                guardrail_counts[key] = guardrail_counts.get(key, 0) + 1
        totals = Usage(
            input_tokens=sum(r.get("input_tokens", 0) for r in rows),
            cached_tokens=sum(r.get("cached_tokens", 0) for r in rows),
            output_tokens=sum(r.get("output_tokens", 0) for r in rows),
            model_calls=sum(r.get("model_calls", 0) for r in rows),
        )
        feedback = self.read_feedback()
        latest = {}
        for f in feedback:  # one vote per answer (last one wins)
            latest[f["run_id"]] = f
        votes = list(latest.values())
        up = sum(v["rating"] == "up" for v in votes)
        questions = {r["run_id"]: r.get("question", "") for r in rows if r.get("run_id")}
        return {
            "feedback": {
                "votes": len(votes), "up": up, "down": len(votes) - up,
                "satisfaction": round(100 * up / len(votes)) if votes else None,
                "recent": [{**v, "question": questions.get(v["run_id"], "")} for v in votes[-8:][::-1]],
            },
            "model": config.MODEL_NAME,
            "prices_configured": config.PRICE_INPUT_PER_M is not None,
            "totals": totals.to_dict(),
            "runs": len(rows),
            "by_agent": by_agent,
            "guardrail_counts": guardrail_counts,
            "recent": rows[-25:][::-1],
            "limits": {
                "session_token_budget": config.SESSION_TOKEN_BUDGET,
                "daily_token_budget": config.DAILY_TOKEN_BUDGET,
                "max_tool_rounds": config.MAX_TOOL_ROUNDS,
                "max_tool_calls": config.MAX_TOOL_CALLS,
                "rate_limit": f"{config.RATE_LIMIT_REQUESTS} requests / {config.RATE_LIMIT_WINDOW_SECONDS}s",
                "max_message_chars": config.MAX_MESSAGE_CHARS,
            },
        }
