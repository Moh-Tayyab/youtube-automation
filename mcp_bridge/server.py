#!/usr/bin/env python3
"""
VideoBridge MCP Server
========================
Unified Model Context Protocol server exposing all production bridges as tools.

Architecture:
  Claude Code (stdio) → VideoBridge MCP → bridges: youtube, captions, render, topaz, quality
                                        → yt-dlp (search)
                                        → YouTube Data API v3 (uploads)

All bridges live in production/bridges/ and production/validation/.
This server is the transport layer that makes them accessible to Claude Code.
"""

from __future__ import annotations

import os
import sys
import json
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Any, Optional

# ─── MCP SDK ──────────────────────────────────────────────────────────────────
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

# ─── Bridges ──────────────────────────────────────────────────────────────────
# Lazy-import so startup is fast and errors are per-tool, not at boot.
sys.path.insert(0, str(Path(__file__).parent.parent))

from production.bridges.youtube import YouTubeBridge
from production.bridges.captions import CaptionBridge
from production.bridges.render import RenderBridge
from production.bridges.topaz import TopazBridge
from production.validation.quality import ValidationEngine
from mcp_bridge.manifest_tool import ManifestTool
from production.bridges.social import SocialBridge

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("video-bridge")

# ─── Constants ──────────────────────────────────────────────────────────────────
WORKSPACE = os.environ.get("BOOTLOGIX_WORKSPACE", "/tmp/bootlogix_output")
BRIDGE_FOLDER = os.path.join(WORKSPACE, "bridges")
CREDENTIALS_DIR = os.path.join(Path(__file__).parent.parent, "production", "secrets")

os.makedirs(WORKSPACE, exist_ok=True)
os.makedirs(BRIDGE_FOLDER, exist_ok=True)

# ─── Manifest Storage ──────────────────────────────────────────────────────────
MANIFEST_DIR = os.path.join(
    Path(__file__).parent.parent,
    "projects/manifests"
)
os.makedirs(MANIFEST_DIR, exist_ok=True)

# ─── Server instance ──────────────────────────────────────────────────────────
app = Server("video-bridge")


