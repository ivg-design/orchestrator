# META-ORCHESTRATION ARCHITECTURE - FINAL APPROVED DESIGN
**Unanimous approval: Gemini ✅ | Codex ✅ | Claude ✅**

---

## OVERVIEW

Main Claude (running in Claude Code) orchestrates 3 worker agents via `/orchestrate` slash command:
- **Gemini**: Architecture & design expert (HEAVY LOAD - largest context, best for complex analysis)
- **Codex**: Problem solver & reviewer (MINIMAL LOAD - smallest context, limited availability)
- **Claude Worker**: Code writer & implementation (HEAVY LOAD - handles complex coding tasks)

**Workload Strategy**: Minimize Codex usage due to small context window and limited availability. Heavy lifting distributed between Gemini (architecture/design) and Claude (implementation).

All workers output JSON streams. Event-driven peer reviews ensure quality. Orchestrator monitors, coordinates, and synthesizes results.

---

## WORKER LAUNCH COMMANDS (With Full Permissions)

### Critical: All workers MUST have explicit directory permissions

```bash
# 1. Gemini Worker
gemini \
  --yolo \
  --include-directories /path/to/workspace \
  --include-directories /path/to/target/project \
  --output-format json \
  "task prompt" > workspace/gemini.jsonl

# 2. Codex Worker
codex exec \
  --json \
  --dangerously-bypass-approvals-and-sandbox \
  -C /path/to/target/project \
  "task prompt" > workspace/codex.jsonl

# 3. Claude Worker
claude \
  --print \
  --dangerously-skip-permissions \
  --strict-mcp-config \
  --add-dir /path/to/workspace \
  --add-dir /path/to/target/project \
  --output-format json \
  "task prompt" > workspace/claude.jsonl
```

**Key Requirements**:
- Gemini: MUST include both workspace AND target directories via `--include-directories`
- Codex: MUST set working directory via `-C` flag
- Claude: **CRITICAL** - Must use `--print` for non-interactive mode, `--add-dir` for both workspace AND target directories, `--output-format json` for structured output
- All three agents MUST have explicit access to both workspace and target folders
- All output to JSON/JSONL streams for consistent parsing

---

## PERMISSION RECOVERY SYSTEM (NEW)

### Orchestrator Auto-Recovery

**Problem**: Workers may fail due to permission errors, missing directories, or authentication issues.

**Solution**: Orchestrator actively monitors and fixes permission issues in real-time.

```python
class PermissionRecoveryEngine:
    """
    Monitors worker output streams and automatically fixes permission issues
    """

    def monitor_and_recover(self, worker_name, stream):
        """
        Parse worker output for error patterns and auto-fix
        """
        error_patterns = {
            "gemini": [
                r"Path must be within one of the workspace directories",
                r"Permission denied",
                r"Authentication required"
            ],
            "codex": [
                r"Not inside a trusted directory",
                r"Permission denied",
                r"Repository check failed"
            ],
            "claude": [
                r"Permission denied",
                r"Access blocked"
            ]
        }

        for line in stream:
            event = json.loads(line)

            # Check for error events
            if event["type"] == "error":
                error_text = event["payload"]["text"]

                # Gemini permission error
                if "workspace directories" in error_text:
                    self.fix_gemini_permissions(worker_name)

                # Codex git repository error
                elif "trusted directory" in error_text:
                    self.fix_codex_permissions(worker_name)

                # Generic permission error
                elif "Permission denied" in error_text:
                    self.escalate_permission_issue(worker_name, error_text)

    def fix_gemini_permissions(self, worker_name):
        """
        Relaunch Gemini with corrected --include-directories flags
        """
        # Stop current worker
        self.stop_worker(worker_name)

        # Extract original task from worker state
        task = self.get_worker_task(worker_name)

        # Relaunch with ALL required directories
        required_dirs = [
            self.workspace_dir,
            self.target_project_dir,
            self.orchestrator_dir
        ]

        cmd = [
            "gemini",
            "--yolo",
            "--output-format", "json"
        ]

        # Add ALL directory permissions
        for dir_path in required_dirs:
            cmd.extend(["--include-directories", str(dir_path)])

        cmd.append(task)

        # Relaunch worker
        self.launch_worker(worker_name, cmd)

        # Log recovery
        self.log_event({
            "type": "recovery",
            "worker": worker_name,
            "issue": "gemini_permissions",
            "action": "relaunched_with_directories",
            "directories": required_dirs
        })

    def fix_codex_permissions(self, worker_name):
        """
        Relaunch Codex with --skip-git-repo-check flag
        """
        self.stop_worker(worker_name)
        task = self.get_worker_task(worker_name)

        cmd = [
            "codex", "exec",
            "--json",
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C", str(self.target_project_dir),
            task
        ]

        self.launch_worker(worker_name, cmd)

        self.log_event({
            "type": "recovery",
            "worker": worker_name,
            "issue": "codex_git_check",
            "action": "relaunched_with_skip_flag"
        })

    def escalate_permission_issue(self, worker_name, error_text):
        """
        If auto-fix not possible, escalate to user
        """
        self.pause_orchestration()

        self.notify_user({
            "type": "permission_blocker",
            "worker": worker_name,
            "error": error_text,
            "action_required": "Manual intervention needed",
            "suggestions": [
                "Check file permissions on target directories",
                "Verify agent authentication status",
                "Review security settings"
            ]
        })
```

