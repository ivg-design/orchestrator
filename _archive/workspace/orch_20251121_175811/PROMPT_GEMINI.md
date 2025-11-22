# GEMINI TASK: Design Meta-Orchestration System Architecture

## Your Role
You are the **Architect & Designer**. Design the complete technical architecture for the meta-orchestration system.

## Context
Read the approved architecture at: `/Users/ivg/orchestrator_design/FINAL_ARCHITECTURE.md`

## Your Task

### 1. Design Complete File Structure
Create detailed specifications for each Python module:
- `orchestrator/models.py` - Pydantic data models for all events and state
- `orchestrator/workers.py` - Agent launcher functions with correct CLI flags
- `orchestrator/coordinator.py` - Main orchestration loop logic
- `orchestrator/review_engine.py` - Peer review trigger and evaluation system
- `orchestrator/recovery.py` - Permission error detection and auto-recovery
- `orchestrator/server.py` - FastAPI backend with SSE endpoints
- `static/dashboard.html` - Real-time UI with EventSource

### 2. Specify Data Models
Define Pydantic models for:
- Agent events (status, progress, finding, blocker, milestone, review)
- Agent state (status, pid, output_file, task)
- Review requests and responses
- Orchestrator decisions

### 3. Design API Endpoints
Specify FastAPI routes:
- `GET /api/{session_id}/agents` - Agent status
- `GET /api/{session_id}/events` - SSE stream
- `POST /api/{session_id}/review` - Trigger review
- `GET /api/{session_id}/health` - Health check

### 4. Design Orchestration Flow
Document:
- Task breakdown algorithm
- Agent launch sequence with fallbacks
- Event monitoring loop
- Review trigger conditions
- Decision policy implementation

## Deliverables

Create the following files in `/Users/ivg/orchestrator/workspace/orch_20251121_175811/`:

1. **ARCHITECTURE_SPEC.md** - Complete technical specification
2. **DATA_MODELS.md** - All Pydantic model specifications
3. **API_SPEC.md** - FastAPI endpoint specifications
4. **FLOW_DIAGRAM.md** - Orchestration flow description

Be thorough and detailed. Include code examples and type annotations.
