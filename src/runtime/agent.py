"""Minimal skill-aware ReAct loop backed by a local OpenAI-compatible model."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from common.schemas import OrganizationView
from organization.skill_loader import SkillLoader


LOAD_PATTERN = re.compile(r"^\s*LOAD_SKILL\s+([A-Za-z0-9_.:-]+)\s*$", re.MULTILINE)
USED_PATTERN = re.compile(r"^\s*USED_SKILLS\s*:\s*(\[[^\n]*\])\s*$", re.MULTILINE)
CODE_PATTERN = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


SYSTEM_PROMPT = """You are an autonomous coding agent in AppWorld.
Solve the task by emitting one Python code block per step. The code is executed in a stateful
environment containing `apis`. Inspect API documentation when needed. When finished, call
`apis.supervisor.complete_task(...)`. Never fabricate observations.

If progressive skill loading is available, request it with a standalone line:
LOAD_SKILL <skill_id>

At the end of every response, report only skills actually used in that step:
USED_SKILLS: ["skill-id"]
Use an empty list when no skill was used. This field is logged and never controls execution.
"""


@dataclass
class ModelReply:
    text: str
    input_tokens: int
    output_tokens: int


class LocalModelClient:
    def __init__(
        self,
        base_url: str,
        model_id: str,
        api_key: str = "local",
        temperature: float = 0.7,
        top_p: float = 0.8,
        top_k: int = 20,
        repetition_penalty: float = 1.05,
        max_output_tokens: int = 4096,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install project dependencies before running the local model client") from exc
        if not base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("Only a loopback local model endpoint is allowed")
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_id = model_id
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: list[dict[str, str]], seed: int) -> ModelReply:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_output_tokens,
            seed=seed,
            extra_body={"top_k": self.top_k, "repetition_penalty": self.repetition_penalty},
        )
        usage = response.usage
        return ModelReply(
            text=response.choices[0].message.content or "",
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        )


class SkillAwareReactAgent:
    def __init__(self, model: LocalModelClient, max_steps: int = 30) -> None:
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        self.model = model
        self.max_steps = max_steps

    def solve(
        self,
        instruction: str,
        view: OrganizationView,
        loader: SkillLoader,
        execute: Callable[[str], str],
        task_completed: Callable[[], bool],
        seed: int,
    ) -> dict[str, Any]:
        user_content = f"Task: {instruction}"
        if view.initial_context:
            user_content += f"\n\n{view.initial_context}"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}]
        steps: list[dict[str, Any]] = []
        used_skill_ids: set[str] = set()
        input_tokens = output_tokens = execution_steps = 0

        for step_number in range(1, self.max_steps + 1):
            reply = self.model.complete(messages, seed)
            input_tokens += reply.input_tokens
            output_tokens += reply.output_tokens
            used = parse_used_skills(reply.text, set(view.allowed_skill_ids))
            used_skill_ids.update(used)
            messages.append({"role": "assistant", "content": reply.text})

            load_match = LOAD_PATTERN.search(reply.text)
            if load_match:
                observation = loader.load(load_match.group(1), step_number)
                action_type = "load_skill"
            else:
                code = parse_code(reply.text)
                if not code:
                    observation = "No executable Python code block or LOAD_SKILL command was found."
                    action_type = "format_error"
                else:
                    observation = str(execute(code))
                    execution_steps += 1
                    action_type = "execute"
            messages.append({"role": "user", "content": f"Observation:\n{observation}"})
            steps.append(
                {
                    "step": step_number,
                    "assistant": reply.text,
                    "action_type": action_type,
                    "observation": observation,
                    "used_skill_ids": used,
                }
            )
            if task_completed():
                break

        return {
            "messages": messages,
            "steps": steps,
            "used_skill_ids": sorted(used_skill_ids),
            "skill_load_events": loader.event_dicts(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "execution_steps": execution_steps,
            "claimed_complete": bool(task_completed()),
            "max_steps_reached": len(steps) >= self.max_steps and not task_completed(),
        }


def parse_code(text: str) -> str | None:
    match = CODE_PATTERN.search(text)
    return match.group(1).strip() if match else None


def parse_used_skills(text: str, allowed: set[str]) -> list[str]:
    match = USED_PATTERN.search(text)
    if not match:
        return []
    try:
        values = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return sorted({value for value in values if isinstance(value, str) and value in allowed})