### Proactive Permission Setup

**Before launching any worker**, orchestrator validates and prepares permissions:

```python
def prepare_worker_environment(worker_name, target_project):
    """
    Ensure all permissions are set BEFORE launching worker
    """
    # 1. Validate directories exist
    required_dirs = [
        workspace_dir,
        target_project_dir,
        orchestrator_dir
    ]

    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    # 2. Check read/write permissions
    for dir_path in required_dirs:
        if not os.access(dir_path, os.R_OK | os.W_OK):
            # Attempt to fix
            try:
                os.chmod(dir_path, 0o755)
            except PermissionError:
                raise PermissionError(
                    f"Cannot access {dir_path}. Manual fix required."
                )

    # 3. Worker-specific setup
    if worker_name == "gemini":
        # Gemini needs explicit directory list
        return {
            "include_directories": required_dirs
        }
    elif worker_name == "codex":
        # Codex needs working directory
        return {
            "working_directory": target_project_dir,
            "flags": ["--skip-git-repo-check"]
        }
    elif worker_name == "claude":
        # Claude needs sandbox restrictions
        return {
            "sandbox": {
                "allowed_dirs": required_dirs,
                "blocked_commands": ["rm -rf", "dd", "mkfs"]
            }
        }
```

**Recovery Strategy Summary**:
1. ✅ **Proactive**: Validate permissions BEFORE launch
2. ✅ **Reactive**: Monitor streams for permission errors
3. ✅ **Auto-fix**: Relaunch workers with corrected flags
4. ✅ **Escalation**: Notify user if auto-fix impossible
5. ✅ **Logging**: Track all recovery actions for debugging

---

## ARCHITECTURE

### Main Claude (Orchestrator)
- Analyzes user task
- Breaks down into 3 specialized sub-tasks
- Launches workers with correct permissions
- Monitors JSON event streams
- Triggers event-based peer reviews
- Makes coordination decisions via policy engine
- Handles permission recovery automatically
- Synthesizes final results

### Worker Agents

**1. Gemini (Architecture & Designer) - HEAVY LOAD**
- Explores and analyzes entire codebase structure
- Designs comprehensive system architecture
- Creates detailed technical specifications
- Identifies patterns, anti-patterns, and optimization opportunities
- Performs complex code analysis and refactoring suggestions
- Outputs: Architecture diagrams, design documents, technical specifications
- **Context advantage**: Largest context window, best for comprehensive analysis

