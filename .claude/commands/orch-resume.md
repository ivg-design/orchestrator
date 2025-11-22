# /orch-resume Command

Resume a paused or stopped orchestration session.

## Usage

The user has invoked this command with a session ID. Your task is to:

1. Validate the session ID exists in workspace/
2. Call the API to resume the session: `POST /api/v1/{session_id}/resume`
3. Display confirmation and dashboard link

## Example

If user types: `/orch-resume orch_20251121_123456`

You should:
1. Verify `workspace/orch_20251121_123456/` exists
2. Send resume request to API
3. Display: "Session orch_20251121_123456 resumed"
4. Display: "Dashboard: http://localhost:8000/?session=orch_20251121_123456"
5. Optionally tail the event stream to show progress

## Error Handling

- If session doesn't exist: "Session not found. Use /orch-status to see active sessions"
- If API call fails: Display error message and suggest checking if server is running
- If session is already running: "Session is already running"

## Notes

- Resuming restores all agent states from the workspace
- Monitoring and peer review will continue from where it left off
- Any pending decisions will be re-evaluated
