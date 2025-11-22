# CLAUDE TASK: Implement Meta-Orchestration System Code

## Your Role
You are the **Code Writer & Implementer**. Implement all Python code for the meta-orchestration system.

## Context
- Architecture design: `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`
- Gemini's specs will be at: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_SPEC.md`
- Target directory: `/Users/ivg/orchestrator/`

## Your Task

### 1. Wait for Gemini's Specifications
First, wait for Gemini to complete the architecture specs. Monitor for:
- `ARCHITECTURE_SPEC.md`
- `DATA_MODELS.md`
- `API_SPEC.md`

### 2. Implement Core Python Modules

Implement the following in `/Users/ivg/orchestrator/orchestrator/`:

**models.py**:
- Pydantic models for all events and state per Gemini's spec
- Type hints and validation
- JSON serialization methods

**workers.py**:
- `launch_gemini(task, workspace, target_dir)` - with `--yolo --include-directories --output-format json`
- `launch_codex(task, workspace, target_dir)` - with `exec --json --dangerously-bypass-approvals-and-sandbox -C`
- `launch_claude_worker(task, workspace, target_dir)` - with `--print --dangerously-skip-permissions --strict-mcp-config --add-dir --output-format json`
- Process management and monitoring
- JSONL stream parsing

**coordinator.py**:
- Task analysis and breakdown logic
- Main orchestration loop
- Event monitoring from all three streams
- Decision policy implementation
- Session management

**review_engine.py**:
- Review trigger detection (milestones, blockers, events)
- Review request generation
- Review response parsing
- Verdict evaluation

**recovery.py**:
- Permission error pattern detection
- Auto-recovery for Gemini (`--include-directories` fix)
- Auto-recovery for Codex (`--skip-git-repo-check` fix)
- Escalation to user when needed

**server.py**:
- FastAPI app with CORS
- SSE endpoint for real-time events
- Agent status endpoints
- Health check endpoint

### 3. Implement Frontend

**static/dashboard.html**:
- Real-time EventSource connection
- Agent status display (Gemini, Codex, Claude Worker)
- Event log with filtering
- Review panel showing peer review results
- Orchestrator decision display

### 4. Create Entry Point

**orchestrate** (executable script):
- Parse command line arguments
- Initialize session
- Start FastAPI server
- Launch coordinator
- Handle graceful shutdown

## Implementation Guidelines

- Follow Gemini's specifications exactly
- Use Python 3.10+ features (async/await, type hints)
- Add error handling and logging
- Keep code modular and testable
- Add docstrings to all functions

## Deliverables

All code files in `/Users/ivg/orchestrator/` directory with proper structure.
