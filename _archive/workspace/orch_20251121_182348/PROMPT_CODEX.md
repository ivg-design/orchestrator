# CODEX TASK: Validate Implementation & Sign Off

## Your Role
You are the **Quality Validator**. Verify all blockers are fixed and validate the complete implementation.

## Context
- Implementation: `/Users/ivg/orchestrator/`
- Your previous blockers: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/IMPLEMENTATION_REVIEW.md`
- Gemini's refined specs: `/Users/ivg/orchestrator/workspace/orch_20251121_182348/`
- Workspace: `/Users/ivg/orchestrator/workspace/orch_20251121_182348/`

## Your Tasks

### Phase 1: Wait for Claude to Complete Fixes

Monitor Claude's progress. Wait until Claude reports completion of blocker fixes.

### Phase 2: Validate Blocker Fixes (CRITICAL)

For each blocker you identified, verify the fix:

**1. Permission Recovery Loop Fix**
- Check `orchestrator/workers.py`: Codex command includes `--skip-git-repo-check`
- Check `orchestrator/recovery.py`: `_fix_codex_permissions()` actually modifies the command
- Test: Simulate permission error and verify recovery adds the flag

**2. Event Detection Fix**
- Check `orchestrator/recovery.py`: Stderr parsing implemented
- Check: Offset tracking prevents duplicate triggers
- Verify: Event parsing includes all error sources

**3. Worker State Updates Fix**
- Check `orchestrator/coordinator.py`: Worker states refreshed from events
- Verify: Progress/status values updated during execution
- Test: SSE stream shows accurate worker progress

**4. Review Engine Implementation**
- Check `orchestrator/review_engine.py`: Full decision tree implemented
- Verify: All 4 rules correctly coded (BLOCKER→STOP, ≥2 CONCERNS→PAUSE, etc.)
- Test: Each decision path with mock review data

**5. API Compliance Fix**
- Check `orchestrator/server.py`: Routes are session-scoped
- Verify: SSE emits typed agent events (not aggregate)
- Check: Review endpoint invokes actual review logic
- Verify: API payloads match specification

**6. Security Sandbox Fix**
- Check: `SafetyEnforcer` applied to Claude worker subprocess
- Verify: Command filtering active
- Check: Directory restrictions enforced

### Phase 3: Validate New Implementations

**Dashboard Validation**
- Review `static/dashboard.html`:
  - SSE connection properly implemented
  - Event handling correct
  - UI elements match Gemini's design
  - Error handling present
  - Reconnection logic works
- Test: Open dashboard, verify live updates

**Slash Commands Validation**
- Check `.claude/commands/*.md` exist
- Verify: Each command has proper prompt
- Test: Execute each command and verify behavior

**Entry Point Validation**
- Check `orchestrate` script:
  - Argument parsing correct
  - Server launches properly
  - Coordinator starts with correct paths
  - Graceful shutdown works
- Test: Run `./orchestrate "test prompt"`

**Integration Validation**
- All modules import without errors
- Three agents can launch successfully
- Permission recovery triggers correctly
- Peer review flow works end-to-end
- Dashboard receives real-time updates

### Phase 4: Final Sign-Off

Create comprehensive review:

**FINAL_VALIDATION_REPORT.md**

Structure:
```markdown
# Final Validation Report

## Blocker Fixes Status
- [ ] Permission recovery loop - RESOLVED/UNRESOLVED
- [ ] Event detection - RESOLVED/UNRESOLVED
- [ ] Worker state updates - RESOLVED/UNRESOLVED
- [ ] Review engine - RESOLVED/UNRESOLVED
- [ ] API compliance - RESOLVED/UNRESOLVED
- [ ] Security sandbox - RESOLVED/UNRESOLVED

## New Implementation Quality
- Dashboard: APPROVED/CONCERNS/BLOCKER
- Slash commands: APPROVED/CONCERNS/BLOCKER
- Entry point: APPROVED/CONCERNS/BLOCKER
- Documentation: APPROVED/CONCERNS/BLOCKER
- Integration: APPROVED/CONCERNS/BLOCKER

## Remaining Issues
[List any remaining concerns or blockers]

## Production Readiness
- [ ] All blockers resolved
- [ ] Core functionality working
- [ ] Dashboard operational
- [ ] Commands functional
- [ ] Documentation complete

## Final Verdict
APPROVED | CONCERNS | BLOCKER

## Recommendation
[Ready for production | Needs minor fixes | Requires significant work]
```

### Phase 5: Edge Case Testing

If verdict is APPROVED, perform additional testing:
- Test with malformed agent output
- Test with permission errors
- Test with missing dependencies
- Test dashboard reconnection after server restart
- Test concurrent session handling

## Deliverables

Create in workspace:
1. `BLOCKER_FIXES_VERIFICATION.md` - Detailed validation of each fix
2. `DASHBOARD_REVIEW.md` - Dashboard code review
3. `SLASH_COMMANDS_REVIEW.md` - Commands validation
4. `INTEGRATION_TEST_RESULTS.md` - End-to-end test results
5. `FINAL_VALIDATION_REPORT.md` - Overall assessment and sign-off

## Success Criteria
- All blockers verified as fixed
- New implementations validated
- Integration tested end-to-end
- Clear verdict (APPROVED/CONCERNS/BLOCKER)
- Production readiness assessment complete
