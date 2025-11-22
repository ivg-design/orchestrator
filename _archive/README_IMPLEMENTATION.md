# Meta-Orchestration System - Implementation Guide

## Overview

The Meta-Orchestration System is a complete implementation of an event-driven multi-agent coordination platform that orchestrates three specialized AI agents:

- **Gemini**: Architecture & Design (Heavy Load)
- **Claude Worker**: Code Implementation (Heavy Load)
- **Codex**: Problem Solving & Review (Minimal Load)

## Architecture

The system follows the specifications defined in:
- `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`
- `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_SPEC.md`

## Project Structure

```
orchestrator/
├── orchestrate                     # Executable entry point script
├── orchestrator/                   # Main Python package
│   ├── __init__.py                 # Package initialization
│   ├── models.py                   # Pydantic data models
│   ├── workers.py                  # Agent launcher & process management
│   ├── coordinator.py              # Main orchestration logic
│   ├── review_engine.py            # Peer review system
│   ├── recovery.py                 # Permission error recovery
│   ├── server.py                   # FastAPI backend & SSE
│   ├── safety.py                   # Sandbox & security enforcement
│   └── utils.py                    # Utility functions
├── static/
│   └── dashboard.html              # Real-time monitoring dashboard
├── workspace/                      # Session workspaces (runtime)
│   └── {session_id}/
│       ├── gemini.jsonl            # Gemini output stream
│       ├── codex.jsonl             # Codex output stream
│       ├── claude.jsonl            # Claude worker output
│       └── reviews/                # Peer review artifacts
├── requirements.txt                # Python dependencies
├── setup.py                        # Package setup
└── README.md                       # User documentation
```

## Module Descriptions

### `models.py`
Defines all Pydantic models for type safety and validation:
- `AgentEvent`: Events emitted by workers
- `WorkerState`: Worker status tracking
- `PeerReview`: Review responses
- `OrchestratorDecision`: Decision policy outcomes
- `TaskBreakdown`: Task decomposition structure
- `SandboxConfig`: Security configuration

### `workers.py`
Manages worker agent processes:
- `WorkerProcess`: Individual worker process wrapper
- `WorkerManager`: Central worker management
- Builds agent-specific CLI commands with proper flags
- Handles JSONL stream parsing
- Process lifecycle management (launch, monitor, stop)

### `coordinator.py`
Core orchestration logic:
- `Coordinator`: Main orchestration engine
- Task decomposition algorithm
- Event monitoring loop
- Review triggering logic
- Session state management
- Integration with recovery and review engines

### `review_engine.py`
Peer review system:
- `ReviewEngine`: Event-based review triggering
- Review request generation
- Response parsing and evaluation
- Decision policy implementation (4 rules)
- Review artifact persistence

### `recovery.py`
Permission error detection and auto-recovery:
- `PermissionRecoveryEngine`: Error monitoring and recovery
- Proactive environment preparation
- Agent-specific error pattern detection
- Automatic relaunch with corrected flags
- Escalation to user when needed

### `safety.py`
Sandbox and security enforcement:
- `SandboxMonitor`: Path and command validation
- `CommandFilter`: Dangerous command detection
- `ResourceMonitor`: CPU/memory limit enforcement
- `SafetyEnforcer`: Unified safety validation

### `server.py`
FastAPI backend with real-time updates:
- REST endpoints for session, workers, reviews, decisions
- Server-Sent Events (SSE) stream for live updates
- Control endpoints (pause, resume, stop, trigger review)
- Dashboard HTML serving

### `utils.py`
Utility functions:
- JSONL reading/writing
- Session directory management
- Event parsing and summarization
- Path sanitization
- Duration formatting

## Key Features

### 1. Event-Driven Architecture
- Workers emit JSON events to JSONL streams
- Orchestrator monitors streams for events
- Reviews triggered by events (not rigid time intervals)
- Supports: `status`, `progress`, `finding`, `task`, `blocker`, `milestone`, `review`, `error`

### 2. Permission Recovery System
**Proactive**:
- Validates directories before launch
- Sets proper permissions on workspace/target directories
- Agent-specific environment preparation

