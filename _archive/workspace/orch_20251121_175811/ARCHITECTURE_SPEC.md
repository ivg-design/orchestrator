# System Architecture Specification

This document details the technical implementation of the Meta-Orchestrator.

## Directory Structure

```
orchestrator/
├── __init__.py
├── main.py                 # CLI Entry point
├── config.py               # Configuration & Constants
├── models.py               # Pydantic Data Models
├── workers.py              # Worker Process Management
├── coordinator.py          # Main Orchestration Logic
├── review_engine.py        # Peer Review Logic
├── recovery.py             # Error Detection & Recovery
├── server.py               # FastAPI Web Server
└── static/
    └── dashboard.html      # Frontend UI
```

## Module Specifications

### 1. `models.py`
Contains all Pydantic definitions found in `DATA_MODELS.md`.
- **Exports**: `AgentEvent`, `AgentState`, `ReviewRequest`, `ReviewResponse`, `OrchestratorDecision`, `TaskBreakdown`.

### 2. `workers.py`
Handles low-level process management.
- **Class**: `WorkerManager`
- **Methods**:
  - `launch_gemini(task: str, dirs: List[str]) -> subprocess.Popen`
  - `launch_codex(task: str, cwd: str) -> subprocess.Popen`
  - `launch_claude(task: str, dirs: List[str]) -> subprocess.Popen`
  - `stop_worker(name: str)`
  - `get_worker_status(name: str) -> AgentState`
- **Responsibilities**:
  - Constructing correct CLI commands (flags, paths).
  - Managing stdout/stderr pipes.
  - Handling signals (SIGINT, SIGTERM).

### 3. `recovery.py`
Implements the self-healing logic.
- **Class**: `PermissionRecoveryEngine`
- **Methods**:
  - `monitor_stream(line: str, worker: str) -> Optional[RecoveryAction]`
  - `_fix_gemini(worker: str)`
  - `_fix_codex(worker: str)`
- **Responsibilities**:
  - Regex pattern matching on log streams.
  - Triggering restart actions in `WorkerManager` with modified flags.

### 4. `review_engine.py`
Manages the peer review workflow.
- **Class**: `ReviewOrchestrator`
- **Methods**:
  - `should_trigger_review(events: List[AgentEvent]) -> bool`
  - `create_review_request(context: Dict) -> ReviewRequest`
  - `evaluate_verdict(reviews: List[ReviewResponse]) -> OrchestratorDecision`
- **Policy**:
  - Implements the 4-rule decision tree (Stop, Pause, Warn, Continue).

### 5. `coordinator.py`
The central brain.
- **Class**: `Orchestrator`
- **Methods**:
  - `run(prompt: str)`: Main entry point.
  - `_decompose_task(prompt: str) -> TaskBreakdown`: Calls Main Claude.
  - `_loop()`: The main event loop.
- **Responsibilities**:
  - Instantiates `WorkerManager`, `RecoveryEngine`, `ReviewOrchestrator`.
  - Coordinates the flow described in `FLOW_DIAGRAM.md`.
  - Writes to the `workspace/` directory.

### 6. `server.py`
Provides the monitoring interface.
- **Framework**: FastAPI
- **Routes**: See `API_SPEC.md`.
- **Integration**: Shares state with `coordinator.py` (likely via a shared thread-safe State object or database/file watcher).

### 7. `main.py`
CLI wrapper.
- **Libs**: `typer` or `argparse`.
- **Commands**:
  - `orchestrate "prompt"`
  - `orchestrate resume {session_id}`

## Implementation Strategy

1. **State Persistence**:
   - The "Database" is simply the filesystem (`workspace/{session_id}/*.jsonl`).
   - The `coordinator` reads these files to rebuild state on restart.
   - `server.py` watches these files (or receives updates from `coordinator` if running in same process) to push SSE.

2. **Concurrency**:
   - The `coordinator` runs in a separate thread or process from the `server` (FastAPI).
   - `asyncio` is recommended for the File I/O and SSE streaming.

3. **Security**:
   - `safety.py` (optional separate module or part of `workers.py`) enforces the Sandbox rules for Claude Worker.