# Usage Examples

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Basic Usage

Run a simple orchestration task:

```bash
./orchestrate "Add user authentication to my web application"
```

This will:
- Create a new session workspace
- Break down the task into 3 agent assignments
- Launch Gemini (architecture), Codex (review), and Claude (implementation)
- Start the dashboard at http://localhost:8000
- Monitor progress and handle reviews automatically

## Command-Line Options

### Specify Target Project

```bash
./orchestrate "Optimize database queries" --target /path/to/my/project
```

### Custom Workspace Location

```bash
./orchestrate "Add dark mode" --workspace ./my-workspace
```

### Change Dashboard Port

```bash
./orchestrate "Implement caching" --port 9000
```

### Headless Mode (No Dashboard)

```bash
./orchestrate "Fix security vulnerabilities" --no-dashboard
```

### Verbose Logging

```bash
./orchestrate "Refactor authentication module" --verbose
```

## Real-World Examples

### Example 1: Adding a Feature

```bash
./orchestrate "Add a user profile page with avatar upload, bio editing, and activity history"
```

**What happens:**
- **Gemini**: Designs the profile page architecture, database schema, API endpoints
- **Claude**: Implements the UI components, API handlers, database migrations
- **Codex**: Reviews for security issues, validates API design, checks integration

### Example 2: Bug Fix

```bash
./orchestrate "Fix the memory leak in the WebSocket connection handler" --target ./backend
```

**What happens:**
- **Gemini**: Analyzes the WebSocket code, identifies leak patterns, proposes solutions
- **Claude**: Implements the fix, adds proper cleanup, writes tests
- **Codex**: Reviews for edge cases, validates the fix doesn't break existing functionality

### Example 3: Performance Optimization

```bash
./orchestrate "Optimize the search query performance - currently taking 5+ seconds"
```

**What happens:**
- **Gemini**: Analyzes query patterns, suggests indexing strategy, proposes caching
- **Claude**: Implements database indexes, adds caching layer, updates queries
- **Codex**: Reviews optimization strategy, validates performance improvements

### Example 4: Code Refactoring

```bash
./orchestrate "Refactor the payment processing module to follow clean architecture principles"
```

**What happens:**
- **Gemini**: Designs clean architecture layers, defines interfaces and boundaries
- **Claude**: Refactors code to new structure, moves logic to appropriate layers
- **Codex**: Reviews architecture adherence, checks for broken dependencies

### Example 5: Test Coverage

```bash
./orchestrate "Add comprehensive test coverage for the authentication module"
```

**What happens:**
- **Gemini**: Analyzes authentication flows, identifies test scenarios and edge cases
- **Claude**: Writes unit tests, integration tests, and E2E tests
- **Codex**: Reviews test coverage, validates test quality and assertions

## Dashboard Usage

Once the orchestration starts, open your browser to `http://localhost:8000`

### Dashboard Features

1. **Session Information**: View session ID, user prompt, and current status
2. **Worker Status**: Real-time progress for Gemini, Codex, and Claude
3. **Latest Decision**: See orchestrator decisions based on peer reviews
4. **Peer Reviews**: View review results and verdicts
5. **Event Log**: Live stream of events from all workers
6. **Controls**: Manually trigger reviews, pause, resume, or stop orchestration

### Manual Controls

**Trigger Review**: Click to force a peer review cycle
```javascript
// Dashboard will show review results and decision
```

**Pause**: Temporarily pause orchestration
```javascript
// Workers continue current tasks but don't start new ones
```

**Resume**: Resume paused orchestration
```javascript
// Workers continue with pending tasks
```

**Stop**: Stop all workers and end orchestration
```javascript
// Gracefully terminates all workers
```

## Understanding Output

### Session Workspace

After running, check the workspace directory:

```
workspace/orch_20251121_175811/
├── gemini.jsonl          # Gemini's event stream
├── codex.jsonl           # Codex's event stream
├── claude.jsonl          # Claude's event stream
└── reviews/              # Peer review results
    ├── review_001.json
    └── review_002.json
```

### Event Stream Format

Each JSONL file contains events like:

```json
{"type": "status", "agent": "gemini", "timestamp": "2025-11-21T17:00:00Z", "payload": {"text": "Starting analysis..."}}
{"type": "progress", "agent": "gemini", "timestamp": "2025-11-21T17:01:00Z", "payload": {"text": "Analyzing codebase", "progress": 25}}
{"type": "milestone", "agent": "gemini", "timestamp": "2025-11-21T17:05:00Z", "payload": {"text": "Architecture design complete"}}
```

### Review Files

Review files contain structured peer review results:

```json
{
  "reviewer": "codex",
  "target": "claude",
  "verdict": "approved",
  "issues": [],
  "recommendations": ["Consider adding edge case tests"],
  "timestamp": "2025-11-21T17:10:00Z"
}
```

## Troubleshooting

### Permission Errors

If you see permission errors, the recovery engine should automatically fix them. If not:

```bash
# Ensure directories are accessible
chmod -R 755 /path/to/workspace
chmod -R 755 /path/to/target
```

### Agent Not Found

Ensure agents are installed and in PATH:

```bash
which gemini
which codex
which claude
```

### Dashboard Not Loading

Check if port is available:

```bash
# Try different port
./orchestrate "task" --port 9000
```

### Workers Stuck

If workers appear stuck, check the event logs:

```bash
tail -f workspace/orch_*/gemini.jsonl
tail -f workspace/orch_*/codex.jsonl
tail -f workspace/orch_*/claude.jsonl
```

## Advanced Usage

### Programmatic Access

You can also use the orchestrator programmatically:

```python
from pathlib import Path
from orchestrator.coordinator import Coordinator, create_session_id

# Create coordinator
coordinator = Coordinator(
    session_id=create_session_id(),
    workspace_dir=Path("./workspace"),
    target_project_dir=Path("./my-project"),
    orchestrator_dir=Path("."),
    user_prompt="Add feature X"
)

# Decompose task
breakdown = coordinator.decompose_task("Add feature X")

# Launch workers
coordinator.launch_all_workers(breakdown)

# Monitor
coordinator.monitor_loop()

# Get summary
summary = coordinator.get_summary()
print(summary)
```

### Custom Task Breakdown

You can customize how tasks are broken down by modifying `coordinator.py`:

```python
def decompose_task(self, user_prompt: str) -> TaskBreakdown:
    # Custom logic here
    pass
```

## Best Practices

1. **Clear Prompts**: Provide specific, actionable task descriptions
2. **Proper Context**: Use `--target` to specify the correct project directory
3. **Monitor Progress**: Keep the dashboard open to track progress
4. **Review Decisions**: Pay attention to orchestrator decisions
5. **Check Logs**: Review `orchestrator.log` for detailed information
6. **Session Management**: Keep workspace directories organized by session

## Tips

- Start with simple tasks to understand the workflow
- Use verbose mode (`-v`) for debugging
- Review the event streams to understand agent behavior
- Manually trigger reviews when you want to check progress
- Use headless mode for automation/CI scenarios
