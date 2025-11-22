# Implementation Review (Claude Code)

## Code issues
- `workers.py` builds the Codex command without `--skip-git-repo-check`; `recovery._fix_codex_permissions` logs a relaunch "with skip flag" but never changes the command, so a trusted-directory failure will loop.
- Permission detection only scans `EventType.ERROR` events from JSONL; stderr is ignored and agents often don't emit structured error events, so recovery is unlikely to trigger. Worker outputs are reread from the start each poll with no offset tracking, causing duplicate triggers.
- Worker state/progress is never updated from parsed events; `session.workers` stays at initial statuses/progress, so SSE responses and completion detection are incorrect. `conduct_peer_review` is stubbed to always CONTINUE, bypassing the decision tree and review parsing entirely.
- Event parsing discards timestamps/agents from JSONL and defaults unknown event types to `status`, masking malformed messages instead of surfacing them.

## Security concerns
- Claude runs with `--dangerously-skip-permissions` but `SandboxConfig` is never enforced around the subprocess; no command filtering or directory restrictions are applied.
- Permission recovery lacks escalation surfacing to the API/UI, so permission denials could be silent.

## Integration problems
- FastAPI routes diverge from the spec: no session-scoped paths, the event stream at `/api/events/stream` emits only aggregate status instead of streaming typed agent events, and the manual review endpoint just invokes the stubbed `conduct_peer_review`.
- API payloads do not match the documented review request format (no reviewer/targets/context), and progress/status exposed via SSE will remain zero because worker states are not refreshed from events.

## Verdict
blocker
