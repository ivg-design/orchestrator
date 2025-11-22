# CODEX TASK ROUND 2: Fix Critical Blockers

You identified these BLOCKER issues. Now FIX THEM:

## 1. Fix Permission Recovery (HIGH PRIORITY)
File: `orchestrator/recovery.py:_fix_codex_permissions`

ISSUE: Method doesn't actually add `--skip-git-repo-check` flag
FIX: Modify the worker's command to include the flag before restart

## 2. Fix Event Parsing Bug (HIGH PRIORITY)
File: `orchestrator/workers.py:_parse_event`

ISSUE: NameError - 'datetime' referenced before assignment when no timestamp
FIX: Import datetime at module level, handle missing timestamps

## 3. Fix Worker State Updates (HIGH PRIORITY)
File: `orchestrator/coordinator.py:_update_worker_states_from_events`

ISSUE: Progress/status never applied to worker states
FIX: Actually apply parsed progress/status values to WorkerState objects

Write the fixed code directly to the files. Be surgical - only fix what's broken.
