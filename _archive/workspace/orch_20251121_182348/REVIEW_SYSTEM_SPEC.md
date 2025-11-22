# Review System Specification

## Overview
The Review System coordinates peer reviews between agents. It is **event-driven**, avoiding rigid time intervals in favor of milestone-based or necessity-based checks.

## 1. Review Triggers

A review cycle is initiated by any of the following events:

1.  **MILESTONE**: Agent emits `{ "type": "milestone", ... }` (Major task complete).
2.  **BLOCKER**: Agent emits `{ "type": "blocker", ... }` (Stuck/Confused).
3.  **REQUEST_REVIEW**: Agent emits `{ "type": "request_review", ... }` (Explicitly asks for feedback).
4.  **USER_MANUAL**: User clicks "Trigger Review" or runs `/review`.
5.  **TIMEOUT_FALLBACK**: No events received from any agent for **15 minutes**. (Safety net for silent failures).

## 2. Review Request Schema

When triggered, the Orchestrator sends this payload to the **Reviewer** (usually Gemini or Codex):

```json
{
  "type": "review_request",
  "reviewer": "codex",
  "targets": ["claude", "gemini"],
  "context": {
    "claude_summary": "Implemented auth_controller.py with JWT support.",
    "gemini_summary": "Provided updated schema for users table."
  },
  "focus_areas": [
    "Security vulnerabilities",
    "Spec compliance",
    "Integration correctness"
  ],
  "max_words": 200
}
```

## 3. Review Response Schema

The Reviewer analyzes the work and responds with:

```json
{
  "type": "review_result",
  "reviewer": "codex",
  "timestamp": "...",
  "payload": {
    "verdict": "approved | concerns | blocker",
    "summary": "Auth logic looks solid, but missing salt in hash.",
    "issues": [
      {
        "severity": "high",
        "description": "Password hashing is using MD5, must use Argon2.",
        "file": "auth_controller.py"
      }
    ]
  }
}
```

## 4. Decision Logic (The "4 Rules")

The Orchestrator collects reviews and applies this deterministic logic:

| Case | Condition | Action | Status |
|---|---|---|---|
| **Rule 1** | Any `verdict == "blocker"` | **STOP & ESCALATE** | `PAUSED` |
| **Rule 2** | ≥ 2 `verdict == "concerns"` | **PAUSE & CLARIFY** | `PAUSED` |
| **Rule 3** | 1 `verdict == "concerns"` | **LOG & CONTINUE** | `RUNNING` (Flagged) |
| **Rule 4** | All `verdict == "approved"` | **CONTINUE** | `RUNNING` |

**Actions:**
- **STOP & ESCALATE**: Notify user immediately. Wait for manual override.
- **PAUSE & CLARIFY**: Orchestrator generates a clarification prompt to agents to resolve the conflict.
- **LOG & CONTINUE**: Add the concern to the "Issues List" but do not stop work.
- **CONTINUE**: Reset 15-min timer and proceed.
