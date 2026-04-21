import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pathlib import Path
from mcp_bridge.state_manager import ManifestManager, ProjectManifest, PhaseState

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_FORMAT = "[ManifestTool] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("ManifestTool")

# --- Pydantic Models for Type-Safe Hand-offs ---

class ProjectMetadata(BaseModel):
    target_platform: str = "YouTube Shorts"
    aspect_ratio: str = "9:16"
    target_duration: int = 60
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    quality_target: str = "standard"  # standard or cinematic
    goals: List[str] = Field(default_factory=list)

class Artifact(BaseModel):
    key: str
    content: Any
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# --- ManifestTool Implementation ---

class ManifestTool:
    """
    The high-level tool interface for the SSD Orchestrator.
    Wraps ManifestManager to provide atomic, project-centric operations.
    """
    def __init__(self, storage_path: Optional[str] = None):
        self.manager = ManifestManager(storage_path=storage_path)

    def init_project(self, project_id: str, metadata: Dict[str, Any] = {}, quality_target: str = "standard") -> Dict[str, Any]:
        """Initializes a new SSD project manifest."""
        try:
            manifest = self.manager.create_manifest(project_id, metadata, quality_target)
            return {
                "status": "success",
                "project_id": project_id,
                "current_phase": manifest.current_phase,
                "quality_target": manifest.quality_target,
                "phases": list(manifest.phases.keys())
            }
        except Exception as e:
            logger.exception(f"Failed to initialize project: {project_id}")
            return {"status": "error", "message": str(e)}

    def get_current_state(self, project_id: str) -> Dict[str, Any]:
        """Returns the current state of the project manifest."""
        manifest = self.manager.load_manifest(project_id)
        if not manifest:
            return {"status": "error", "message": f"Project {project_id} not found."}

        return {
            "status": "success",
            "project_id": manifest.project_id,
            "current_phase": manifest.current_phase,
            "quality_target": manifest.quality_target,
            "overall_status": manifest.status,
            "phase_details": {
                phase: {
                    "status": state.status,
                    "artifacts": state.artifacts,
                    "agent": state.agent,
                    "started_at": state.started_at,
                    "completed_at": state.completed_at,
                    "feedback": state.feedback
                }
                for phase, state in manifest.phases.items()
            },
            "metadata": manifest.metadata,
            "updated_at": manifest.updated_at
        }

    def update_metadata(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merges new metadata into the project profile."""
        manifest = self.manager.load_manifest(project_id)
        if not manifest:
            return {"status": "error", "message": f"Project {project_id} not found."}

        manifest.metadata.update(updates)
        self.manager.save_manifest(manifest)
        return {"status": "success", "updated_metadata": manifest.metadata}

    def record_artifact(self, project_id: str, phase: str, key: str, content: Any) -> Dict[str, Any]:
        """Stores a produced JSON artifact or file path in the manifest."""
        try:
            self.manager.update_artifact(project_id, phase, key, content)
            return {"status": "success", "artifact": key, "phase": phase}
        except ValueError as e:
            return {"status": "error", "message": str(e)}

    def transition_to_phase(self, project_id: str, target_phase: str, agent_id: str = "SSD_Orchestrator") -> Dict[str, Any]:
        """
        Validates prerequisites and transitions the project to the target phase.
        """
        success = self.manager.transition_phase(project_id, target_phase, agent_id)

        if success:
            return {
                "status": "success",
                "new_phase": target_phase,
                "message": f"Project {project_id} transitioned to {target_phase}."
            }
        else:
            manifest = self.manager.load_manifest(project_id)
            if not manifest:
                 return {"status": "error", "message": f"Project {project_id} not found."}

            phase_state = manifest.phases.get(target_phase)
            if not phase_state:
                 return {"status": "error", "message": f"Phase {target_phase} not found."}

            missing = [dep for dep in phase_state.dependencies if manifest.phases[dep].status != "COMPLETED"]

            return {
                "status": "error",
                "message": f"Cannot transition to {target_phase}. Missing completed dependencies: {missing}"
            }

    def complete_current_phase(self, project_id: str) -> Dict[str, Any]:
        """Marks the current phase as completed."""
        manifest = self.manager.load_manifest(project_id)
        if not manifest:
            return {"status": "error", "message": f"Project {project_id} not found."}

        try:
            self.manager.complete_phase(project_id, manifest.current_phase)
            return {"status": "success", "completed_phase": manifest.current_phase}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_phase_completion(self, project_id: str, phase: str, required_keys: List[str]) -> Dict[str, Any]:
        """Checks if all mandatory artifacts for a phase are present."""
        manifest = self.manager.load_manifest(project_id)
        if not manifest or phase not in manifest.phases:
            return {"status": "error", "message": "Project or phase not found."}

        artifacts = manifest.phases[phase].artifacts
        missing = [key for key in required_keys if key not in artifacts or not artifacts[key]]

        if not missing:
            return {"status": "success", "message": f"Phase {phase} is complete."}
        else:
            return {"status": "incomplete", "missing_artifacts": missing}

    def reset_artifact_status(self, project_id: str, phase: str, artifact_key: str, feedback: str = "") -> Dict[str, Any]:
        """
        Surgically resets a specific artifact for re-generation.
        """
        manifest = self.manager.load_manifest(project_id)
        if not manifest or phase not in manifest.phases:
            return {"status": "error", "message": "Project or phase not found."}

        phase_state = manifest.phases[phase]

        if artifact_key in phase_state.artifacts:
            del phase_state.artifacts[artifact_key]

        phase_state.status = "IN_PROGRESS"
        phase_state.feedback = feedback

        if "retry_counts" not in manifest.metadata:
            manifest.metadata["retry_counts"] = {}

        retry_key = f"{phase}_{artifact_key}"
        current_retries = manifest.metadata["retry_counts"].get(retry_key, 0)
        manifest.metadata["retry_counts"][retry_key] = current_retries + 1

        self.manager.save_manifest(manifest)

        return {
            "status": "success",
            "retries": manifest.metadata["retry_counts"][retry_key],
            "message": f"Artifact {artifact_key} reset for re-generation."
        }