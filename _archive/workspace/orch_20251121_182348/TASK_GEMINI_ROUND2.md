# GEMINI TASK ROUND 2: Implement Missing Components

Codex found dashboard/slash commands are missing/incomplete. CREATE THEM:

## 1. Create Slash Commands (HIGH PRIORITY)
Directory: `/Users/ivg/orchestrator/.claude/commands/`

Create these command files:
- `orchestrate.md` - Start orchestration
- `orch-status.md` - Check status
- `orch-review.md` - Trigger review
- `orch-stop.md` - Stop orchestration

Each is a markdown file with prompt text for Claude Code CLI.

## 2. Fix Dashboard Issues
File: `/Users/ivg/orchestrator/static/dashboard.html`

Codex found: Missing review rendering, reconnection UX, session scoping
FIX: Add these missing features to the existing dashboard

Work fast - write the actual files directly.
