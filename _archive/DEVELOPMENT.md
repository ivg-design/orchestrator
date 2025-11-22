# Development Guide

## Architecture Overview

The meta-orchestration system is built with a modular architecture:

```
orchestrator/
├── models.py           # Pydantic data models (events, state, reviews)
├── workers.py          # Worker process management
├── coordinator.py      # Main orchestration logic
├── review_engine.py    # Peer review system
├── recovery.py         # Error detection and recovery
└── server.py           # FastAPI dashboard backend
```

## Core Components

### 1. Models (`models.py`)

Defines all data structures using Pydantic for validation:

- **Event Models**: `Event`, `EventPayload`, `EventType`
- **Review Models**: `PeerReview`, `ReviewRequest`, `Verdict`
- **State Models**: `WorkerState`, `SessionState`, `WorkerStatus`
- **Decision Models**: `OrchestratorDecision`, `Action`
- **Task Models**: `TaskBreakdown`, `TaskAssignment`
- **Recovery Models**: `RecoveryAction`, `PermissionBlocker`

**Key Features**:
- Type validation
- JSON serialization
- Enum types for consistency
- Datetime handling

### 2. Workers (`workers.py`)

Manages agent processes:

**Classes**:
- `WorkerProcess`: Single worker management
- `WorkerManager`: Multi-worker coordination

**Key Methods**:
- `build_command()`: Constructs agent-specific CLI commands
- `launch()`: Starts worker process with output redirection
- `read_events()`: Parses JSONL event streams
- `is_running()`: Checks process status
- `stop()`: Gracefully terminates worker

**Agent-Specific Launching**:
```python
# Gemini - with directory permissions
cmd = ["gemini", "--yolo", "--include-directories", ...]

# Codex - with working directory
cmd = ["codex", "exec", "--json", "-C", ...]

# Claude - with sandbox
cmd = ["claude", "--print", "--add-dir", ...]
```

### 3. Coordinator (`coordinator.py`)

Main orchestration logic:

**Key Methods**:
- `decompose_task()`: Breaks user task into 3 agent assignments
- `format_task_prompt()`: Formats prompts for each agent
- `launch_all_workers()`: Launches Gemini, Codex, Claude
- `monitor_loop()`: Main event monitoring loop
- `conduct_peer_review()`: Triggers review cycle
- `check_completion()`: Determines when work is done

**Orchestration Flow**:
1. Decompose user task
2. Prepare environments
3. Launch workers
4. Monitor events
5. Detect errors → trigger recovery
6. Detect triggers → conduct reviews
7. Evaluate reviews → make decisions
8. Check completion
9. Generate summary

### 4. Review Engine (`review_engine.py`)

Event-based peer review system:

**Key Methods**:
- `should_trigger_review()`: Event-based trigger detection
- `create_review_request()`: Generates review requests
- `parse_review_response()`: Parses agent review output
- `evaluate_reviews()`: Applies decision policy

**Decision Policy**:
```python
if any_blockers:
    return STOP_AND_ESCALATE
elif majority_concerns:
    return PAUSE_AND_CLARIFY
elif single_concern:
    return LOG_WARNING
else:
    return CONTINUE
```

**Review Triggers**:
- `MILESTONE` events
- `BLOCKER` events
- `REQUEST_REVIEW` events
- User manual trigger
- 15-minute fallback

### 5. Recovery Engine (`recovery.py`)

Automatic error detection and recovery:

**Key Methods**:
- `check_for_errors()`: Scans events for error patterns
- `attempt_recovery()`: Tries to fix detected errors
- `prepare_worker_environment()`: Proactive permission setup

**Error Patterns**:
- Gemini: "workspace directories" → relaunch with correct flags
- Codex: "git repository" → add `--skip-git-repo-check`
- Generic: "Permission denied" → escalate to user

**Recovery Actions**:
1. Detect error pattern
2. Stop failed worker
3. Modify launch command
4. Relaunch worker
5. Log recovery action

### 6. Server (`server.py`)

FastAPI backend for dashboard:

**Endpoints**:

```python
# Information
GET  /                      # Dashboard HTML
GET  /health                # Health check
GET  /api/session           # Session info
GET  /api/workers           # Worker states
GET  /api/reviews           # Review summary
GET  /api/decisions         # Decision history
GET  /api/recovery          # Recovery actions
GET  /api/summary           # Complete summary

# Real-time
GET  /api/events/stream     # SSE event stream

# Control
POST /api/control/pause     # Pause orchestration
POST /api/control/resume    # Resume orchestration
POST /api/control/stop      # Stop orchestration
POST /api/control/review    # Trigger review
```

**SSE Stream**:
- Sends updates every 2 seconds
- Worker status updates
- Latest decision updates
- Session status updates

## Development Setup

### 1. Clone and Install

```bash
cd /Users/ivg/orchestrator
pip install -r requirements.txt
pip install -e .  # Editable install
```

### 2. Run Tests

```bash
# Unit tests (TODO: add tests)
pytest tests/

# Integration test
./orchestrate "test task" --verbose
```