# ─── Tool definitions ──────────────────────────────────────────────────────────
TOOLS: list[Tool] = [
    # ── Project Management (SSD Pipeline) ────────────────────────────────────
    Tool(
        name="project_init",
        description="Initialize a new SSD project manifest (Search -> Script -> Design -> Generate).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id":     {"type": "string", "description": "Unique project identifier"},
                "metadata":       {"type": "object", "description": "Initial project metadata (target_platform, tone, etc.)"},
                "quality_target": {"type": "string", "default": "standard", "enum": ["standard", "cinematic"], "description": "standard (Remotion), cinematic (After Effects)"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="project_get_state",
        description="Retrieve the current state, phase, and artifacts of a project.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="project_record_artifact",
        description="Record a production artifact (file path or data) for a specific phase.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "phase":        {"type": "string", "enum": ["SEARCH", "SCRIPT", "DESIGN", "GENERATE"]},
                "artifact_key": {"type": "string", "description": "e.g., transcript, script_md, voiceover_path"},
                "content":      {"type": "any",    "description": "The file path or structured data to record"},
            },
            "required": ["project_id", "phase", "artifact_key", "content"],
        },
    ),
    Tool(
        name="project_transition_phase",
        description="Transition a project to the next phase if dependencies are met.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "target_phase": {"type": "string", "enum": ["SEARCH", "SCRIPT", "DESIGN", "GENERATE"]},
                "agent_id":     {"type": "string", "default": "SSD_Orchestrator"},
            },
            "required": ["project_id", "target_phase"],
        },
    ),
    Tool(
        name="project_complete_phase",
        description="Mark the current phase of a project as COMPLETED.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="project_reset_artifact",
        description="Reset a specific artifact for re-generation (used in QA loops).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id":   {"type": "string"},
                "phase":        {"type": "string"},
                "artifact_key": {"type": "string"},
                "feedback":     {"type": "string", "description": "Reason for reset/QA feedback"},
            },
            "required": ["project_id", "phase", "artifact_key"],
        },
    ),
    Tool(
        name="social_upload",
        description="Upload a video to TikTok or Instagram Reels via browser automation.",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "caption":    {"type": "string"},
                "platform":   {"type": "string", "enum": ["tiktok", "instagram"]},
            },
            "required": ["video_path", "caption", "platform"],
        },
    ),

    # ── YouTube ──────────────────────────────────────────────────────────────
    Tool(
        name="youtube_upload",
        description=(
            "Upload a video to YouTube with full SEO metadata, thumbnail, and tags. "
            "Requires client_secrets.json for OAuth authentication. "
            "Call youtube_authenticate first if not yet authenticated."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path":     {"type": "string",  "description": "Path to video file"},
                "title":          {"type": "string",  "description": "Video title (max 100 chars for SEO)"},
                "description":    {"type": "string",  "description": "Video description with timestamps and links"},
                "tags":           {"type": "array",   "items": {"type": "string"}, "description": "SEO tags"},
                "category_id":    {"type": "string",  "default": "22", "description": "YouTube category ID (22=People)"},
                "privacy":        {"type": "string",  "default": "public", "enum": ["public", "unlisted", "private"]},
                "thumbnail_path": {"type": "string",  "description": "Optional thumbnail image path"},
            },
            "required": ["video_path", "title", "description"],
        },
    ),
    Tool(
        name="youtube_authenticate",
        description="Run YouTube OAuth flow to authenticate. Writes tokens to production/secrets/",
        inputSchema={
            "type": "object",
            "properties": {
                "client_secrets_path": {
                    "type": "string",
                    "description": "Path to client_secrets.json (default: production/secrets/client_secrets.json)",
                },
            },
        },
    ),
    Tool(
        name="youtube_get_channel",
        description="Get authenticated channel info (name, subscriber count, video count).",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="youtube_search",
        description=(
            "Search YouTube for videos matching a query. Returns video IDs, titles, "
            "and metadata. Uses yt-dlp for fast metadata extraction."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Search query"},
                "limit":      {"type": "integer", "default": 5, "description": "Max results"},
                "duration":   {"type": "string",  "description": "Filter: <3m, 3m-10m, >10m"},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="youtube_download",
        description=(
            "Download a YouTube video (or shorts) using yt-dlp. "
            "Stores in WORKSPACE/<project_id>/. "
            "Returns the local file path."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url":        {"type": "string", "description": "YouTube URL"},
                "project_id": {"type": "string", "description": "Project folder name"},
                "format":     {"type": "string", "default": "mp4", "description": "Output format"},
            },
            "required": ["url", "project_id"],
        },
    ),
    Tool(
        name="youtube_get_transcript",
        description=(
            "Extract transcript/captions from a YouTube video or Short using Playwright. "
            "Returns timed word-level captions suitable for karaoke generation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "YouTube video or Shorts URL"},
            },
            "required": ["url"],
        },
    ),

    # ── Captions ──────────────────────────────────────────────────────────────
    Tool(
        name="caption_transcribe",
        description=(
            "Generate SRT captions from an audio file using ElevenLabs Scribe. "
            "Outputs word-level timestamps for karaoke animation. "
            "Falls back to placeholder captions if STT is unavailable."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "audio_path":  {"type": "string", "description": "Path to audio file (.wav, .mp3)"},
                "project_id": {"type": "string", "description": "Project folder name"},
            },
            "required": ["audio_path", "project_id"],
        },
    ),
    Tool(
        name="caption_generate_ass",
        description=(
            "Convert SRT to ASS karaoke captions with Maven-Edit styling. "
            "Words matching highlight_words use yellow highlight style. "
            "Output: WORKSPACE/<project_id>/maven_captions.ass"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "srt_path":        {"type": "string", "description": "Path to SRT file"},
                "project_id":     {"type": "string", "description": "Project folder name"},
                "highlight_words": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Words to highlight in yellow (default: WAIT, NO, MIND, THIS, BEST, PERFECT, SUBSCRIBE)",
                },
            },
            "required": ["srt_path", "project_id"],
        },
    ),

    # ── Render ────────────────────────────────────────────────────────────────
    Tool(
        name="render_burn_captions",
        description=(
            "Burn ASS subtitles into a video using libass + ffmpeg. "
            "Output: WORKSPACE/<project_id>/final_video.mp4"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path":  {"type": "string", "description": "Path to source video"},
                "ass_path":   {"type": "string", "description": "Path to ASS subtitle file"},
                "project_id": {"type": "string", "description": "Project folder name"},
                "output_name": {"type": "string", "default": "final_video.mp4"},
                "quality":    {"type": "string", "default": "high", "enum": ["high", "medium", "fast"]},
            },
            "required": ["video_path", "ass_path", "project_id"],
        },
    ),
    Tool(
        name="render_burn_captions_async",
        description="Starts burning captions in the background. Returns project info and pid file.",
        inputSchema={
            "type": "object",
            "properties": {
                "video_path":  {"type": "string"},
                "ass_path":   {"type": "string"},
                "project_id": {"type": "string"},
                "output_name": {"type": "string", "default": "final_video.mp4"},
            },
            "required": ["video_path", "ass_path", "project_id"],
        },
    ),
    Tool(
        name="render_poll_status",
        description="Check if a background render is still running.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "output_name": {"type": "string", "default": "final_video.mp4"},
            },
            "required": ["project_id"],
        },
    ),
    Tool(
        name="render_encode_frames",
        description=(
            "Encode a directory of frames into a video. "
            "Assumes frame_NNNN.png naming. "
            "Output: WORKSPACE/<project_id>/<output_name>"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "frames_dir":  {"type": "string", "description": "Directory containing PNG frames"},
                "project_id": {"type": "string", "description": "Project folder name"},
                "output_name": {"type": "string", "default": "final_video.mp4"},
                "fps":        {"type": "integer", "default": 30},
                "width":      {"type": "integer", "default": 1080},
                "height":     {"type": "integer", "default": 1920},
            },
            "required": ["frames_dir", "project_id"],
        },
    ),
    Tool(
        name="render_linear_wipe",
        description=(
            "Add a linear wipe transition between two clips using ffmpeg xfade. "
            "Output: WORKSPACE/<project_id>/transitioned.mp4"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video1_path":        {"type": "string"},
                "video2_path":        {"type": "string"},
                "project_id":         {"type": "string"},
                "transition_duration": {"type": "number", "default": 1.0},
                "direction":         {"type": "string", "default": "left", "enum": ["left", "right", "top", "bottom"]},
            },
            "required": ["video1_path", "video2_path", "project_id"],
        },
    ),
    Tool(
        name="render_convert_format",
        description="Convert a video to a different format using ffmpeg.",
        inputSchema={
            "type": "object",
            "properties": {
                "input_path":  {"type": "string"},
                "project_id": {"type": "string"},
                "output_ext": {"type": "string", "description": "Target extension (mp4, webm, mov, mkv)"},
                "codec":      {"type": "string", "default": "libx264"},
                "bitrate":    {"type": "string", "description": "Optional video bitrate (e.g. 5M)"},
            },
            "required": ["input_path", "project_id", "output_ext"],
        },
    ),

    # ── Topaz Enhancement ─────────────────────────────────────────────────────
    Tool(
        name="topaz_upscale",
        description=(
            "Upscale video using Topaz Video AI via inference.sh. "
            "Proteus model: 2x (1080→2160) or 4x (1080→4K). "
            "Timeout: 10 minutes. "
            "Output: WORKSPACE/<project_id>/upscaled.mp4"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path":  {"type": "string"},
                "project_id": {"type": "string"},
                "scale":      {"type": "integer", "default": 2, "description": "Scale factor: 2 (2x) or 4 (4x)"},
                "model":      {"type": "string", "default": "Proteus", "description": "Model: Proteus, Artemis, Iris"},
                "output_name": {"type": "string", "default": "upscaled.mp4"},
            },
            "required": ["video_path", "project_id"],
        },
    ),
    Tool(
        name="topaz_denoise",
        description=(
            "Denoise and enhance video using Topaz via inference.sh. "
            "Iris model: remove noise while preserving detail. "
            "Output: WORKSPACE/<project_id>/denoised.mp4"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path":  {"type": "string"},
                "project_id": {"type": "string"},
                "model":      {"type": "string", "default": "Iris"},
                "output_name": {"type": "string", "default": "denoised.mp4"},
            },
            "required": ["video_path", "project_id"],
        },
    ),

    # ── Quality Validation ────────────────────────────────────────────────────
    Tool(
        name="quality_validate",
        description=(
            "Run quality gate checks on a media artifact. "
            "check_type: duration | resolution | file_exists | audio_level"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "artifact_path": {"type": "string"},
                "check_type":   {"type": "string", "enum": ["duration", "resolution", "file_exists", "audio_level"]},
            },
            "required": ["artifact_path", "check_type"],
        },
    ),
    Tool(
        name="quality_report",
        description=(
            "Generate a full quality report for a video: duration, resolution, "
            "codec, file size, and audio channels. Returns a structured dict."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
            },
            "required": ["video_path"],
        },
    ),
]


