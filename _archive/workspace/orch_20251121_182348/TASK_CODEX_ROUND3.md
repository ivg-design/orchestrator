# CODEX TASK ROUND 3: ACTUALLY APPLY THE FIXES

Round 2 analyzed but didn't fix. NOW FIX THEM:

## CRITICAL: You MUST modify the actual code files, not just analyze!

## Fix 1: Add datetime import to workers.py (BLOCKER)
File: `/Users/ivg/orchestrator/orchestrator/workers.py`

ISSUE: No module-level datetime import causes NameError in `_parse_event` at line ~236
FIX: Add `from datetime import datetime` at top of file after other imports

## Fix 2: Recovery doesn't modify worker command (BLOCKER)
File: `/Users/ivg/orchestrator/orchestrator/recovery.py`

ISSUE: `_fix_codex_permissions` sets `worker.skip_git_check = True` but worker was already launched with old command
FIX: Worker must rebuild its command when relaunched - verify `build_command()` is called on relaunch

## Fix 3: Worker state updates not applied (BLOCKER)
File: `/Users/ivg/orchestrator/orchestrator/coordinator.py`

ISSUE: `_update_worker_states_from_events` doesn't apply parsed progress/status to WorkerState
FIX: Apply event data to worker.state.progress and worker.state.status fields

## REQUIREMENTS:
- Use Edit or Write tools to modify files
- Verify each fix with Read tool after applying
- Test that fixes work (no syntax errors)
- Report exactly what was changed

Work fast and surgically - only fix these 3 issues.
