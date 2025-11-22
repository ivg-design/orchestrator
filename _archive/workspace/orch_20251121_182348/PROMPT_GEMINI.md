# GEMINI TASK: Architecture Refinement & Dashboard Design

## Your Role
You are the **Architect & Designer**. Refine the architecture to address Codex's concerns and design the complete dashboard UI/UX.

## Context
- Previous architecture: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_SPEC.md`
- Codex concerns: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_REVIEW.md`
- Final approved design: `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`
- Target implementation: `/Users/ivg/orchestrator/`
- Workspace: `/Users/ivg/orchestrator/workspace/orch_20251121_182348/`

## Your Tasks

### Phase 1: Address Architecture Concerns (HIGH PRIORITY)

Review Codex's concerns and create updated specifications:

**1. CLI & Permissions Specification** (`CLI_PERMISSIONS_SPEC.md`)
- Document exact CLI command for each agent (Gemini, Codex, Claude)
- Specify all three directory paths: workspace, target, orchestrator
- Define pre-flight permission validation logic
- Include chmod fallback procedures
- Specify sandbox constraints

**2. Recovery Engine Specification** (`RECOVERY_SPEC.md`)
- Document proactive permission setup (before launch)
- Define reactive recovery patterns (regex → action mapping)
- Specify Gemini recovery: add `--include-directories`
- Specify Codex recovery: add `--skip-git-repo-check`
- Define structured recovery event schema
- Document escalation workflow when auto-fix fails
- Include recovery logging format

**3. Review System Specification** (`REVIEW_SYSTEM_SPEC.md`)
- Define all review triggers:
  - MILESTONE events
  - BLOCKER events
  - REQUEST_REVIEW events
  - User manual trigger
  - 15-minute no-event fallback
- Specify review request format (reviewer, targets[], context, max_words)
- Document 4-rule decision tree in detail
- Define review response schema

**4. API & SSE Specification** (`API_SSE_SPEC.md`)
- Convert all endpoints to session-scoped paths: `/api/{session_id}/...`
- Define complete SSE event envelope schema
- Specify typed event formats for each `AgentEvent` type
- Document recovery/decision update events
- Include request/response examples for all endpoints

**5. Complete Flow Diagram** (`COMPLETE_FLOW.md`)
- Add recovery branch to main flow
- Include sandbox validation steps
- Show permission failure → proactive fix → relaunch path
- Document decision tree flow (review → verdict → action)
- Include all edge cases and error paths

### Phase 2: Dashboard Design (HIGH PRIORITY)

Create complete UI/UX specifications:

**Dashboard Design Document** (`DASHBOARD_DESIGN.md`)
- Component hierarchy and layout
- Real-time features:
  - Live agent status cards (Gemini, Codex, Claude)
  - Progress bars with percentage
  - Event stream panel (auto-scroll, filterable)
  - Review results display
  - Orchestrator decisions panel
- Control panel:
  - Pause/Resume/Stop buttons
  - Manual review trigger
  - Session selector
- Color scheme and visual design
- Responsive layout specifications
- SSE connection management
- Error handling and reconnection logic

### Phase 3: Slash Command Design

**Slash Command Specification** (`SLASH_COMMANDS_SPEC.md`)
- `/orchestrate <prompt>` - Start new orchestration
- `/resume <session_id>` - Resume existing session
- `/status` - Show current orchestration status
- `/review` - Trigger manual peer review
- `/pause` - Pause orchestration
- `/stop` - Stop orchestration
- Document command syntax, arguments, output format

## Deliverables

Create in workspace:
1. `CLI_PERMISSIONS_SPEC.md`
2. `RECOVERY_SPEC.md`
3. `REVIEW_SYSTEM_SPEC.md`
4. `API_SSE_SPEC.md`
5. `COMPLETE_FLOW.md`
6. `DASHBOARD_DESIGN.md`
7. `SLASH_COMMANDS_SPEC.md`

Each spec should be detailed, actionable, and directly address Codex's concerns. Include code examples, JSON schemas, and command-line examples where appropriate.

## Success Criteria
- All Codex architecture concerns addressed
- Specifications are implementation-ready (no ambiguity)
- Dashboard design is complete and feasible
- All specs align with FINAL_ARCHITECTURE.md
