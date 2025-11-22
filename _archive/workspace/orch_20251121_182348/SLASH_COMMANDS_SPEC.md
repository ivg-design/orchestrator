# Slash Command Specification

## Overview
The system is controlled primarily through a set of slash commands, accessible via the terminal (CLI wrapper) or the Dashboard input.

## Commands

### 1. `/orchestrate`
**Purpose**: Start a new orchestration session.
**Syntax**: `/orchestrate [options] <prompt>`
**Arguments**:
- `<prompt>`: The natural language task description.
- `--target-dir, -C`: Path to the target project (defaults to current).
- `--resume <id>`: Resume a specific session (alias for `/resume`).

**Example**:
```bash
/orchestrate "Refactor the auth module to use OAuth2" -C ~/projects/myapp
```

### 2. `/resume`
**Purpose**: Resume a paused or stopped session.
**Syntax**: `/resume <session_id>`

### 3. `/status`
**Purpose**: Show high-level status of current/active session.
**Output**:
```
Session: orch_20251121_abc
State: RUNNING
Active Agents: Gemini, Claude
Latest Decision: CONTINUE (All approved)
Failures: 0
```

### 4. `/review`
**Purpose**: Force a manual peer review cycle immediately.
**Syntax**: `/review [focus_area]`
**Arguments**:
- `focus_area` (Optional): Specific instruction for the reviewer (e.g., "Check for memory leaks").

### 5. `/pause`
**Purpose**: Gracefully pause all agents.
**Behavior**: Sends SIGSTOP or internal pause signal. Preserves state.

### 6. `/stop`
**Purpose**: Terminate the session.
**Behavior**: Kills all worker processes, saves final state, closes session.

### 7. `/logs`
**Purpose**: Tail the logs of a specific agent.
**Syntax**: `/logs <agent_name>`
**Example**: `/logs gemini`
