# Recovery Engine Specification

## Overview
The `PermissionRecoveryEngine` ensures system resilience by actively monitoring worker streams for permission-related failures and automatically applying corrective actions. It includes proactive setup, reactive fixes, and structured logging.

## 1. Proactive Setup (Pre-Launch)

Before any worker is launched, the `prepare_worker_environment` function runs:

```python
def prepare_worker_environment(workspace, target, orchestrator):
    dirs = [workspace, target, orchestrator]
    for d in dirs:
        if not os.path.exists(d):
            if d == workspace:
                os.makedirs(d, exist_ok=True)
            else:
                raise FileNotFoundError(f"Critical directory missing: {d}")
        
        if not os.access(d, os.R_OK | os.W_OK):
            try:
                os.chmod(d, 0o755) # Attempt Auto-Fix
            except PermissionError:
                raise PermissionError(f"Cannot fix permissions for {d}")
```

## 2. Reactive Recovery (Runtime)

The engine monitors `stderr` and JSON `stdout` for specific error patterns.

### Regex Trigger Map

| Agent | Pattern (Regex) | Issue Type | Recovery Action |
|---|---|---|---|
| **Gemini** | `Path must be within.*workspace directories` | `DIR_SCOPE_ERROR` | Relaunch with missing dir in `--include-directories` |
| **Gemini** | `Permission denied` | `FS_PERM_ERROR` | `chmod +x` target dir & Relaunch |
| **Codex** | `Not inside a trusted directory` | `GIT_TRUST_ERROR` | Relaunch with `--skip-git-repo-check` |
| **Codex** | `Repository check failed` | `GIT_CHECK_ERROR` | Relaunch with `--skip-git-repo-check` |
| **Claude** | `Access blocked` | `SANDBOX_ERROR` | Verify path is in allowed list; if valid, relaunch with `--add-dir` |

### Recovery Actions

#### Action: `RELAUNCH_WITH_FLAGS`
1. **Stop** the failing worker process (SIGTERM).
2. **Capture** the last task/prompt.
3. **Modify** the launch command flags (e.g., add `--skip-git-repo-check` or append path to `--include-directories`).
4. **Start** a new worker instance.
5. **Replay** the last task.

## 3. Recovery Event Schema

When a recovery action is taken, the Orchestrator emits a structured event via SSE.

```json
{
  "type": "recovery",
  "id": "rec_123456789",
  "timestamp": "2025-11-21T10:05:00Z",
  "payload": {
    "worker": "codex",
    "issue_detected": "Not inside a trusted directory",
    "action_taken": "RELAUNCH_WITH_SKIP_GIT_CHECK",
    "status": "success",
    "retry_count": 1
  }
}
```

## 4. Escalation Policy

If `retry_count > 3` OR `chmod` fails:

1. **State Change**: Orchestrator moves to `PAUSED` state.
2. **Notification**: User alert triggered via Dashboard.
3. **Event**:
   ```json
   {
     "type": "blocker",
     "payload": {
       "text": "Persistent permission error for Codex on /target/dir. Manual intervention required.",
       "details": "Chmod failed. Please check directory ownership."
     }
   }
   ```
4. **Wait**: Blocks until User resumes via Dashboard or `/resume` command.
