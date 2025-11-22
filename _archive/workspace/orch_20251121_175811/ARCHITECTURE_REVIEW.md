# Architecture Review (Gemini Specs)

## Issues
- CLI/perms: Worker commands omit the orchestrator directory in Gemini's `--include-directories` list and never mention preparing/validating directories before launch, diverging from the approved requirement that all workers get explicit workspace/target/orchestrator access with pre-flight permission checks.
- Recovery: The `PermissionRecoveryEngine` description only covers regex matching and relaunch; it omits proactive permission setup, chmod fallback, recovery logging, and the codex `--skip-git-repo-check` relaunch path spelled out in the final design. Escalation handling and recovery event schema are also absent.
- Reviews: Triggering rules exclude the 15-minute no-event fallback and do not mention `[REQUEST_REVIEW]` events or multi-target review requests, leaving review timing/coverage ambiguous.
- API/flow gaps: The API spec is not session-scoped and lacks reviewer selection and context payloads; SSE schema is undefined beyond a single `message` event, so the dashboard/event parser contract is unclear. The flow diagram omits the new recovery branch and sandbox validation steps, so the path from permission failure → relaunch → decision tree is underspecified.

## Recommendations
- Document explicit directory requirements (workspace/target/orchestrator) and pre-launch permission validation for all workers, including chmod fallback and sandbox constraints.
- Expand recovery to show structured recovery events/logging, codex relaunch with `--skip-git-repo-check`, and escalation messaging when auto-fix fails.
- Align review triggers with the approved policy (milestone/blocker/request/user click plus 15-minute silence fallback) and define the review request schema (reviewer, targets[], context summaries, max_words).
- Update the API to be session-scoped and specify SSE event envelopes that carry typed `AgentEvent` records and recovery/decision updates; reflect the recovery and sandbox steps in the flow diagram.

## Verdict
concerns
