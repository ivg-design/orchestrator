# Meta-Orchestration System

A sophisticated system for coordinating multiple AI agents (Gemini, Codex, and Claude) to work collaboratively on complex tasks.

## Overview

The Meta-Orchestration System breaks down complex user tasks into specialized sub-tasks and distributes them across three AI agents:

- **Gemini**: Architecture & Design expert (heavy load - 40-50% of work)
- **Codex**: Problem Solver & Reviewer (minimal load - 10-20% of work)
- **Claude Worker**: Code Writer & Implementer (heavy load - 40-50% of work)

## Features

- Event-driven peer review system
- Automatic permission recovery
- Real-time web dashboard
- JSON streaming output from all workers
- Proactive error detection and recovery
- Resource management and limits
- Session persistence and state tracking

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure you have the required AI agents installed:
   - `gemini` CLI
   - `codex` CLI
   - `claude` CLI

## Usage

### Basic Usage

```bash
./orchestrate "Add user authentication to the application"
```

### With Custom Workspace

```bash
./orchestrate "Implement dark mode" --workspace /path/to/workspace
```

### Specify Target Project

```bash
./orchestrate "Add tests" --target /path/to/project
```

### Headless Mode (No Dashboard)

```bash
./orchestrate "Fix bugs" --no-dashboard
```

### Verbose Logging

```bash
./orchestrate "Optimize performance" --verbose
```

### Custom Dashboard Port

```bash
./orchestrate "Add feature X" --port 9000
```

## Architecture

### Directory Structure

```
orchestrator/
├── orchestrate                 # Entry point script
├── orchestrator/
│   ├── __init__.py
│   ├── models.py              # Pydantic data models
│   ├── workers.py             # Worker process management
│   ├── coordinator.py         # Main orchestration logic
│   ├── review_engine.py       # Peer review system
│   ├── recovery.py            # Permission recovery engine
│   └── server.py              # FastAPI dashboard server
├── static/
│   └── dashboard.html         # Real-time web dashboard
├── workspace/                 # Session workspaces (auto-created)
│   └── {session_id}/
│       ├── gemini.jsonl       # Gemini output stream
│       ├── codex.jsonl        # Codex output stream
│       ├── claude.jsonl       # Claude output stream
│       └── reviews/           # Peer review artifacts
└── requirements.txt
```

### Components

#### Coordinator (`coordinator.py`)

The main orchestration engine that:
- Analyzes user tasks
- Breaks down tasks into agent-specific assignments
- Launches and monitors workers
- Triggers event-based peer reviews
- Makes coordination decisions
- Handles recovery and error management

#### Workers (`workers.py`)

Manages worker agent processes:
- Launches Gemini with `--include-directories` permissions
- Launches Codex with `-C` working directory
- Launches Claude with `--add-dir` sandbox restrictions
- Parses JSON event streams
- Monitors process status

#### Review Engine (`review_engine.py`)

Event-based peer review system:
- Detects review triggers (milestones, blockers, requests)
- Creates review requests with context
- Parses review responses
- Evaluates reviews using decision policy
- Makes orchestrator decisions

#### Recovery Engine (`recovery.py`)

Automatic error recovery:
- Detects permission errors
- Auto-fixes Gemini directory permissions
- Auto-fixes Codex git repository issues
- Escalates unrecoverable errors to user
- Tracks recovery actions

#### Server (`server.py`)

FastAPI dashboard server:
- Real-time SSE event streaming
- Worker status endpoints
- Review and decision endpoints
- Control endpoints (pause, resume, stop)
- Health checks

## Dashboard

The real-time dashboard provides:

- **Session Information**: Session ID, user prompt, status
- **Worker Agents**: Real-time status and progress for each agent
- **Latest Decision**: Current orchestrator decision and reasoning
- **Peer Reviews**: Review results and verdicts
- **Event Log**: Live event stream from all workers
- **Controls**: Trigger review, pause, resume, stop

Access at: `http://localhost:8000` (default port)

## Event Types

Workers emit JSON events:

```json
{
  "type": "status|progress|finding|task|blocker|milestone|review|error",
  "agent": "gemini|codex|claude",
  "timestamp": "2025-11-21T17:00:00Z",
  "payload": {
    "text": "...",
    "progress": 45,
    "file": "/path/to/file"
  }
}
```

## Decision Policy

The orchestrator evaluates peer reviews using a deterministic decision tree:

1. **Any blocker** → STOP_AND_ESCALATE
2. **Majority concerns (2+)** → PAUSE_AND_CLARIFY
3. **Single concern** → LOG_WARNING
4. **All approved** → CONTINUE

## Recovery System

### Proactive Recovery

Before launching workers:
1. Validate directories exist
2. Check read/write permissions
3. Create missing directories
4. Set appropriate permissions

### Reactive Recovery

During execution:
1. Monitor event streams for errors
2. Detect error patterns (permission denied, git errors, etc.)
3. Attempt auto-recovery (relaunch with correct flags)
4. Escalate to user if auto-fix impossible

## Security

Claude worker runs in a restricted sandbox:
- Limited to workspace and target directories
- Blocked dangerous commands (rm -rf, dd, mkfs)
- Requires confirmation for high-risk operations
- Monitors for suspicious patterns (sudo, curl | sh)

## Logging

Logs are written to:
- `orchestrator.log` (file)
- stdout (console)

Use `--verbose` flag for debug-level logging.

## License

MIT
