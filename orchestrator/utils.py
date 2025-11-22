"""Utility functions for the orchestration system."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def create_session_directory(base_dir: Path, session_id: str) -> Path:
    """Create a session directory structure."""
    session_dir = base_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (session_dir / "reviews").mkdir(exist_ok=True)
    (session_dir / "logs").mkdir(exist_ok=True)

    logger.info(f"Created session directory: {session_dir}")
    return session_dir


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file and return list of parsed objects."""
    if not file_path.exists():
        return []

    events = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSONL line in {file_path}: {e}")
                continue

    return events


def append_jsonl(file_path: Path, data: Dict[str, Any]) -> None:
    """Append a JSON object to a JSONL file."""
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")
        f.flush()


def save_json(file_path: Path, data: Any, pretty: bool = True) -> None:
    """Save data as JSON file."""
    with open(file_path, "w") as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file."""
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def extract_summary_from_events(events: List[Dict[str, Any]], max_events: int = 10) -> str:
    """Extract a summary from a list of events."""
    if not events:
        return "No activity"

    # Get the last N events
    recent_events = events[-max_events:]

    summaries = []
    for event in recent_events:
        event_type = event.get("type", "unknown")
        payload = event.get("payload", {})
        text = payload.get("text", "")

        if event_type in ["milestone", "finding", "blocker"]:
            summaries.append(f"{event_type.upper()}: {truncate_text(text, 80)}")

    if not summaries:
        return "Working..."

    return " | ".join(summaries[-3:])  # Last 3 important events


def format_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """Format duration between two times as human-readable string."""
    if end_time is None:
        end_time = datetime.utcnow()

    duration = end_time - start_time

    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def validate_agent_name(name: str) -> bool:
    """Validate agent name."""
    return name in ["gemini", "codex", "claude"]


def validate_event_type(event_type: str) -> bool:
    """Validate event type."""
    valid_types = [
        "status", "progress", "finding", "task",
        "blocker", "milestone", "review", "error",
        "recovery", "permission_blocker"
    ]
    return event_type in valid_types


def sanitize_path(path: str) -> Path:
    """Sanitize and validate a file path."""
    # Remove any potentially dangerous characters
    sanitized = path.replace("..", "").replace("~", "")
    return Path(sanitized).resolve()


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    if not file_path.exists():
        return 0.0

    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def ensure_directory(dir_path: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    dir_path.mkdir(parents=True, exist_ok=True)


def count_lines(file_path: Path) -> int:
    """Count lines in a file."""
    if not file_path.exists():
        return 0

    with open(file_path, "r") as f:
        return sum(1 for _ in f)


def get_recent_lines(file_path: Path, n: int = 10) -> List[str]:
    """Get the last N lines from a file."""
    if not file_path.exists():
        return []

    with open(file_path, "r") as f:
        lines = f.readlines()

    return [line.strip() for line in lines[-n:]]


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def get_agent_color(agent_name: str) -> str:
    """Get color code for an agent."""
    colors = {
        "gemini": "#4285F4",  # Google Blue
        "codex": "#00A67E",   # OpenAI Green
        "claude": "#61DAFB",  # Claude Blue
    }
    return colors.get(agent_name, "#888888")


def format_event_for_display(event: Dict[str, Any]) -> str:
    """Format an event for display in logs."""
    event_type = event.get("type", "unknown")
    agent = event.get("agent", "unknown")
    payload = event.get("payload", {})
    text = payload.get("text", "")

    return f"[{agent.upper()}] {event_type.upper()}: {text}"


def calculate_progress(completed: int, total: int) -> int:
    """Calculate progress percentage."""
    if total == 0:
        return 0
    return min(100, int((completed / total) * 100))


def is_terminal_event(event_type: str) -> bool:
    """Check if event type indicates terminal state."""
    return event_type in ["milestone", "error", "blocker"]


def group_events_by_agent(events: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Group events by agent name."""
    grouped = {}
    for event in events:
        agent = event.get("agent", "unknown")
        if agent not in grouped:
            grouped[agent] = []
        grouped[agent].append(event)
    return grouped


def get_latest_event_by_type(
    events: List[Dict[str, Any]],
    event_type: str
) -> Optional[Dict[str, Any]]:
    """Get the most recent event of a specific type."""
    for event in reversed(events):
        if event.get("type") == event_type:
            return event
    return None