**2. Codex (Problem Solver & Reviewer) - MINIMAL LOAD**
- Reviews work from Gemini and Claude for quality issues
- Solves specific, well-defined problems
- Provides focused feedback and recommendations
- Validates integration points between components
- Outputs: Brief review reports, problem solutions, validation checks
- **Constraints**: Smallest context window, limited availability - use sparingly

**3. Claude Worker (Code Writer & Implementation) - HEAVY LOAD**
- Implements code based on Gemini's architecture
- Writes comprehensive test suites
- Handles complex file operations and refactoring
- Performs integration work between components
- Executes build and test commands
- Outputs: Code implementations, test files, integration reports
- **Context advantage**: Large context window, good for sustained coding work

---

## TASK BREAKDOWN STRATEGY

### Workload Distribution Principles

**PRIMARY GOAL**: Minimize Codex usage while maximizing Gemini and Claude Worker utilization.

```python
def decompose_task(user_prompt):
    """
    Break down user task into 3 agent assignments based on capabilities
    """

    # 1. GEMINI TASK (60-70% of cognitive load)
    gemini_task = {
        "agent": "gemini",
        "role": "architect_designer",
        "responsibilities": [
            "Analyze entire codebase structure and dependencies",
            "Design comprehensive architecture and system changes",
            "Create detailed technical specifications",
            "Identify all affected components and integration points",
            "Suggest optimization opportunities and refactoring needs",
            "Document design decisions and rationale"
        ],
        "deliverables": [
            "Architecture design document",
            "Component interaction diagrams",
            "Technical specification for implementation",
            "List of files to be created/modified",
            "API contracts and interfaces"
        ],
        "complexity": "HIGH",
        "estimated_tokens": "8000-10000"
    }

    # 2. CLAUDE TASK (60-70% of cognitive load)
    claude_task = {
        "agent": "claude",
        "role": "code_writer_implementer",
        "responsibilities": [
            "Implement code based on Gemini's architecture",
            "Write all production code and test suites",
            "Perform file operations (create, modify, delete)",
            "Integrate components according to spec",
            "Execute build, test, and validation commands",
            "Handle complex refactoring tasks"
        ],
        "deliverables": [
            "Production code implementations",
            "Comprehensive test suites",
            "Integration code",
            "Build and test results",
            "Refactored code (if needed)"
        ],
        "complexity": "HIGH",
        "estimated_tokens": "8000-10000"
    }

    # 3. CODEX TASK (10-20% of cognitive load) - MINIMAL
    codex_task = {
        "agent": "codex",
        "role": "problem_solver_reviewer",
        "responsibilities": [
            "Review Gemini's architecture for potential issues",
            "Review Claude's implementation for bugs and quality",
            "Validate integration points are correct",
            "Solve specific, well-defined technical problems",
            "Provide focused feedback and recommendations"
        ],
        "deliverables": [
            "Brief review reports (200 words max)",
            "Specific problem solutions",
            "Validation results",
            "Integration checks"
        ],
        "complexity": "LOW",
        "estimated_tokens": "2000-3000"
    }

    return {
        "gemini": gemini_task,
        "claude": claude_task,
        "codex": codex_task
    }
```

### Example Task Breakdown

**User Request**: "Add user authentication system to the application"

```python
breakdown = {
    "gemini": """
    TASK: Design user authentication system architecture

    1. Analyze current application structure and identify integration points
    2. Design authentication flow (registration, login, logout, password reset)
    3. Specify database schema for user accounts
    4. Design API endpoints and contracts
    5. Identify security requirements (hashing, tokens, sessions)
    6. Document all components that need modification
    7. Create technical specification for implementation

    DELIVERABLES:
    - Authentication architecture document
    - Database schema design
    - API endpoint specifications
    - Security requirements document
    - List of files to create/modify
    """,

    "claude": """
    TASK: Implement user authentication system

    Based on Gemini's architecture specification:
    1. Create user model and database migrations
    2. Implement authentication API endpoints
    3. Write password hashing and token generation logic
    4. Create middleware for protected routes
    5. Implement frontend login/registration forms
    6. Write comprehensive test suite
    7. Integrate with existing application

    DELIVERABLES:
    - User model and migrations
    - Authentication API implementation
    - Frontend components
    - Test suite (unit + integration)
    - Integration code
    """,

    "codex": """
    TASK: Review authentication system implementation

    1. Review Gemini's architecture for security vulnerabilities
    2. Review Claude's code for common auth bugs:
       - SQL injection risks
       - Password storage issues
       - Token validation problems
       - Session management issues
    3. Validate API contracts match specification
    4. Check integration points are correct

    DELIVERABLES:
    - Brief security review (200 words)
    - List of issues found (if any)
    - Validation results
    """
}
```

