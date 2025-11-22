# /orch-pause Command

Gracefully pause the current orchestration session.

## Usage

The user has invoked this command. Your task is to:

1. Get the current active session ID
2. Call the API to pause: `POST /api/v1/{session_id}/pause`
3. Confirm the pause action

## Implementation

You should:
1. Identify the running session (read from workspace/ or server)
2. Send pause request: `curl -X POST http://localhost:8000/api/v1/{session_id}/pause`
3. Display: "Orchestration paused. Use /orch-resume to continue"

## Behavior

When paused:
- All worker agents remain running but monitoring loop pauses
- No new peer reviews are triggered
- Events continue to accumulate
- State is preserved in workspace files
- Session can be resumed at any time

## Notes

- Pause is graceful - doesn't kill worker processes
- Use /orch-stop to fully terminate the session
- Paused sessions can be resumed days later
