"""
Video Pipeline Team — Native Claude Code Team Implementation
===========================================================
Uses Claude Code's native TeamCreate/Agent(team_name=...) system.

Usage from Claude Code:
    /team bootlogix-video
    Then spawn agents via Agent tool with team_name="bootlogix-video"
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Import the dynamic prompt loader
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.prompt_loader import (
    get_researcher_prompt,
    get_scriptwriter_prompt,
    get_visual_designer_prompt,
    get_producer_prompt,
    get_critique_prompt,
    list_roles,
)

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
PROJECTS_DIR = WORKSPACE_ROOT / "projects"
MANIFESTS_DIR = PROJECTS_DIR / "manifests"


def bootstrap_team() -> dict[str, Any]:
    """
    Returns the team configuration for the video-pipeline team.
    To be used when initializing via TeamCreate.
    """
    return {
        "team_name": "video-pipeline",
        "description": "SSD Pipeline for viral Shorts: Search -> Script -> Design -> Generate",
        "members": [
            {
                "name": "researcher",
                "agent_type": "general-purpose",
                "role": "SEARCH",
                "skills": ["find-skills", "mcp__youtube-shorts-transcript-extractor"],
            },
            {
                "name": "scriptwriter",
                "agent_type": "general-purpose",
                "role": "SCRIPT",
                "skills": ["copywriting", "elevenlabs-tts"],
            },
            {
                "name": "visual-designer",
                "agent_type": "general-purpose",
                "role": "DESIGN",
                "skills": ["ai-video-generation"],
            },
            {
                "name": "producer",
                "agent_type": "general-purpose",
                "role": "GENERATE",
                "skills": ["remotion", "remotion-best-practices", "elevenlabs-tts", "ai-video-generation"],
            },
            {
                "name": "critique",
                "agent_type": "general-purpose",
                "role": "CRITIQUE",
                "skills": [],
            },
        ],
    }


def get_team_member_prompt(member_name: str, project_context: dict[str, Any] | None = None) -> str:
    """
    Return the full prompt for a team member by loading it dynamically.
    This replaces static string prompts with runtime-loaded ones.
    """
    role_to_loader = {
        "researcher": get_researcher_prompt,
        "scriptwriter": get_scriptwriter_prompt,
        "visual-designer": get_visual_designer_prompt,
        "producer": get_producer_prompt,
        "critique": get_critique_prompt,
    }

    loader = role_to_loader.get(member_name)
    if loader is None:
        raise ValueError(f"Unknown member: {member_name}")

    agent = loader()
    prompt = agent["prompt"]

    if project_context:
        context_block = _build_context_block(project_context)
        prompt = f"{context_block}\n\n{prompt}"

    return prompt


def _build_context_block(context: dict[str, Any]) -> str:
    parts = []
    if "project_id" in context:
        parts.append(f"- **Project ID**: {context['project_id']}")
    if "topic" in context:
        parts.append(f"- **Topic**: {context['topic']}")
    if "quality_target" in context:
        parts.append(f"- **Quality Target**: {context['quality_target']}")
    if "constraints" in context:
        parts.append(f"- **Constraints**: {context['constraints']}")

    if not parts:
        return ""
    return "## Project Context\n" + "\n".join(parts)


def init_project_manifest(project_id: str, quality_target: str = "standard") -> dict[str, Any]:
    """
    Initialize a new project manifest for the SSD pipeline.
    Returns the manifest data structure.
    """
    from mcp_bridge.state_manager import ManifestManager

    manager = ManifestManager(storage_path=str(MANIFESTS_DIR))
    manifest = manager.create_manifest(
        project_id=project_id,
        metadata={"team": "video-pipeline", "quality_target": quality_target},
        quality_target=quality_target,
    )
    return {
        "project_id": manifest.project_id,
        "status": manifest.status,
        "current_phase": manifest.current_phase,
        "quality_target": manifest.quality_target,
        "manifest_path": str(MANIFESTS_DIR / f"{project_id}.json"),
    }


def read_manifest(project_id: str) -> dict[str, Any]:
    """Read a project manifest and return it as a dict."""
    from mcp_bridge.state_manager import ManifestManager

    manager = ManifestManager(storage_path=str(MANIFESTS_DIR))
    manifest = manager.load_manifest(project_id)
    if manifest is None:
        raise ValueError(f"Manifest not found for project: {project_id}")

    from dataclasses import asdict
    return asdict(manifest)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video Pipeline Team CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("bootstrap", help="Print team bootstrap config as JSON")
    sub.add_parser("members", help="List all team members and their roles")
    sub.add_parser("init", help="Initialize a new project manifest")
    sub.add_parser("manifest", help="Read a project manifest")

    args = parser.parse_args()

    if args.cmd == "bootstrap":
        print(json.dumps(bootstrap_team(), indent=2))
    elif args.cmd == "members":
        for role in list_roles():
            agent = {
                "researcher": get_researcher_prompt,
                "scriptwriter": get_scriptwriter_prompt,
                "visual-designer": get_visual_designer_prompt,
                "producer": get_producer_prompt,
                "critique": get_critique_prompt,
            }.get(role, lambda: {"name": "", "prompt": ""})()
            print(f"  {agent['name']} ({role})")
    elif args.cmd == "init":
        import uuid
        pid = f"proj_{uuid.uuid4().hex[:8]}"
        result = init_project_manifest(pid)
        print(json.dumps(result, indent=2))
    elif args.cmd == "manifest":
        import uuid
        # List available manifests
        manifests = list(MANIFESTS_DIR.glob("*.json"))
        if not manifests:
            print("No manifests found.")
        else:
            for m in manifests:
                print(f"  {m.stem}")
    else:
        parser.print_help()
