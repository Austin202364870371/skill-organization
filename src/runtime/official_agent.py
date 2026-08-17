"""Minimal subclass of AppWorld's official simplified ReAct code agent."""

from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from typing import Any

from common.schemas import OrganizationView
from organization.skill_loader import SkillLoader
from runtime.agent import LOAD_PATTERN, parse_used_skills


LOAD_SENTINEL = "__LOAD_SKILL__:"
COMPLETION_RULE = """
AppWorld completion rule:
- For an action task, call `apis.supervisor.complete_task()` without an answer.
- Pass `answer=...` only when the task explicitly asks for information to be returned.
"""
SKILL_RULES = """
Skill controller rules:
- To load a disclosed skill, emit a standalone line: LOAD_SKILL <skill_id>
- At the end of every response emit: USED_SKILLS: ["skill-id"]
- USED_SKILLS is logging only and does not control execution.
"""


def solve_with_official(
    world: Any,
    view: OrganizationView,
    loader: SkillLoader,
    model_config: dict[str, Any],
    prompt_file_path: str,
    max_steps: int,
    seed: int,
    experiment_name: str,
) -> dict[str, Any]:
    try:
        from appworld_agents.code.simplified.agent import ExecutionIO
        from appworld_agents.code.simplified.react_code_agent import SimplifiedReActCodeAgent
    except ImportError as exc:
        raise RuntimeError("Pinned appworld-agents[simplified] is required for formal runs") from exc

    class SkillAwareOfficialAgent(SimplifiedReActCodeAgent):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.used_skill_ids: set[str] = set()
            original_generate = self.language_model.generate

            def normalized_generate(*args: Any, **generation_kwargs: Any) -> dict[str, Any]:
                output = original_generate(*args, **generation_kwargs)
                if output.get("reasoning_content") is None:
                    output["reasoning_content"] = ""
                return output

            self.language_model.generate = normalized_generate

        def initialize(self, current_world: Any) -> None:
            super().initialize(current_world)
            skill_addition = (
                SKILL_RULES
                if view.loader_enabled
                else "At the end of every response emit USED_SKILLS: []. No skills are available in this condition."
            )
            addition = COMPLETION_RULE + "\n" + skill_addition
            if view.initial_context:
                addition += "\n" + view.initial_context
            for message in reversed(self.messages):
                if message.get("role") == "user":
                    message["content"] = str(message.get("content") or "") + "\n\n" + addition
                    break

        def extract_code_and_fix_content(self, text: str) -> tuple[str, str]:
            self.used_skill_ids.update(parse_used_skills(text, set(view.allowed_skill_ids)))
            load_match = LOAD_PATTERN.search(text)
            if load_match:
                return LOAD_SENTINEL + load_match.group(1), text
            return super().extract_code_and_fix_content(text)

    agent = SkillAwareOfficialAgent(
        prompt_file_path=prompt_file_path,
        model_config={**model_config, "seed": seed},
        appworld_config={"random_seed": seed},
        max_steps=max_steps,
        ignore_multiple_calls=True,
        log_lm_calls=True,
    )
    agent.logger.initialize(experiment_name=experiment_name, num_tasks=1, num_processes=1, process_index=0)
    agent.initialize(world)
    outputs: list[Any] = []
    steps = []
    input_tokens = output_tokens = execution_steps = 0

    for _ in range(max_steps):
        agent.step_number += 1
        execution_inputs, usage, status = agent.next_execution_inputs_usage_and_status(outputs)
        if status.failed:
            steps.append({"step": agent.step_number, "action_type": "model_error", "observation": status.message})
            break
        prompt_tokens, completion_tokens = _usage_tokens(usage)
        input_tokens += prompt_tokens
        output_tokens += completion_tokens
        if len(execution_inputs) != 1:
            raise ValueError("official ReAct must emit exactly one execution input")
        content = execution_inputs[0].content
        if content.startswith(LOAD_SENTINEL):
            skill_id = content.removeprefix(LOAD_SENTINEL)
            observation = loader.load(skill_id, agent.step_number)
            outputs = [ExecutionIO(content=observation, metadata={"action_type": "load_skill", "skill_id": skill_id})]
            action_type = "load_skill"
        else:
            raw_outputs = world.batch_execute([content])
            observation = raw_outputs[0]
            outputs = [ExecutionIO(content=observation, metadata=execution_inputs[0].metadata)]
            execution_steps += 1
            action_type = "execute"
        agent.usage_tracker.add(world.task_id, usage)
        agent.log_usage()
        steps.append({"step": agent.step_number, "action_type": action_type, "code": content, "observation": observation})
        if world.task_completed() or agent.usage_tracker.exceeded(world.task_id):
            break
    agent.logger.complete_task()
    return {
        "messages": agent.messages,
        "steps": steps,
        "used_skill_ids": sorted(agent.used_skill_ids),
        "skill_load_events": loader.event_dicts(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "execution_steps": execution_steps,
        "claimed_complete": bool(world.task_completed()),
        "max_steps_reached": len(steps) >= max_steps and not world.task_completed(),
        "official_agent_class": "SimplifiedReActCodeAgent",
    }


def local_model_config(base_url: str, model_id: str) -> dict[str, Any]:
    if not base_url.startswith(("http://127.0.0.1", "http://localhost")):
        raise ValueError("formal Agent model must use a loopback endpoint")
    # appworld-agents resolves model URLs through this environment variable,
    # even when the supplied base_url contains no template placeholders.
    os.environ["MODEL_SERVER_URL"] = base_url
    os.environ.setdefault("OPENAI_API_KEY", "local")
    return {
        "name": model_id,
        "cost_per_token": {
            "input_cache_miss": 0.0,
            "input_cache_hit": 0.0,
            "input_cache_write": 0.0,
            "output": 0.0,
        },
        "client_name": "openai",
        "base_url": base_url,
        "api_key": "local",
        "temperature": 0.7,
        "top_p": 0.8,
        "max_tokens": 4096,
        "use_cache": False,
        "max_retries": 3,
    }


def _usage_tokens(usage: Any) -> tuple[int, int]:
    tokens = getattr(usage, "tokens", None)
    if tokens is not None:
        prompt = int(getattr(tokens, "input_cache_miss", 0) or 0)
        prompt += int(getattr(tokens, "input_cache_hit", 0) or 0)
        completion = int(getattr(tokens, "output", 0) or 0)
        return prompt, completion
    value = asdict(usage) if is_dataclass(usage) else getattr(usage, "__dict__", {})
    prompt = value.get("prompt_tokens", value.get("input_tokens", 0))
    completion = value.get("completion_tokens", value.get("output_tokens", 0))
    return int(prompt or 0), int(completion or 0)