### Workload Metrics

Target distribution:
- **Gemini**: 40-50% of total work (architecture, design, analysis)
- **Claude**: 40-50% of total work (implementation, testing, integration)
- **Codex**: 10-20% of total work (review, validation, focused problem-solving)

---

## PEER REVIEW SYSTEM

### Event-Based Triggers (NOT time-based)

**Review triggered by**:
1. Worker emits `[MILESTONE]` event
2. Worker emits `[BLOCKER]` event
3. Worker emits `[REQUEST_REVIEW]` event
4. User clicks "Review Now" in dashboard
5. **Fallback**: No events for 15 minutes

**NO rigid 5-minute intervals** - prevents context disruption.

### Review Protocol

```python
# Orchestrator requests review
{
  "type": "review_request",
  "reviewer": "gemini",
  "targets": ["codex", "claude"],
  "focus": "Check for conflicts, gaps, quality issues",
  "context": {
    "codex_summary": "Implemented authentication module...",
    "claude_summary": "Integration tests passing..."
  },
  "max_words": 200
}

# Worker responds
{
  "type": "peer_review",
  "reviewer": "gemini",
  "target": "codex",
  "verdict": "approved|concerns|blocker",
  "issues": ["Minor: Consider edge case X"],
  "recommendations": ["Suggest adding test for Y"]
}
```

**Brief reviews** (200 words max) minimize overhead.

---

## DECISION POLICY

### Orchestrator Decision Tree

```python
def evaluate_peer_reviews(reviews):
    blockers = [r for r in reviews if r["verdict"] == "blocker"]
    concerns = [r for r in reviews if r["verdict"] == "concerns"]
    approved = [r for r in reviews if r["verdict"] == "approved"]

    # RULE 1: Any blocker → STOP
    if len(blockers) > 0:
        return {
            "action": "STOP_AND_ESCALATE",
            "reason": f"{len(blockers)} blocker(s) detected",
            "next": "Present issue to user, await decision"
        }

    # RULE 2: Majority concerns (2+) → PAUSE
    if len(concerns) >= 2:
        return {
            "action": "PAUSE_AND_CLARIFY",
            "reason": "Majority have concerns",
            "next": "Orchestrator clarifies requirements, agents resume"
        }

    # RULE 3: Single concern → LOG_WARNING
    if len(concerns) == 1:
        return {
            "action": "LOG_WARNING",
            "reason": "One agent has concerns",
            "next": "Continue but monitor closely, review again in 10 min"
        }

    # RULE 4: All approved → CONTINUE
    if len(approved) == len(reviews):
        return {
            "action": "CONTINUE",
            "reason": "All reviews positive",
            "next": "Continue work, next review on event trigger"
        }
```

**Deterministic decision making** - no ambiguity.

---

## SECURITY & SAFETY

### Claude Worker Sandbox

**Problem**: `--dangerously-skip-permissions` is risky

**Solution**: Restricted sandbox with command filtering

```python
claude_worker = launch_agent(
    "claude",
    command=[
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--strict-mcp-config",  # Disable MCPs from user config
        "--add-dir", workspace_dir,
        "--add-dir", target_project_dir,
        "--output-format", "json"
    ],
    sandbox={
        "allowed_dirs": [workspace_dir, target_project_dir],
        "blocked_commands": [
            "rm -rf",
            "dd",
            "mkfs",
            "format",
            "fdisk"
        ],
        "require_confirm": [
            "git push",
            "npm publish",
            "pip install",
            "cargo publish"
        ],
        "monitor_patterns": [
            r"sudo\s+",
            r"curl.*\|\s*sh",
            r"wget.*\|\s*sh"
        ]
    }
)
```

