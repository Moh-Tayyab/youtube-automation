"""
Agents package — re-exports SkillResult from the canonical location.
The canonical SkillResult lives in mcp_bridge.agents (complete definition).
All agent code imports from there.
"""
from mcp_bridge.agents import SkillResult

__all__ = ["SkillResult"]