# ─── Bridge helpers (lazy init) ───────────────────────────────────────────────

def _youtube_bridge() -> YouTubeBridge:
    secrets = os.path.join(CREDENTIALS_DIR, "client_secrets.json")
    return YouTubeBridge(secrets)


def _caption_bridge() -> CaptionBridge:
    return CaptionBridge(WORKSPACE)


def _render_bridge() -> RenderBridge:
    return RenderBridge(WORKSPACE)


def _topaz_bridge() -> TopazBridge:
    return TopazBridge(WORKSPACE)


def _validation_engine() -> ValidationEngine:
    return ValidationEngine()


def _manifest_tool() -> ManifestTool:
    return ManifestTool(storage_path=MANIFEST_DIR)


def _social_bridge() -> SocialBridge:
    return SocialBridge()


# ─── Tool handlers ─────────────────────────────────────────────────────────────

async def handle_social_upload(args: dict) -> CallToolResult:
    try:
        bridge = _social_bridge()
        platform = args["platform"]
        if platform == "tiktok":
            result = bridge.upload_to_tiktok(args["video_path"], args["caption"])
        else:
            result = bridge.upload_to_reels(args["video_path"], args["caption"])

        return CallToolResult(content=[TextContent(type="text", text=json.dumps({
            "success": result.success,
            "platform": result.platform,
            "url": result.url,
            "error": result.error
        }, indent=2))])
    except Exception as e:
        logger.exception("social_upload failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_init(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.init_project(
            args["project_id"],
            args.get("metadata", {}),
            args.get("quality_target", "standard")
        )
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_init failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_get_state(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.get_current_state(args["project_id"])
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_get_state failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_record_artifact(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.record_artifact(
            args["project_id"],
            args["phase"],
            args["artifact_key"],
            args["content"]
        )
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_record_artifact failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_transition_phase(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.transition_to_phase(
            args["project_id"],
            args["target_phase"],
            args.get("agent_id", "SSD_Orchestrator")
        )
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_transition_phase failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_complete_phase(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.complete_current_phase(args["project_id"])
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_complete_phase failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_project_reset_artifact(args: dict) -> CallToolResult:
    try:
        tool = _manifest_tool()
        result = tool.reset_artifact_status(
            args["project_id"],
            args["phase"],
            args["artifact_key"],
            args.get("feedback", "")
        )
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    except Exception as e:
        logger.exception("project_reset_artifact failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_upload(args: dict) -> CallToolResult:
    try:
        bridge = _youtube_bridge()
        if not bridge.youtube:
            bridge.authenticate()

        result = bridge.upload(
            video_path=args["video_path"],
            title=args["title"],
            description=args["description"],
            tags=args.get("tags", []),
            category_id=args.get("category_id", "22"),
            privacy_status=args.get("privacy", "public"),
            thumbnail_path=args.get("thumbnail_path"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    except Exception as e:
        logger.exception("youtube_upload failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_authenticate(args: dict) -> CallToolResult:
    try:
        bridge = _youtube_bridge()
        secrets = args.get("client_secrets_path") or os.path.join(CREDENTIALS_DIR, "client_secrets.json")
        bridge.client_secrets = secrets
        bridge.authenticate()
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"authenticated": True}))]
        )
    except Exception as e:
        logger.exception("youtube_authenticate failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_get_channel(_: dict) -> CallToolResult:
    try:
        bridge = _youtube_bridge()
        info = bridge.get_channel_info()
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(info, indent=2))]
        )
    except Exception as e:
        logger.exception("youtube_get_channel failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_search(args: dict) -> CallToolResult:
    """Search using yt-dlp --dump-json."""
    try:
        query = args["query"]
        limit = args.get("limit", 5)
        duration = args.get("duration", "")

        filter_param = ""
        if duration == "<3m":
            filter_param = "--match-filter=duration<180"
        elif duration == "3m-10m":
            filter_param = "--match-filter=duration>=180,duration<=600"
        elif duration == ">10m":
            filter_param = "--match-filter=duration>600"

        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--flat-playlist",
            f"--max-results={limit}",
            *filter_param.split(),
            f"ytsearch{limit}:{query}",
        ]
        cmd = [c for c in cmd if c]  # remove empty strings

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return CallToolResult(
                content=[TextContent(type="text", text=f"yt-dlp error: {result.stderr}")],
                isError=True,
            )

        videos = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    item = json.loads(line)
                    videos.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "url": item.get("webpage_url", item.get("url", "")),
                        "duration": item.get("duration", 0),
                        "uploader": item.get("uploader", ""),
                    })
                except json.JSONDecodeError:
                    continue

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(videos, indent=2))]
        )
    except subprocess.TimeoutExpired:
        return CallToolResult(content=[TextContent(type="text", text="Search timed out")], isError=True)
    except Exception as e:
        logger.exception("youtube_search failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_download(args: dict) -> CallToolResult:
    try:
        url = args["url"]
        project_id = args["project_id"]
        fmt = args.get("format", "mp4")

        project_dir = os.path.join(WORKSPACE, project_id)
        os.makedirs(project_dir, exist_ok=True)

        cmd = [
            "yt-dlp",
            "-f", f"bestvideo[ext={fmt}]+bestaudio[ext=m4a]/best[ext={fmt}]",
            "-o", f"{project_dir}/%(title)s.%(ext)s",
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Download failed: {result.stderr}")],
                isError=True,
            )

        # Find downloaded file
        import glob
        files = glob.glob(f"{project_dir}/*.mp4") + glob.glob(f"{project_dir}/*.mkv")
        downloaded = files[0] if files else ""

        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"success": True, "path": downloaded, "stderr": result.stderr[-500:]}))]
        )
    except Exception as e:
        logger.exception("youtube_download failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_youtube_get_transcript(args: dict) -> CallToolResult:
    """Delegate to the Playwright MCP server via subprocess for transcript extraction."""
    try:
        url = args["url"]
        # The Playwright MCP server exposes the tool via its own protocol.
        # We invoke it the same way Claude Code would — via a JS subprocess call.
        # Since we don't have direct MCP-to-MCP calls, we use the skill's CLI wrapper.
        cmd = [
            "node",
            str(Path(__file__).parent.parent / ".claude/skills/playwright-youtube-shorts/cli.js"),
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout:
            return CallToolResult(
                content=[TextContent(type="text", text=result.stdout)]
            )
        return CallToolResult(
            content=[TextContent(type="text", text=f"Transcript extraction failed: {result.stderr}")],
            isError=True,
        )
    except Exception as e:
        logger.exception("youtube_get_transcript failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_caption_transcribe(args: dict) -> CallToolResult:
    try:
        bridge = _caption_bridge()
        result = bridge.transcribe_audio(args["audio_path"], args["project_id"])
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "srt_path": result.srt_path,
                "word_count": len(result.word_timestamps),
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("caption_transcribe failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_caption_generate_ass(args: dict) -> CallToolResult:
    try:
        bridge = _caption_bridge()
        result = bridge.srt_to_ass(
            args["srt_path"],
            args["project_id"],
            args.get("highlight_words"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "ass_path": result.ass_path,
                "caption_count": result.caption_count,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("caption_generate_ass failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_burn_captions(args: dict) -> CallToolResult:
    try:
        bridge = _render_bridge()
        result = bridge.burn_captions(
            args["video_path"],
            args["ass_path"],
            args["project_id"],
            args.get("output_name", "final_video.mp4"),
            args.get("quality", "high"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "file_size_mb": result.file_size_mb,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("render_burn_captions failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_burn_captions_async(args: dict) -> CallToolResult:
    try:
        bridge = _render_bridge()
        pid_file = bridge.start_background_burn(
            args["video_path"],
            args["ass_path"],
            args["project_id"],
            args.get("output_name", "final_video.mp4")
        )
        return CallToolResult(content=[TextContent(type="text", text=json.dumps({
            "status": "started",
            "pid_file": pid_file,
            "message": "Render started in background."
        }, indent=2))])
    except Exception as e:
        logger.exception("render_burn_captions_async failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_poll_status(args: dict) -> CallToolResult:
    try:
        project_id = args["project_id"]
        output_name = args.get("output_name", "final_video.mp4")
        pid_file = os.path.join(WORKSPACE, project_id, f"{output_name}.pid")
        
        if not os.path.exists(pid_file):
            return CallToolResult(content=[TextContent(type="text", text=json.dumps({"status": "not_found"}))])
        
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        
        # Check if process is still alive
        is_running = os.path.exists(f"/proc/{pid}")
        
        return CallToolResult(content=[TextContent(type="text", text=json.dumps({
            "status": "running" if is_running else "finished",
            "pid": pid
        }, indent=2))])
    except Exception as e:
        logger.exception("render_poll_status failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_encode_frames(args: dict) -> CallToolResult:
    try:
        bridge = _render_bridge()
        result = bridge.encode_from_frames(
            args["frames_dir"],
            args["project_id"],
            args.get("output_name", "final_video.mp4"),
            args.get("fps", 30),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "file_size_mb": result.file_size_mb,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("render_encode_frames failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_linear_wipe(args: dict) -> CallToolResult:
    try:
        bridge = _render_bridge()
        result = bridge.add_linear_wipe_transition(
            args["video1_path"],
            args["video2_path"],
            args["project_id"],
            args.get("transition_duration", 1.0),
            args.get("direction", "left"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "file_size_mb": result.file_size_mb,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("render_linear_wipe failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_render_convert_format(args: dict) -> CallToolResult:
    try:
        bridge = _render_bridge()
        result = bridge.convert_format(
            args["input_path"],
            args["project_id"],
            args["output_ext"],
            args.get("codec", "libx264"),
            args.get("bitrate"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "file_size_mb": result.file_size_mb,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("render_convert_format failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_topaz_upscale(args: dict) -> CallToolResult:
    try:
        bridge = _topaz_bridge()
        result = bridge.upscale(
            args["video_path"],
            args["project_id"],
            args.get("scale", 2),
            args.get("model", "Proteus"),
            args.get("output_name", "upscaled.mp4"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "resolution": result.resolution,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("topaz_upscale failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_topaz_denoise(args: dict) -> CallToolResult:
    try:
        bridge = _topaz_bridge()
        result = bridge.enhance_denoise(
            args["video_path"],
            args["project_id"],
            args.get("model", "Iris"),
            args.get("output_name", "denoised.mp4"),
        )
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "success": result.success,
                "output_path": result.output_path,
                "resolution": result.resolution,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("topaz_denoise failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_quality_validate(args: dict) -> CallToolResult:
    try:
        engine = _validation_engine()
        result = engine.verify_artifact(args["artifact_path"], args["check_type"])
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "passed": result.passed,
                "message": result.message,
            }, indent=2))]
        )
    except Exception as e:
        logger.exception("quality_validate failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


async def handle_quality_report(args: dict) -> CallToolResult:
    try:
        import subprocess
        video = args["video_path"]
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return CallToolResult(
            content=[TextContent(type="text", text=result.stdout or f"ffprobe error: {result.stderr}")]
        )
    except Exception as e:
        logger.exception("quality_report failed")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {e}")], isError=True)


# ─── Route dispatcher ─────────────────────────────────────────────────────────
TOOL_HANDLERS = {
    "project_init":             handle_project_init,
    "project_get_state":         handle_project_get_state,
    "project_record_artifact":   handle_project_record_artifact,
    "project_transition_phase": handle_project_transition_phase,
    "project_complete_phase":   handle_project_complete_phase,
    "project_reset_artifact":    handle_project_reset_artifact,
    "social_upload":           handle_social_upload,
    "youtube_upload":          handle_youtube_upload,
    "youtube_authenticate":    handle_youtube_authenticate,
    "youtube_get_channel":      handle_youtube_get_channel,
    "youtube_search":          handle_youtube_search,
    "youtube_download":        handle_youtube_download,
    "youtube_get_transcript":   handle_youtube_get_transcript,
    "caption_transcribe":      handle_caption_transcribe,
    "caption_generate_ass":    handle_caption_generate_ass,
    "render_burn_captions":    handle_render_burn_captions,
    "render_burn_captions_async": handle_render_burn_captions_async,
    "render_poll_status":      handle_render_poll_status,
    "render_encode_frames":    handle_render_encode_frames,
    "render_linear_wipe":       handle_render_linear_wipe,
    "render_convert_format":   handle_render_convert_format,
    "topaz_upscale":           handle_topaz_upscale,
    "topaz_denoise":           handle_topaz_denoise,
    "quality_validate":        handle_quality_validate,
    "quality_report":          handle_quality_report,
}


# ─── MCP protocol handlers ────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return all available tools when Claude Code queries the server."""
    return TOOLS


@app.call_tool()
async def call_tool(request: CallToolRequest) -> CallToolResult:
    """
    Main entry point — Claude Code calls a tool by name.
    Dispatch to the appropriate handler.
    """
    tool_name = request.name
    args = dict(request.arguments) if request.arguments else {}

    logger.info(f"Tool call: {tool_name} | args: {list(args.keys())}")

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {tool_name}")],
            isError=True,
        )

    return await handler(args)


# ─── Entry point ───────────────────────────────────────────────────────────────

async def main():
    """Start the stdio MCP server. Blocks forever."""
    parser = argparse.ArgumentParser(description="VideoBridge MCP Server")
    parser.add_argument("--workspace", default=WORKSPACE, help="Output workspace directory")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level))
    logger.info(f"VideoBridge MCP starting — workspace: {args.workspace}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
