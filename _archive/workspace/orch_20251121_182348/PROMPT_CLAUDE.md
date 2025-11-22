# CLAUDE TASK: Fix Blockers & Complete Implementation

## Your Role
You are the **Code Implementer**. Fix all blocker issues from Codex's review and complete the full implementation.

## Context
- Implementation directory: `/Users/ivg/orchestrator/`
- Codex blockers: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/IMPLEMENTATION_REVIEW.md`
- Architecture specs: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_SPEC.md`
- Gemini's new specs: `/Users/ivg/orchestrator/workspace/orch_20251121_182348/` (wait for Gemini to complete)
- Workspace: `/Users/ivg/orchestrator/workspace/orch_20251121_182348/`

## Your Tasks

### Phase 1: Fix Critical Blockers (CRITICAL PRIORITY)

**1. Fix `orchestrator/workers.py`**
- Add `--skip-git-repo-check` flag to Codex worker command builder
- Verify all three agents get correct CLI flags:
  - Gemini: `--yolo --include-directories <workspace> --include-directories <target> --include-directories <orchestrator> --output-format json`
  - Codex: `exec --json --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C <target>`
  - Claude: `--print --dangerously-skip-permissions --strict-mcp-config --add-dir <workspace> --add-dir <target> --add-dir <orchestrator> --output-format json`

**2. Fix `orchestrator/recovery.py`**
- Implement stderr parsing in addition to JSONL event scanning
- Add offset tracking to prevent duplicate event processing
- Implement actual command modification in `_fix_codex_permissions()` to add `--skip-git-repo-check`
- Add escalation surfacing (emit events, update API state)
- Implement structured recovery event emission

**3. Fix Event Parsing & Worker State Updates**
- Update `coordinator.py` to refresh worker states from parsed events
- Extract and preserve timestamps/agent info from JSONL events
- Handle malformed JSON properly (log error, don't default to "status")
- Implement progress calculation based on event milestones

**4. Complete `review_engine.py`**
- Implement full `conduct_peer_review()` with 4-rule decision tree:
  1. Any BLOCKER verdict → STOP_AND_ESCALATE
  2. Majority (≥2) CONCERNS → PAUSE_AND_CLARIFY
  3. Single CONCERN → LOG_WARNING
  4. All APPROVED → CONTINUE
- Parse review responses properly
- Emit review decision events

**5. Fix `orchestrator/server.py`**
- Convert all routes to session-scoped: `/api/{session_id}/...`
- Implement proper SSE streaming with typed `AgentEvent` records
- Fix event stream to emit individual agent events (not aggregate status)
- Implement manual review endpoint with actual review invocation
- Match API payloads to spec (reviewer/targets/context format)

**6. Enforce Security Sandbox**
- Apply `SafetyEnforcer` around Claude worker subprocess
- Implement command filtering before execution
- Add directory restriction validation
- Monitor resource usage (CPU/memory)

### Phase 2: Complete Dashboard Implementation (HIGH PRIORITY)

Wait for Gemini's `DASHBOARD_DESIGN.md`, then implement:

**Create `orchestrator/static/dashboard.html`** (complete single-file app)
- Real-time SSE connection to `/api/{session_id}/events/stream`
- Agent status cards (Gemini, Codex, Claude) with live progress bars
- Event log panel (auto-scroll, filter by agent/type)
- Review results display section
- Orchestrator decisions panel
- Control buttons (pause/resume/stop/trigger review)
- Session selector dropdown
- Reconnection logic on SSE disconnect
- Proper error handling and loading states
- Responsive CSS layout

### Phase 3: Slash Commands Implementation

Wait for Gemini's `SLASH_COMMANDS_SPEC.md`, then create:

**Create `.claude/commands/` directory with:**
- `orchestrate.md` - Main orchestration command
- `orch-resume.md` - Resume session
- `orch-status.md` - Status check
- `orch-review.md` - Manual review trigger
- `orch-pause.md` - Pause orchestration
- `orch-stop.md` - Stop orchestration

Each command should be a markdown file that expands to a prompt for Claude Code CLI.

### Phase 4: Entry Point & Documentation

**Create `orchestrate` executable script**
- Parse CLI arguments (prompt, --resume, --session-id)
- Initialize session directory
- Launch FastAPI server in background
- Start coordinator with proper paths
- Display dashboard URL
- Stream orchestration progress
- Handle graceful shutdown

**Create/Update Documentation**
- `README.md` - User guide with examples
- `IMPLEMENTATION_GUIDE.md` - Developer documentation
- `TROUBLESHOOTING.md` - Common issues and solutions
- `requirements.txt` - All Python dependencies

### Phase 5: Integration & Testing

**Integration tasks:**
- Ensure all modules work together
- Test all three agents launch correctly
- Verify permission recovery works
- Test peer review flow end-to-end
- Validate dashboard receives SSE updates
- Test slash commands

**Create basic smoke tests:**
- `tests/test_workers.py` - Worker command building
- `tests/test_recovery.py` - Recovery pattern matching
- `tests/test_review.py` - Decision tree logic

## Deliverables

In `/Users/ivg/orchestrator/`:
1. Fixed Python modules (workers.py, recovery.py, coordinator.py, review_engine.py, server.py)
2. Complete dashboard (static/dashboard.html)
3. Slash commands (.claude/commands/*.md)
4. Entry point script (orchestrate)
5. Documentation (README.md, etc.)
6. Basic tests (tests/*.py)

In workspace:
- `IMPLEMENTATION_LOG.md` - What you fixed and implemented

## Success Criteria
- All Codex blockers resolved
- Dashboard fully functional with live updates
- All slash commands working
- Entry point script executable and tested
- Documentation complete
- No syntax errors, all imports working