**Safety measures**:
1. ✅ Monitor stdout for dangerous patterns
2. ✅ Require confirmation for high-risk commands
3. ✅ Limit file system access to workspace + target
4. ✅ Log all commands executed
5. ✅ Auto-kill on suspicious activity

---

## FALLBACK STRATEGY

### 4-Tier Graceful Degradation (Prioritizing Heavy Workers)

**Priority Order**: Gemini > Claude Worker > Codex

```python
def launch_workers_with_fallback(task_breakdown):
    # Tier 1: Full 3-agent setup (IDEAL)
    try:
        gemini = launch_gemini(task_breakdown["gemini"])
        claude = launch_claude_worker(task_breakdown["claude"])
        codex = launch_codex(task_breakdown["codex"])
        return [gemini, claude, codex]

    except CodexUnavailableError:
        # Tier 2: 2-agent mode WITHOUT Codex (PREFERRED FALLBACK)
        # This is actually acceptable since Codex has minimal load
        gemini = launch_gemini(task_breakdown["gemini"])
        claude = launch_claude_worker(task_breakdown["claude"])

        # Orchestrator handles review tasks that Codex would do
        orchestrator_performs_reviews()

        return [gemini, claude]

    except ClaudeUnavailableError:
        # Tier 3: 2-agent mode (Gemini + Codex)
        # Gemini does architecture, Codex does minimal implementation
        gemini = launch_gemini(task_breakdown["gemini"])
        codex = launch_codex(task_breakdown["codex"])

        # Orchestrator handles implementation tasks
        orchestrator_handles_implementation()

        return [gemini, codex]

    except GeminiUnavailableError:
        # Tier 4: 2-agent mode (Claude + Codex)
        # Claude does both architecture and implementation
        # Codex does review
        claude = launch_claude_worker(task_breakdown["claude"])
        codex = launch_codex(task_breakdown["codex"])

        # Orchestrator handles architecture analysis
        orchestrator_handles_architecture()

        return [claude, codex]

    except AllAgentsUnavailableError:
        # Tier 5: Solo mode (Main Claude does everything)
        orchestrator_executes_task_solo()
        return []
```

**Fallback Priorities**:
1. **IDEAL**: Gemini + Claude + Codex (full team)
2. **ACCEPTABLE**: Gemini + Claude (Codex optional for reviews)
3. **DEGRADED**: Gemini + Codex (Claude implementation handled by orchestrator)
4. **DEGRADED**: Claude + Codex (Gemini architecture handled by orchestrator)
5. **FALLBACK**: Solo orchestrator mode

**Note**: Losing Codex has minimal impact since its role is primarily review/validation, which the orchestrator can handle.

---

## PERFORMANCE OPTIMIZATION

### Token Management
- **Bounded output**: Workers limited to 10K tokens per task
- **Lazy reviews**: Only trigger on events (not time-based)
- **Summary mode**: Reviews use summaries, not full output
- **Deduplication**: Don't re-send common context

### Resource Limits
```python
worker_limits = {
    "cpu_percent": 50,      # Max 50% CPU per worker
    "memory_mb": 2048,      # Max 2GB RAM per worker
    "max_runtime": 3600     # Kill if running >1 hour
}
```

---

## UNIFIED OUTPUT PROTOCOL

### JSON Event Format

```json
{
  "type": "status|progress|finding|task|blocker|milestone|review",
  "agent": "gemini|codex|claude",
  "timestamp": "2025-11-21T17:00:00Z",
  "payload": {
    "text": "...",
    "progress": 45,
    "file": "/path/to/file"
  }
}
```

