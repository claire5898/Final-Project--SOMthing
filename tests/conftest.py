"""Shared test fixtures. Tests never call the real AI: a scripted fake model stands in."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from somthing import agents, config  # noqa: E402
from somthing.safety import RateLimiter, TokenBudget  # noqa: E402
from somthing.store import Store  # noqa: E402
from somthing.usage import UsageLog  # noqa: E402


@dataclass
class FakeUsageDetails:
    cached_tokens: int = 0


@dataclass
class FakeOutDetails:
    reasoning_tokens: int = 0


@dataclass
class FakeUsage:
    input_tokens: int = 100
    output_tokens: int = 20
    input_tokens_details: FakeUsageDetails = field(default_factory=FakeUsageDetails)
    output_tokens_details: FakeOutDetails = field(default_factory=FakeOutDetails)


@dataclass
class FakeCall:
    name: str
    arguments: str
    call_id: str
    type: str = "function_call"

    def model_dump(self, exclude_none: bool = True) -> dict:
        return {"type": self.type, "name": self.name, "arguments": self.arguments, "call_id": self.call_id}


@dataclass
class FakeResponse:
    output: list
    output_text: str = ""
    usage: FakeUsage = field(default_factory=FakeUsage)


def tool_call(name: str, **args) -> FakeResponse:
    return FakeResponse(output=[FakeCall(name=name, arguments=json.dumps(args), call_id=f"call_{name}")])


def final(**payload) -> FakeResponse:
    return FakeResponse(output=[type("Msg", (), {"type": "message"})()], output_text=json.dumps(payload))


class FakeClient:
    """Plays back a script of responses and records every request it receives."""

    def __init__(self, script: list[FakeResponse] | None = None, repeat_last: bool = False):
        self.script = list(script or [])
        self.repeat_last = repeat_last
        self.requests: list[dict] = []
        self.responses = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if len(self.script) > 1 or not self.repeat_last:
            return self.script.pop(0)
        return self.script[0]


@pytest.fixture
def store(tmp_path) -> Store:
    return Store(data_dir=config.DATA_DIR, runtime_dir=tmp_path / "runtime")


@pytest.fixture
def guards(tmp_path) -> agents.Guards:
    return agents.Guards(limiter=RateLimiter(), budget=TokenBudget(), log=UsageLog(tmp_path / "usage.jsonl"))