### 3. Development Mode

```bash
# Run with verbose logging
./orchestrate "task" --verbose

# Monitor logs
tail -f orchestrator.log

# Check event streams
tail -f workspace/orch_*/gemini.jsonl
```

## Adding New Features

### Adding a New Event Type

1. Add to `EventType` enum in `models.py`:
```python
class EventType(str, Enum):
    NEW_TYPE = "new_type"
```

2. Update event parsing in `workers.py`:
```python
def _parse_event(self, data: Dict) -> Optional[Event]:
    # Handle new event type
    pass
```

3. Update dashboard to display new event type in `dashboard.html`

### Adding a New Worker

1. Add to `AgentName` enum in `models.py`:
```python
class AgentName(str, Enum):
    NEW_AGENT = "new_agent"
```

2. Add launch method in `workers.py`:
```python
def _build_new_agent_command(self) -> List[str]:
    return ["new-agent", "args..."]
```

3. Update `build_command()` to handle new agent

4. Add to task breakdown in `coordinator.py`

### Adding a New Recovery Pattern

1. Add error pattern in `recovery.py`:
```python
ERROR_PATTERNS = {
    AgentName.NEW_AGENT: [
        r"new error pattern",
    ]
}
```

2. Add recovery method:
```python
def _fix_new_agent_error(self, worker: WorkerProcess) -> RecoveryAction:
    # Fix logic here
    pass
```

3. Update `attempt_recovery()` to call new method

## Code Style

### Python Guidelines

- Use Python 3.10+ features (type hints, match/case)
- Follow PEP 8 style guide
- Use Pydantic for data validation
- Add docstrings to all public methods
- Use type hints everywhere
- Keep functions focused and small

### Example:

```python
def process_event(event: Event) -> Optional[Action]:
    """
    Process an event and determine if action is needed.

    Args:
        event: Event to process

    Returns:
        Action to take, or None if no action needed
    """
    if event.type == EventType.BLOCKER:
        return Action.STOP_AND_ESCALATE
    return None
```

## Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(f"Worker {name} started with PID {pid}")
logger.error(f"Failed to launch {name}: {error}", exc_info=True)

# Bad
print("Worker started")  # Don't use print
```

## Testing

### Unit Test Example

```python
import pytest
from orchestrator.models import Event, EventType, AgentName

def test_event_creation():
    event = Event(
        type=EventType.MILESTONE,
        agent=AgentName.GEMINI,
        payload={"text": "Complete"}
    )
    assert event.type == EventType.MILESTONE
    assert event.agent == AgentName.GEMINI
```

### Integration Test Example

```python
from orchestrator.coordinator import Coordinator

def test_task_decomposition():
    coordinator = Coordinator(...)
    breakdown = coordinator.decompose_task("Add feature")

    assert breakdown.gemini.agent == AgentName.GEMINI
    assert breakdown.claude.agent == AgentName.CLAUDE
    assert breakdown.codex.agent == AgentName.CODEX
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Events

```bash
# Pretty-print JSONL
cat workspace/orch_*/gemini.jsonl | jq .

# Filter by event type
cat workspace/orch_*/gemini.jsonl | jq 'select(.type == "error")'
```

### Monitor Process

```bash
# Check worker processes
ps aux | grep -E "gemini|codex|claude"

# Monitor resource usage
top -pid $(pgrep -f orchestrate)
```

## Performance Optimization

### Current Limits

```python
worker_limits = {
    "cpu_percent": 50,      # Max 50% CPU
    "memory_mb": 2048,      # Max 2GB RAM
    "max_runtime": 3600     # 1 hour timeout
}
```

### Optimization Tips

1. **Event Stream Parsing**: Use incremental parsing, not full file reads
2. **Review Triggers**: Event-based, not time-based polling
3. **Dashboard Updates**: 2-second intervals, not real-time
4. **Process Management**: Proper cleanup to avoid zombie processes
5. **Memory**: Stream events, don't load all into memory

## Security Considerations

### Sandbox Restrictions

```python
blocked_commands = [
    "rm -rf",      # Dangerous deletion
    "dd",          # Disk operations
    "mkfs",        # Filesystem formatting
    "sudo",        # Privilege escalation
]

monitor_patterns = [
    r"curl.*\|\s*sh",   # Pipe to shell
    r"wget.*\|\s*sh",   # Download and execute
]
```

### Best Practices

1. Always validate user input
2. Use subprocess with proper escaping
3. Limit file system access
4. Monitor for suspicious patterns
5. Log all actions for audit trail

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Update documentation
5. Submit pull request

## TODO

- [ ] Add comprehensive test suite
- [ ] Add CLI argument validation
- [ ] Implement review request/response protocol
- [ ] Add metrics and monitoring
- [ ] Support custom agent configurations
- [ ] Add session resume capability
- [ ] Implement resource limit enforcement
- [ ] Add agent health checks
- [ ] Support distributed orchestration
- [ ] Add plugin system for custom agents
