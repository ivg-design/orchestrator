# API Specification

This document defines the REST API and Server-Sent Events (SSE) endpoints for the Orchestrator Dashboard. The server is built using **FastAPI**.

## Base URL
`http://localhost:8000`

## Endpoints

### 1. Get Session Status
Retrieves the current state of all agents and the orchestration session.

- **Endpoint:** `GET /api/{session_id}/status`
- **Response Model:** `SessionStatusResponse`

```json
{
  "session_id": "orch_20251121_175811",
  "status": "running",
  "agents": {
    "gemini": {
      "status": "running",
      "current_task": "Designing architecture...",
      "progress": 45
    },
    "codex": {
      "status": "waiting",
      "current_task": null,
      "progress": 0
    },
    "claude": {
      "status": "running",
      "current_task": "Implementing models...",
      "progress": 30
    }
  },
  "active_blockers": 0
}
```

### 2. Event Stream (SSE)
Real-time stream of events from all agents and the orchestrator. This connects directly to the `AgentEvent` model.

- **Endpoint:** `GET /api/{session_id}/events`
- **Format:** Server-Sent Events (text/event-stream)

**Stream Content:**
```text
data: {"type": "progress", "agent": "gemini", "payload": {"progress": 45, "text": "..."}}

data: {"type": "review", "agent": "codex", "payload": {"verdict": "approved", ...}}

data: {"type": "recovery", "agent": "orchestrator", "payload": {"action": "relaunched_gemini", ...}}
```

### 3. Trigger Manual Review
Allows the user to force a peer review cycle immediately.

- **Endpoint:** `POST /api/{session_id}/review`
- **Body:**
```json
{
  "focus": "Check for security vulnerabilities in the new auth module"
}
```
- **Response:** `202 Accepted`

### 4. Health Check
Simple health check for the orchestrator service.

- **Endpoint:** `GET /api/health`
- **Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 5. List Files (Workspace)
View files generated in the workspace for debugging.

- **Endpoint:** `GET /api/{session_id}/files`
- **Response:**
```json
{
  "files": [
    "gemini.jsonl",
    "claude.jsonl",
    "DATA_MODELS.md"
  ]
}
```

### 6. Get File Content
Read the content of a specific file (e.g., a generated spec).

- **Endpoint:** `GET /api/{session_id}/files/{filename}`
- **Response:** `text/plain` or `application/json` depending on file type.

## Implementation Notes

- **CORS:** Must be enabled to allow the frontend (served statically or via proxy) to connect.
- **Concurrency:** The SSE endpoint must handle multiple clients (browser tabs) without blocking the main orchestration loop.
- **Error Handling:** Standard HTTP error codes (404 for invalid session, 500 for server errors).