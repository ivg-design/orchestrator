# Dashboard Design

## Visual Philosophy
- **Theme**: Dark Mode (High contrast terminal-like aesthetic).
- **Layout**: Dense, information-rich, single-view.
- **Responsiveness**: Desktop-first, functional on tablet.

## Component Hierarchy

```
+---------------------------------------------------------------+
| HEADER: Session ID | Status (Running) | Time Elapsed: 00:12:30|
| [Pause] [Resume] [Stop] [Trigger Review]                      |
+---------------------------------------------------------------+
|                                                               |
|  +-------------------+  +-------------------+  +-----------+  |
|  | GEMINI (Arch)     |  | CLAUDE (Impl)     |  | CODEX     |  |
|  | Status: Thinking  |  | Status: Writing   |  | Status:   |  |
|  | Progress: [====-] |  | Progress: [==---] |  | Idle      |  |
|  | Last: "Spec v1"   |  | Last: "test.py"   |  |           |  |
|  +-------------------+  +-------------------+  +-----------+  |
|                                                               |
+---------------------------------------------------------------+
| EVENTS LOG (Scrollable)                                       |
| [10:01:05] [SYS] Proactive permissions set for /target        |
| [10:01:06] [GEM] Started analysis...                          |
| [10:01:10] [REC] RECOVERY: Fixed Gemini Dir Scope -> Success  |
| [10:05:00] [REV] Review Triggered (Milestone)                 |
+---------------------------------------------------------------+
| REVIEW PANEL (Conditional)                                    |
| +-----------------------------------------------------------+ |
| | Reviewer: Codex | Verdict: APPROVED                       | |
| | Summary: "Logic is sound, tests passed."                  | |
| +-----------------------------------------------------------+ |
+---------------------------------------------------------------+
```

## Functional Requirements

### 1. Agent Cards
- **Avatar/Icon**: Visual distinction.
- **Status Badge**: `IDLE` (Grey), `WORKING` (Blue), `ERROR` (Red), `RECOVERING` (Yellow).
- **Progress Bar**: Based on `progress` payload in events.
- **Latest Action**: Truncated text of last event.

### 2. Events Log
- **Auto-scroll**: Sticks to bottom unless user scrolls up.
- **Color Coding**:
  - `[SYS]` / `[REC]` (Recovery): Cyan
  - `[GEM]`: Purple
  - `[CLD]`: Orange
  - `[CDX]`: Green
  - `[ERR]` / `[BLK]`: Red

### 3. Control Panel
- **Pause**: Sends `/pause` API call. Visual feedback immediately.
- **Review**: Sends `/review` API call.
- **Session Selector**: Dropdown to switch `session_id`.

### 4. Connectivity
- **SSE Client**: Reconnects automatically on disconnect (exponential backoff).
- **State Hydration**: On load, fetch `/state` to populate, then listen to `/events`.

## Error Handling UI
- **Connection Lost**: Overlay banner "Reconnecting...".
- **Escalation Modal**: If Orchestrator enters `ESCALATED` state (e.g., permission failure), show a modal:
  - "Permission Error on Codex"
  - "Action Failed: chmod 755"
  - Options: [Retry] [Manual Fix Confirmed] [Abort]
