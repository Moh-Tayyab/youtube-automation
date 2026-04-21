"""
Dynamic Agent Prompt Loader
===========================
Loads *_PROMPT and *_AGENT_NAME constants from agents/prompts/*.py at runtime.
Ensures prompts are always in sync with source files — no hardcoded strings.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import TypedDict

AGENTS_PROMPTS_DIR = Path(__file__).parent / "prompts"


class AgentPrompt(TypedDict):
    name: str
    prompt: str


_PROMPT_CACHE: dict[str, AgentPrompt] | None = None


def _load_prompt_module(file_path: Path):
    """Load a Python module from a file path without side effects."""
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[file_path.stem] = module
    spec.loader.exec_module(module)
    return module


def _derive_role_key(name: str) -> str:
    """Derive a consistent role key from an agent name like 'researcher' or 'maven-producer'."""
    return name.replace("-", "_")


def load_all_prompts() -> dict[str, AgentPrompt]:
    """
    Load all agent prompts from agents/prompts/*.py.
    Returns a dict mapping agent role -> {name, prompt}.
    Caches after first load.

    Convention: each *.py file must export exactly one *_PROMPT and one *_AGENT_NAME.
    Variable names are matched by suffix pattern: *_PROMPT and *_AGENT_NAME.
    """
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE

    prompts: dict[str, AgentPrompt] = {}

    for file_path in sorted(AGENTS_PROMPTS_DIR.glob("*_agent.py")):
        module = _load_prompt_module(file_path)
        module_attrs = dir(module)

        # Find *_PROMPT and *_AGENT_NAME by suffix match
        prompt_value: str | None = None
        name_value: str | None = None

        for attr in module_attrs:
            if attr.endswith("_PROMPT"):
                prompt_value = getattr(module, attr)
            elif attr.endswith("_AGENT_NAME"):
                name_value = getattr(module, attr)

        if prompt_value is not None and name_value is not None:
            role_key = _derive_role_key(name_value)
            prompts[role_key] = AgentPrompt(name=name_value, prompt=prompt_value.strip())

    _PROMPT_CACHE = prompts
    return prompts


def get_prompt(role: str) -> AgentPrompt:
    """
    Get a single prompt by role key.
    Role key is the agent name with dashes replaced by underscores.
    E.g., 'researcher', 'scriptwriter', 'visual_designer', 'producer', 'critique'.
    """
    prompts = load_all_prompts()
    if role not in prompts:
        available = ", ".join(sorted(prompts.keys()))
        raise ValueError(f"Unknown agent role '{role}'. Available: {available}")
    return prompts[role]


def get_researcher_prompt() -> AgentPrompt:
    return get_prompt("researcher")


def get_scriptwriter_prompt() -> AgentPrompt:
    return get_prompt("scriptwriter")


def get_visual_designer_prompt() -> AgentPrompt:
    return get_prompt("visual_designer")


def get_producer_prompt() -> AgentPrompt:
    return get_prompt("producer")


def get_maven_producer_prompt() -> AgentPrompt:
    return get_prompt("maven_producer")


def get_critique_prompt() -> AgentPrompt:
    return get_prompt("critique")


def list_roles() -> list[str]:
    """List all available agent roles."""
    return sorted(load_all_prompts().keys())