**Event Types**:
- `status`: Agent state change
- `progress`: Percent complete (0-100)
- `finding`: Discovery/result
- `task`: New sub-task started
- `blocker`: Blocked, needs help
- `milestone`: Major phase complete
- `review`: Peer review response
- `error`: Error occurred (triggers recovery)

---

## DEFINITION OF DONE

**Task is complete when**:
1. ✅ All workers report `{"type": "milestone", "payload": {"text": "Complete"}}`
2. ✅ Final peer review: All approve
3. ✅ Orchestrator validates output files exist
4. ✅ Integration check passes
5. ✅ No outstanding blockers
6. ✅ No unresolved permission errors

**Prevents infinite refinement loops.**

---

## FILE STRUCTURE

```
~/orchestrator/
├── orchestrate                     # Slash command entry point
├── orchestrator/
│   ├── cli.py                      # Task analysis & breakdown
│   ├── server.py                   # FastAPI backend
│   ├── coordinator.py              # Orchestrator logic
│   ├── review_engine.py            # Peer review system
│   ├── workers.py                  # Agent launchers
│   ├── safety.py                   # Sandbox & security
│   └── recovery.py                 # Permission recovery engine (NEW)
├── static/
│   └── dashboard.html              # Real-time UI with review panel
└── workspace/
    └── {session_id}/
        ├── gemini.jsonl            # Gemini output stream
        ├── codex.jsonl             # Codex output stream
        ├── claude.jsonl            # Claude worker output
        └── reviews/                # Peer review artifacts
            ├── review_001.json
            └── review_002.json
```

---

## SLASH COMMAND WORKFLOW

**File**: `.claude/commands/orchestrate.md`

```bash
#!/bin/bash
# /orchestrate command handler

PROMPT="$1"

# 1. Analyze task
analyze_task "$PROMPT"

# 2. Break down into 3 parts
breakdown=$(decompose_task "$PROMPT")

# 3. Prepare permissions proactively
prepare_all_worker_environments

# 4. Start dashboard & backend
start_dashboard_with_recovery_panel

# 5. Launch workers with fallback
launch_workers_with_fallback "$breakdown"

# 6. Monitor & coordinate with auto-recovery
while not_complete; do
    check_for_events
    check_for_permission_errors        # NEW
    auto_recover_failed_workers        # NEW
    trigger_reviews_if_needed
    make_decisions_based_on_reviews
done

# 7. Synthesize results
synthesize_and_present
```

---

## KEY FEATURES

✅ **Event-driven reviews** (not rigid intervals)
✅ **All workers use JSON streaming output**
✅ **Automatic permission recovery** (NEW)
✅ **Proactive permission setup** (NEW)
✅ **4-tier fallback strategy**
✅ **Safety sandbox for Claude worker**
✅ **Clear decision policy** (4 rules)
✅ **Performance limits** (CPU, memory, tokens)
✅ **Definition of done** (prevents infinite loops)
✅ **Minimal infrastructure** (no scope creep)
✅ **Real-time dashboard** with recovery status

---

## IMPLEMENTATION READINESS

**Status**: ✅ **APPROVED BY ALL THREE AGENTS**

- Gemini: ✅ Approved
- Codex: ✅ Approved
- Claude: ✅ Approved

**Next Steps**:
1. Validate CLI flags via agent-specific research
2. Validate tech stack choices
3. Begin implementation of core components

---

## CRITICAL REQUIREMENTS CHECKLIST

- [x] All workers output JSON streams
- [x] Gemini gets `--include-directories` for workspace AND target
- [x] Codex gets working directory via `-C` flag
- [x] Claude worker uses `--output-format json`
- [x] Event-based peer reviews (not time-based)
- [x] Orchestrator has permission recovery system
- [x] Fallback strategy for missing agents
- [x] Safety sandbox for dangerous commands
- [x] Clear decision tree with 4 rules
- [x] Definition of done to prevent infinite loops
- [x] Performance limits (CPU, memory, tokens)
- [x] Auto-starting dashboard with real-time updates

---

**This is the final approved architecture. Ready for validation and implementation.**
