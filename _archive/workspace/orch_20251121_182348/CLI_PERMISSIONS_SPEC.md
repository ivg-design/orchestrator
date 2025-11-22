# CLI & Permissions Specification

## Overview
This document defines the exact CLI commands, permission requirements, and sandbox constraints for the three worker agents (Gemini, Codex, Claude). Strict adherence to these specifications is required to ensure system stability and security.

## Directory Definitions

All agents operate within three distinct directory contexts:

1.  **Workspace Directory** (`workspace_dir`):
    - Path: `~/orchestrator/workspace/{session_id}/
    - Purpose: Stores agent logs, intermediate outputs, and review artifacts.
    - Access: Read/Write.

2.  **Target Directory** (`target_dir`):
    - Path: Defined by user (e.g., `~/github/my-project`)
    - Purpose: The codebase being modified or analyzed.
    - Access: Read/Write.

3.  **Orchestrator Directory** (`orchestrator_dir`):
    - Path: `~/orchestrator/
    - Purpose: Source code of the orchestration tool itself.
    - Access: Read-Only (generally), Read/Write (if self-modifying).

## Pre-Flight Validation & Setup

**Before** launching any worker, the Orchestrator MUST execute the following `prepare_worker_environment` routine:

1.  **Existence Check**: Verify `workspace_dir`, `target_dir`, and `orchestrator_dir` exist. If not, create `workspace_dir`. Fail if `target_dir` is missing.
2.  **Permission Check**: Verify R/W access to `workspace_dir` and `target_dir`.
3.  **Chmod Fallback**:
    - If access is denied, attempt: `chmod -R 755 {dir_path}`
    - If `chmod` fails, raise `PermissionError` (triggers escalation).
4.  **Path Normalization**: Resolve all paths to absolute paths to avoid relative path ambiguity.

## Agent Launch Commands

### 1. Gemini Worker (Architecture & Design)

**Role**: Heavy load, large context analysis.

```bash
gemini \
  --yolo \
  --include-directories "{workspace_dir}" \
  --include-directories "{target_dir}" \
  --include-directories "{orchestrator_dir}" \
  --output-format json \
  "{initial_task_prompt}" > "{workspace_dir}/gemini.jsonl"
```

**Constraints**:
- MUST explicitly include all three directories.
- `--output-format json` is mandatory for parsing.

### 2. Codex Worker (Review & Fix)

**Role**: Minimal load, targeted fixes.

```bash
codex exec \
  --json \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check \
  -C "{target_dir}" \
  "{initial_task_prompt}" > "{workspace_dir}/codex.jsonl"
```

**Constraints**:
- `-C "{target_dir}"` sets the working directory context.
- `--skip-git-repo-check` is CRITICAL to prevent refusals in non-git dirs.
- `--dangerously-bypass-approvals-and-sandbox` allows file edits without interactive prompts (managed by Orchestrator loop).

### 3. Claude Worker (Implementation)

**Role**: Heavy load, coding.

```bash
claude \
  --print \
  --dangerously-skip-permissions \
  --strict-mcp-config \
  --add-dir "{workspace_dir}" \
  --add-dir "{target_dir}" \
  --output-format json \
  "{initial_task_prompt}" > "{workspace_dir}/claude.jsonl"
```

**Constraints**:
- `--print` prevents interactive TUI mode.
- `--add-dir` grants specific directory access.
- `--strict-mcp-config` prevents loading user-global MCPs that might interfere.

## Sandbox Constraints (Claude Only)

While `--dangerously-skip-permissions` is used, the Orchestrator implements a **Logical Sandbox** by filtering commands before execution (if the agent supports a "validate command" step) or by monitoring the output stream for executed commands and killing the process if violations occur.

**Blocked Commands (Regex Match)**:
- `rm -rf /` (Root deletion)
- `mkfs.*` (Filesystem formatting)
- `dd if=.*` (Direct disk write)
- `shutdown`, `reboot`

**Allowed Directories**:
- `{workspace_dir}`
- `{target_dir}`
- `/tmp` (limited)
