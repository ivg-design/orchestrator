# /orch-status Command

Check the status of the current or most recent orchestration session.

## Usage

The user has invoked this command. Your task is to:

1.  **Find Active Session**: Look in the `workspace/` directory for the most recent session folder (`orch_YYYYMMDD_...`).
2.  **Read State**: Check the `session_state.json` or agent logs within that directory.
3.  **Report**: Display a summary of the current state.

## Execution

You can often get a quick status by querying the running API or checking the file system:

```bash
# Check for running python processes related to orchestration
ps aux | grep orchestrator

# OR check the latest log tail
ls -t orchestrator.log | head -n 1 | xargs tail -n 20
```

## Output Template

```markdown
### Orchestration Status
**Session:** `orch_2023...`
**Status:** `RUNNING` | `PAUSED` | `COMPLETED` | `FAILED`

**Agent Progress:**
*   **Gemini (Architect):** [====..] 60% - Designing API
*   **Claude (Implementer):** [==....] 30% - Waiting for specs
*   **Codex (Reviewer):** [......] 0% - Idle

**Latest Decision:**
`CONTINUE` - Architecture approved, proceeding to implementation.

[View Dashboard](http://localhost:8000/?session=<SESSION_ID>)
```