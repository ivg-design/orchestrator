"""Pydantic models for orchestration events and state management."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    """Enumeration of available agents."""
    GEMINI = "gemini"
    CODEX = "codex"
    CLAUDE = "claude"


class EventType(str, Enum):
    """Types of events that can be emitted by agents."""
    STATUS = "status"
    PROGRESS = "progress"
    FINDING = "finding"
    TASK = "task"
    BLOCKER = "blocker"
    MILESTONE = "milestone"
    REVIEW = "review"
    ERROR = "error"
    RECOVERY = "recovery"
    PERMISSION_BLOCKER = "permission_blocker"


class Verdict(str, Enum):
    """Peer review verdict types."""
    APPROVED = "approved"
    CONCERNS = "concerns"
    BLOCKER = "blocker"


class Action(str, Enum):
    """Orchestrator decision actions."""
    CONTINUE = "CONTINUE"
    LOG_WARNING = "LOG_WARNING"
    PAUSE_AND_CLARIFY = "PAUSE_AND_CLARIFY"
    STOP_AND_ESCALATE = "STOP_AND_ESCALATE"


class WorkerStatus(str, Enum):
    """Worker agent status."""
    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


# Event Payload Models

class EventPayload(BaseModel):
    """Base payload for events."""
    text: str
    progress: Optional[int] = Field(None, ge=0, le=100)
    file: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class Event(BaseModel):
    """Base event model emitted by agents."""
    type: EventType
    agent: AgentName
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: EventPayload

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "type": self.type.value,
            "agent": self.agent.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload.dict(exclude_none=True)
        }


# Review Models

class ReviewRequest(BaseModel):
    """Request for peer review."""
    reviewer: AgentName
    targets: List[AgentName]
    focus: str
    context: Dict[str, str]
    max_words: int = 200


class PeerReview(BaseModel):
    """Peer review response from an agent."""
    reviewer: AgentName
    target: AgentName
    verdict: Verdict
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "reviewer": self.reviewer.value,
            "target": self.target.value,
            "verdict": self.verdict.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


# Decision Models

class OrchestratorDecision(BaseModel):
    """Decision made by orchestrator based on reviews."""
    action: Action
    reason: str
    next_steps: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Task Breakdown Models

class TaskAssignment(BaseModel):
    """Task assignment for a specific agent."""
    agent: AgentName
    role: str
    responsibilities: List[str]
    deliverables: List[str]
    complexity: str
    estimated_tokens: str


class TaskBreakdown(BaseModel):
    """Complete task breakdown for all agents."""
    gemini: TaskAssignment
    claude: TaskAssignment
    codex: TaskAssignment
    user_prompt: str
    session_id: str


# Worker State Models

class WorkerState(BaseModel):
    """State information for a worker agent."""
    name: AgentName
    status: WorkerStatus
    task: Optional[str] = None
    process_id: Optional[int] = None
    start_time: Optional[datetime] = None
    last_event: Optional[Event] = None
    progress: int = Field(0, ge=0, le=100)
    error_count: int = 0


# Recovery Models

class RecoveryAction(BaseModel):
    """Recovery action taken by the orchestrator."""
    worker: AgentName
    issue: str
    action: str
    directories: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PermissionBlocker(BaseModel):
    """Permission blocker requiring user intervention."""
    worker: AgentName
    error: str
    action_required: str
    suggestions: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Session Models

class SessionState(BaseModel):
    """Overall orchestration session state."""
    session_id: str
    workspace_dir: str
    target_project_dir: str
    user_prompt: str
    workers: Dict[AgentName, WorkerState]
    reviews: List[PeerReview] = Field(default_factory=list)
    decisions: List[OrchestratorDecision] = Field(default_factory=list)
    recovery_actions: List[RecoveryAction] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    is_complete: bool = False


# Resource Limits

class ResourceLimits(BaseModel):
    """Resource limits for worker processes."""
    cpu_percent: int = 50
    memory_mb: int = 2048
    max_runtime: int = 3600  # seconds


# Sandbox Configuration

class SandboxConfig(BaseModel):
    """Sandbox configuration for Claude worker."""
    allowed_dirs: List[str]
    blocked_commands: List[str] = Field(default_factory=lambda: [
        "rm -rf",
        "dd",
        "mkfs",
        "format",
        "fdisk"
    ])
    require_confirm: List[str] = Field(default_factory=lambda: [
        "git push",
        "npm publish",
        "pip install",
        "cargo publish"
    ])
    monitor_patterns: List[str] = Field(default_factory=lambda: [
        r"sudo\s+",
        r"curl.*\|\s*sh",
        r"wget.*\|\s*sh"
    ])
