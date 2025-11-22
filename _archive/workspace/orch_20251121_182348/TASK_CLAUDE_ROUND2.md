# CLAUDE TASK ROUND 2: Apply Critical Blocker Fixes

You are Claude worker agent. Apply these 3 blocker fixes NOW:

## Fix 1: Add datetime import to workers.py
File: `/Users/ivg/orchestrator/orchestrator/workers.py`

Add `from datetime import datetime` to the imports at the top of the file (after line 5).

## Fix 2: Verify recovery.py command rebuild
File: `/Users/ivg/orchestrator/orchestrator/recovery.py`

The `_fix_codex_permissions` method already sets `worker.skip_git_check = True` and calls `worker.launch()`. Verify that `worker.launch()` calls `build_command()` which will pick up the new skip_git_check flag.

## Fix 3: Worker state updates already implemented
File: `/Users/ivg/orchestrator/orchestrator/coordinator.py`

Check lines 248-278 - the `_update_worker_states_from_events` method already applies progress and status updates. Verify this is correct.

## Requirements:
- Use Edit tool to add the datetime import
- Use Read tool to verify the other two issues
- Report exactly what you found and what you changed
- Work surgically - only fix what's needed