**Reactive**:
- Monitors streams for permission errors
- Auto-detects Gemini missing `--include-directories`
- Auto-detects Codex git repository issues
- Relaunches workers with corrected flags
- Escalates unrecoverable issues to user

### 3. Peer Review System
**Triggers**:
- `MILESTONE` event from any worker
- `BLOCKER` event from any worker
- Explicit review request in event payload
- Manual trigger via dashboard
- Fallback: 15 minutes with no events

**Decision Policy**:
1. Any `blocker` → **STOP_AND_ESCALATE**
2. Majority (≥2) `concerns` → **PAUSE_AND_CLARIFY**
3. Single `concern` → **LOG_WARNING** (continue but monitor)
4. All `approved` → **CONTINUE**

### 4. Security Sandbox
**For Claude Worker**:
- Restricted to allowed directories (workspace, target, orchestrator)
- Blocked commands: `rm -rf`, `dd`, `mkfs`, `fdisk`
- Confirmation required: `git push`, `npm publish`, `pip install`
- Pattern monitoring: `sudo`, `curl | sh`, `wget | sh`

### 5. Real-Time Dashboard
- Live worker status updates via SSE
- Progress bars for each agent
- Event log with filtering
- Peer review results display
- Orchestrator decision panel
- Manual control buttons (pause, resume, stop, trigger review)

## Agent Launch Commands

### Gemini
```bash
gemini \
  --yolo \
  --include-directories /path/to/workspace \
  --include-directories /path/to/target \
  --include-directories /path/to/orchestrator \
  --output-format json \
  "task prompt"
```

### Codex
```bash
codex exec \
  --json \
  --dangerously-bypass-approvals-and-sandbox \
  -C /path/to/target \
  "task prompt"
```

### Claude Worker
```bash
claude \
  --print \
  --dangerously-skip-permissions \
  --strict-mcp-config \
  --add-dir /path/to/workspace \
  --add-dir /path/to/target \
  --output-format json \
  "task prompt"
```

## Usage

### Basic Usage
```bash
./orchestrate "Implement user authentication system for the web app"
```

### With Options
```bash
./orchestrate \
  --target /path/to/project \
  --workspace /path/to/workspace \
  --port 8080 \
  --verbose \
  "Your task description"
```

### Headless Mode (No Dashboard)
```bash
./orchestrate --no-dashboard "Your task"
```

### Command-Line Options
- `--target PATH`: Target project directory (default: current directory)
- `--workspace PATH`: Workspace directory (default: auto-generated)
- `--port PORT`: Dashboard server port (default: 8000)
- `--no-dashboard`: Run without dashboard (headless mode)
- `--verbose, -v`: Enable verbose logging

## Installation

### 1. Install Dependencies
```bash
cd /Users/ivg/orchestrator
pip install -r requirements.txt
```

### 2. Make Script Executable
```bash
chmod +x orchestrate
```

### 3. Verify Installation
```bash
./orchestrate --help
```

## Testing

### Unit Tests (TODO)
```bash
pytest tests/
```

### Integration Test
```bash
# Test with a simple task
./orchestrate "Analyze the codebase structure"

# Monitor dashboard at http://localhost:8000
```

## Configuration

### Environment Variables
- `ORCHESTRATOR_LOG_LEVEL`: Set logging level (default: INFO)
- `ORCHESTRATOR_WORKSPACE`: Default workspace directory

### Sandbox Configuration
Edit `orchestrator/safety.py` to customize:
- Blocked commands
- Confirmation-required commands
- Resource limits (CPU%, memory MB)

## Event Format

Workers must emit events in this format:

```json
{
  "type": "progress",
  "agent": "gemini",
  "timestamp": "2025-11-21T18:00:00Z",
  "payload": {
    "text": "Analyzing codebase structure...",
    "progress": 45,
    "file": "/path/to/file.py"
  }
}
```

## Recovery Scenarios

### Scenario 1: Gemini Permission Error
**Error**: "Path must be within one of the workspace directories"

