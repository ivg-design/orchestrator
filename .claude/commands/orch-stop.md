# /orch-stop Command

Gracefully stop the current orchestration session.

## Usage

The user wants to halt the autonomous agents.

1.  **Identify Session**: Get the active session ID.
2.  **Send Stop Signal**: Contact the orchestration API or terminate the process.
3.  **Verify**: Ensure all agent processes have ceased.

## Execution

**Method 1: API (Preferred)**

```bash
curl -X POST "http://localhost:8000/api/control/stop?session=<SESSION_ID>"
```

**Method 2: Process Termination (Fallback)**

```bash
pkill -f "python -m orchestrator.main"
```

## Output

"Orchestration session `<SESSION_ID>` has been stopped.
*   State saved to `workspace/<SESSION_ID>/`
*   All agent processes terminated."