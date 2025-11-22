# CODEX TASK: Review Meta-Orchestration System

## Your Role
You are the **Problem Solver & Reviewer**. Review the architecture and implementation for quality issues.

## Context
- Architecture design: `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`
- Workspace: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/`
- Implementation: `/Users/ivg/orchestrator/`

## Your Task

### Phase 1: Review Gemini's Architecture (Wait for Gemini to complete first)

Review files:
- `ARCHITECTURE_SPEC.md`
- `DATA_MODELS.md`
- `API_SPEC.md`
- `FLOW_DIAGRAM.md`

Check for:
- Missing components from FINAL_ARCHITECTURE.md
- Incomplete specifications
- Potential design issues
- Integration gaps between modules

### Phase 2: Review Claude's Implementation (Wait for Claude to complete first)

Review all Python files in `/Users/ivg/orchestrator/orchestrator/`:

**Critical Checks**:
1. **CLI Flags Correctness**:
   - Gemini: `--yolo --include-directories <workspace> --include-directories <target> --output-format json`
   - Codex: `exec --json --dangerously-bypass-approvals-and-sandbox -C <target>`
   - Claude: `--print --dangerously-skip-permissions --strict-mcp-config --add-dir <workspace> --add-dir <target> --output-format json`

2. **Permission Handling**:
   - All three agents have explicit directory access
   - Recovery.py properly detects permission errors
   - Fallback mechanisms implemented

3. **Event Stream Parsing**:
   - Correct JSONL parsing
   - All event types handled
   - Error handling for malformed JSON

4. **Review Engine**:
   - Event-based triggers implemented
   - Review request format correct
   - Decision tree matches specification

5. **Integration Issues**:
   - Server endpoints match frontend expectations
   - SSE streaming works correctly
   - Agent processes properly managed

### Deliverables

Create review reports in workspace:

**ARCHITECTURE_REVIEW.md**:
- Issues found in Gemini's specs
- Recommendations
- Verdict: approved|concerns|blocker

**IMPLEMENTATION_REVIEW.md**:
- Code issues found
- Security concerns
- Integration problems
- Verdict: approved|concerns|blocker

Keep reviews focused and concise (200-300 words each).