**Auto-Recovery**:
1. Detect error in JSONL stream
2. Stop Gemini worker
3. Relaunch with all required `--include-directories` flags
4. Log recovery action

### Scenario 2: Codex Git Repository Error
**Error**: "Not inside a trusted directory"

**Auto-Recovery**:
1. Detect error in JSONL stream
2. Stop Codex worker
3. Relaunch with `--skip-git-repo-check` flag
4. Log recovery action

### Scenario 3: Generic Permission Error
**Error**: "Permission denied"

**Escalation**:
1. Detect error in JSONL stream
2. Pause orchestration
3. Notify user with suggestions
4. Wait for manual intervention

## Monitoring & Debugging

### View Logs
```bash
tail -f orchestrator.log
```

### View Worker Output
```bash
# Gemini output
tail -f workspace/{session_id}/gemini.jsonl

# Codex output
tail -f workspace/{session_id}/codex.jsonl

# Claude output
tail -f workspace/{session_id}/claude.jsonl
```

### API Endpoints
- `GET /health`: Health check
- `GET /api/session`: Session information
- `GET /api/workers`: Worker status
- `GET /api/reviews`: Peer review summary
- `GET /api/decisions`: Orchestrator decisions
- `GET /api/recovery`: Recovery actions
- `GET /api/summary`: Complete summary
- `GET /api/events/stream`: SSE event stream
- `POST /api/control/pause`: Pause orchestration
- `POST /api/control/resume`: Resume orchestration
- `POST /api/control/stop`: Stop orchestration
- `POST /api/control/review`: Trigger manual review

## Troubleshooting

### Problem: Workers not starting
**Solution**: Check that agent CLIs are in PATH:
```bash
which gemini
which codex
which claude
```

### Problem: Permission errors persist
**Solution**: Manually check directory permissions:
```bash
ls -la workspace/
ls -la target_project/
```

### Problem: Dashboard not loading
**Solution**: Check if port is already in use:
```bash
lsof -i :8000
```

### Problem: Events not appearing in dashboard
**Solution**: Check SSE connection in browser console, verify JSONL format

## Performance Considerations

### Resource Limits
- CPU: 50% per worker (configurable)
- Memory: 2GB per worker (configurable)
- Runtime: 1 hour max per worker (configurable)

### Token Management
- Gemini: 8K-10K tokens per task
- Claude Worker: 8K-10K tokens per task
- Codex: 2K-3K tokens per task (minimal load)
- Reviews: 200 words max per review

### Fallback Strategy
1. **Tier 1** (Ideal): Gemini + Claude + Codex
2. **Tier 2** (Acceptable): Gemini + Claude (orchestrator reviews)
3. **Tier 3** (Degraded): Gemini + Codex
4. **Tier 4** (Degraded): Claude + Codex
5. **Tier 5** (Fallback): Solo orchestrator mode

## Future Enhancements

### Planned Features
- [ ] WebSocket support for bi-directional communication
- [ ] Review voting system with weighted verdicts
- [ ] Automatic task priority adjustment
- [ ] Worker health checks and heartbeat monitoring
- [ ] Persistent session storage (SQLite/PostgreSQL)
- [ ] Multi-session management
- [ ] Agent performance metrics
- [ ] Custom review policies
- [ ] Integration with CI/CD pipelines
- [ ] Plugin system for custom agents

### Optional Integrations
- [ ] Slack/Discord notifications
- [ ] GitHub issue tracking
- [ ] Prometheus metrics export
- [ ] Grafana dashboard
- [ ] Docker containerization
- [ ] Kubernetes orchestration

## References

- Architecture Design: `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`
- Gemini Specs: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/ARCHITECTURE_SPEC.md`
- Data Models: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/DATA_MODELS.md`
- API Spec: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/API_SPEC.md`
- Flow Diagram: `/Users/ivg/orchestrator/workspace/orch_20251121_175811/FLOW_DIAGRAM.md`

## License

MIT License

## Contributing

See CONTRIBUTING.md for guidelines.

## Support

For issues and questions, please file a GitHub issue.
