# Orchestration Flow

This document describes the logical flow of the Meta-Orchestrator, from user input to final delivery.

## 1. Startup & Initialization
1. **User Command**: `/orchestrate "Build a Todo App"`
2. **CLI Entry (`cli.py`)**: 
   - Validates environment (API keys, tools).
   - Creates a new session directory: `workspace/{session_id}/`.
   - Proactively checks/fixes permissions for workspace and target directories.
3. **Server Start**: Backgrounds `server.py` (FastAPI) to serve the Dashboard.

## 2. Analysis & Decomposition
1. **Orchestrator Agent (Main Claude)**: 
   - Receives the raw prompt.
   - Calls `decompose_task(prompt)` -> returns `TaskBreakdown` JSON.
   - **Output**: 3 distinct task prompts for Gemini, Claude, and Codex.

## 3. Worker Launch (Parallel)
1. **Permission Check**: `prepare_worker_environment()` runs for each agent.
2. **Launch**: `launch_workers_with_fallback()` is called.
   - Tries Tier 1 (Gemini + Claude + Codex).
   - If failure, degrades to Tier 2/3/4.
3. **Processes**: Agents are started as subprocesses, piping stdout to `workspace/{session_id}/{agent}.jsonl`.

## 4. Main Orchestration Loop (`coordinator.py`)

The loop runs continuously until "Definition of Done" is met.

### A. Monitor Streams
- Reads new lines from `*.jsonl` files.
- Parses lines into `AgentEvent` objects.
- Broadcasts events to `GET /events` (SSE).

### B. Recovery Check (`recovery.py`)
- **Input**: Stream text/events.
- **Logic**: Matches error patterns (regex).
  - *Gemini*: "Path must be within..." -> Relaunch with `--include-directories`.
  - *Codex*: "Not inside a trusted..." -> Relaunch with `-C` / `--skip-git-repo-check`.
  - *Claude*: "Permission denied" -> Relaunch.
- **Action**: `stop_worker()` -> `launch_worker(corrected_flags)`.

### C. Event Triggers
- **Milestone**: Agent finishes a major step.
- **Blocker**: Agent explicitly asks for help.
- **Request Review**: Agent requests feedback.
- **User Action**: Manual "Review Now" button.

### D. Peer Review Cycle (`review_engine.py`)
*Triggered by C above.*
1. **Pause**: Non-reviewing agents are paused (SIGSTOP or just logical ignore).
2. **Request**: Orchestrator sends `ReviewRequest` to Reviewer Agent (usually Gemini or Codex).
3. **Wait**: Orchestrator waits for `ReviewResponse`.
4. **Evaluation**: `evaluate_peer_reviews(response)` -> `OrchestratorDecision`.
   - **STOP**: Critical issues. Escalate to user.
   - **PAUSE**: Major concerns. Clarify requirements.
   - **WARN**: Minor issues. Log and continue.
   - **CONTINUE**: All good.
5. **Resume**: Agents unpaused.

## 5. Definition of Done
The loop terminates when:
1. All agents emit `milestone: Complete`.
2. Final Peer Review is `approved`.
3. No active `blocker` events.
4. No active `recovery` actions pending.

## 6. Synthesis
1. Orchestrator aggregates all created files.
2. Runs final integration verification.
3. Generates a summary report.
4. Exits.