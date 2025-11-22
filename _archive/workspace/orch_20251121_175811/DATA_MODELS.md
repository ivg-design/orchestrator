# Data Models Specification

This document defines the Pydantic data models for the Meta-Orchestration System. These models ensure type safety and consistent data interchange between the orchestrator, workers, and the dashboard.

## Core Event Models

### `AgentEvent`
Represents a single event emitted by a worker agent.

```python
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from datetime import datetime

class AgentEvent(BaseModel):
    type: Literal[
        "status", 
        "progress", 
        "finding", 
        "task", 
        "blocker", 
        "milestone", 
        "review", 
        "error",
        "recovery"  # Added for orchestrator recovery events
    ]
    agent: Literal["gemini", "codex", "claude", "orchestrator"]
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "type": "progress",
                "agent": "gemini",
                "timestamp": "2025-11-21T17:00:00Z",
                "payload": {
                    "text": "Analyzing codebase structure...",
                    "progress": 45,
                    "file": "src/main.py"
                }
            }
        }
```

## Agent State Models

### `AgentState`
Tracks the runtime state of a worker.

```python
class AgentState(BaseModel):
    name: Literal["gemini", "codex", "claude"]
    status: Literal["starting", "running", "paused", "stopped", "failed", "completed"]
    pid: Optional[int] = None
    output_file: str
    current_task: str
    last_active: datetime = Field(default_factory=datetime.now)
    error_count: int = 0
```

## Review System Models

### `ReviewRequest`
Sent by the orchestrator to reviewers.

```python
from typing import List

class ReviewRequest(BaseModel):
    type: Literal["review_request"] = "review_request"
    reviewer: Literal["gemini", "codex", "claude"]
    targets: List[Literal["gemini", "codex", "claude"]]
    focus: str
    context: Dict[str, Any]  # Summaries of work to review
    max_words: int = 200
```

### `ReviewResponse`
The output from a reviewer agent.

```python
class ReviewResponse(BaseModel):
    type: Literal["peer_review"] = "peer_review"
    reviewer: Literal["gemini", "codex", "claude"]
    target: Literal["gemini", "codex", "claude"]
    verdict: Literal["approved", "concerns", "blocker"]
    issues: List[str]
    recommendations: List[str]
```

### `OrchestratorDecision`
The result of the policy engine's evaluation of reviews.

```python
class OrchestratorDecision(BaseModel):
    action: Literal["STOP_AND_ESCALATE", "PAUSE_AND_CLARIFY", "LOG_WARNING", "CONTINUE"]
    reason: str
    next_step: str
```

## Task Management Models

### `TaskDefinition`
A single sub-task assigned to an agent.

```python
class TaskDefinition(BaseModel):
    agent: Literal["gemini", "codex", "claude"]
    role: str
    responsibilities: List[str]
    deliverables: List[str]
    complexity: str
    estimated_tokens: str
    raw_prompt: Optional[str] = None # The actual prompt text sent to CLI
```

### `TaskBreakdown`
The result of the initial task decomposition.

```python
class TaskBreakdown(BaseModel):
    gemini: TaskDefinition
    claude: TaskDefinition
    codex: TaskDefinition
```

## Recovery Models

### `RecoveryAction`
Logs an automated recovery attempt.

```python
class RecoveryAction(BaseModel):
    worker: str
    issue: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool
```