import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from mcp_bridge.state_manager import ManifestManager, ProjectManifest
from mcp_bridge.manifest_tool import ManifestTool
from production.bridges.payload import BridgeManager, TTSPayload, VideoPrompt
from production.adobe.jsx_gen import AdobeBridge
from production.validation.quality import ValidationEngine

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_FORMAT = "[ORCHESTRATOR] %(asctime)s - %(levelname)s - %(message)s"
# Note: In a production environment, we might want to log to a file,
# but for the MCP server, stderr is often better for debugging.
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("Orchestrator")

class Orchestrator:
    """
    The Brain of the system.
    Responsible for reading the workflow spec, managing the agentic manifest,
    and dispatching work to specialized agents based on SSD phases.
    """
    def __init__(self, workflow_spec_path: Optional[str] = None):
        if not workflow_spec_path:
            workflow_spec_path = str(Path(__file__).parent.parent / "workflow_spec.json")
            
        with open(workflow_spec_path, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)

        self.validation_engine = ValidationEngine()
        self.manifest_manager = ManifestManager()
        self.manifest_tool = ManifestTool()
        self.bridge_manager = BridgeManager()
        self.adobe_bridge = AdobeBridge()

    def create_project(self, project_id: str, metadata: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Initializes a new project and returns the tool result."""
        return self.manifest_tool.init_project(project_id, metadata)

    def get_project_state(self, project_id: str) -> Dict[str, Any]:
        """Provides the current state of the project for the Brain."""
        return self.manifest_tool.get_current_state(project_id)

    def update_project_metadata(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates project metadata (e.g. from /interview)."""
        return self.manifest_tool.update_metadata(project_id, updates)

    def record_project_artifact(self, project_id: str, phase: str, key: str, content: Any) -> Dict[str, Any]:
        """Records an artifact produced by a specialist."""
        return self.manifest_tool.record_artifact(project_id, phase, key, content)

    def transition_project_phase(self, project_id: str, target_phase: str) -> Dict[str, Any]:
        """Transitions the project to the next SSD phase."""
        return self.manifest_tool.transition_to_phase(project_id, target_phase)

    def bridge_and_execute(self, project_id: str, bridge_type: str, input_artifact: str, config: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        The core agentic loop: Read Artifact -> Transform via Bridge -> Execute Skill.
        Supports hot-swap rendering between Remotion and After Effects.
        """
        # 1. Retrieve artifact from manifest
        manifest = self.manifest_manager.load_manifest(project_id)
        if not manifest:
            return {"status": "error", "message": "Project manifest not found."}

        # Determine which renderer to use for GENERATE phase
        quality_target = getattr(manifest, 'quality_target', 'standard')
        
        # Override bridge_type if we are in GENERATE phase and want cinematic
        if bridge_type == "REMOTION" and quality_target == "cinematic":
            logger.info(f"Hot-swapping REMOTION -> AFTER_EFFECTS for project {project_id}")
            bridge_type = "AFTER_EFFECTS"

        # Find the artifact path across all phases
        artifact_path = None
        for phase in manifest.phases.values():
            if input_artifact in phase.artifacts:
                artifact_path = phase.artifacts[input_artifact]
                break

        if not artifact_path:
            return {"status": "error", "message": f"Artifact {input_artifact} not found in manifest."}

        # 2. Transform using the BridgeManager
        try:
            artifact_file = Path(artifact_path)
            if bridge_type == "TTS":
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                payload = self.bridge_manager.prepare_tts_payload(content, config)
            elif bridge_type == "VIDEO":
                with open(artifact_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                payload = self.bridge_manager.prepare_video_prompts(content, config)
            elif bridge_type == "REMOTION":
                payload = self.bridge_manager.generate_remotion_metadata(
                    project_id,
                    config.get('audio_paths', []),
                    config.get('video_paths', []),
                    config.get('fps', 30)
                )
            elif bridge_type == "AFTER_EFFECTS":
                # After Effects bridge uses JSX generation
                payload = {
                    "project_id": project_id,
                    "type": "cinematic_render",
                    "composition": "Shorts_Main",
                    "assets": config.get('assets', [])
                }
            else:
                return {"status": "error", "message": f"Unsupported bridge type: {bridge_type}"}
        except Exception as e:
            logger.exception(f"Bridge transformation failed for {bridge_type}")
            return {"status": "error", "message": f"Bridge transformation failed: {str(e)}"}

        # 3. Execute Skill
        logger.info(f"Executing {bridge_type} skill for {project_id}")
        
        # For long-running tasks, we transition to a intermediate state
        if bridge_type in ["REMOTION", "AFTER_EFFECTS", "VIDEO"]:
             self.manifest_tool.record_artifact(project_id, "GENERATE", f"rendering_started", datetime.utcnow().isoformat())
             # Set status to GENERATING
             manifest.phases["GENERATE"].status = "GENERATING"
             self.manifest_manager.save_manifest(manifest)

        simulated_result_path = f"/tmp/{project_id}_{bridge_type}_output.wav" if bridge_type == "TTS" else f"/tmp/{project_id}_{bridge_type}_output.mp4"

        # Ensure directory exists
        Path(simulated_result_path).parent.mkdir(parents=True, exist_ok=True)
        with open(simulated_result_path, 'w', encoding='utf-8') as f:
            f.write("SIMULATED OUTPUT")

        # 4. Record the new artifact back to the manifest
        phase_map = {"TTS": "GENERATE", "VIDEO": "GENERATE", "REMOTION": "GENERATE", "AFTER_EFFECTS": "GENERATE"}
        target_phase = phase_map.get(bridge_type, "GENERATE")

        self.manifest_tool.record_artifact(project_id, target_phase, f"{bridge_type}_output", simulated_result_path)

        return {
            "status": "success",
            "artifact_path": simulated_result_path,
            "payload": payload,
            "renderer": "After Effects" if bridge_type == "AFTER_EFFECTS" else "Remotion" if bridge_type == "REMOTION" else None
        }

    def execute_adobe_command(self, app: str, jsx_code: str, script_name: str = "cmd.jsx") -> Dict[str, Any]:
        """
        Sends an ExtendScript command to Adobe Premiere or After Effects via the AdobeBridge.
        """
        try:
            file_path = self.adobe_bridge.execute_jsx(app, jsx_code, script_name)
            return {
                "status": "success",
                "script_path": file_path,
                "message": f"Command successfully delivered to {app} drop-zone."
            }
        except Exception as e:
            logger.error(f"Adobe Bridge execution failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
