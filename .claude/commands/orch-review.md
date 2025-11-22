# /orch-review Command

Trigger a manual peer review cycle immediately.

## Usage

The user wants to force the agents to review the current work.

1.  **Identify Session**: Get the active session ID.
2.  **Trigger Review**: Send a POST request to the orchestration control API.
3.  **Report**: Confirm the review has started.

## Execution

```bash
# Assuming the dashboard/API is running on localhost:8000
curl -X POST "http://localhost:8000/api/control/review?session=<SESSION_ID>"
```

*   If you don't have the session ID, try to find it from `orch-status` or the `workspace/` directory.
*   If no API is running, you may need to manually signal the orchestrator (e.g., by creating a `trigger_review` flag file in the session directory, if supported, or just telling the user to use the dashboard).

## Output

"Manual review cycle triggered. Agents (Codex/Gemini) will now review the current artifacts. Check the [Dashboard](http://localhost:8000/) for results."