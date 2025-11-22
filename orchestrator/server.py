"""FastAPI server for real-time orchestration dashboard."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .coordinator import Coordinator
from .models import AgentName, Event

logger = logging.getLogger(__name__)

# Global sessions storage
active_sessions: Dict[str, Coordinator] = {}


class OrchestrationRequest(BaseModel):
    """Request to start orchestration."""
    prompt: str
    target_dir: str


def create_app(static_dir: Path) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Meta-Orchestration Dashboard",
        description="Real-time monitoring for multi-agent orchestration",
        version="0.1.0",
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files if directory exists
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app(Path(__file__).parent.parent / "static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML."""
    dashboard_path = Path(__file__).parent.parent / "static" / "dashboard.html"

    if dashboard_path.exists():
        return dashboard_path.read_text()
    else:
        return """
        <html>
            <head><title>Orchestration Dashboard</title></head>
            <body>
                <h1>Orchestration Dashboard</h1>
                <p>Dashboard HTML not found. Please create static/dashboard.html</p>
            </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
    }


# Session Management Endpoints

@app.post("/api/v1/orchestrate")
async def create_orchestration(request: OrchestrationRequest):
    """Start a new orchestration session."""
    from datetime import datetime
    from .coordinator import create_session_id

    session_id = create_session_id()

    # Create workspace directory
    workspace_dir = Path("workspace") / session_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Initialize coordinator
    coordinator = Coordinator(
        session_id=session_id,
        workspace_dir=workspace_dir,
        target_project_dir=Path(request.target_dir),
        orchestrator_dir=Path(__file__).parent.parent,
        user_prompt=request.prompt,
    )

    # Store session
    active_sessions[session_id] = coordinator

    # Start orchestration in background
    # In production, this would be run in a separate thread/process
    # For now, we just initialize it
    breakdown = coordinator.decompose_task(request.prompt)
    coordinator.launch_all_workers(breakdown)

    # Start monitoring loop in background
    asyncio.create_task(run_coordinator_loop(coordinator))

    return {
        "session_id": session_id,
        "status": "initializing",
        "created_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/sessions")
async def list_sessions():
    """List all active sessions."""
    sessions = []
    for session_id, coordinator in active_sessions.items():
        sessions.append({
            "id": session_id,
            "status": "running" if coordinator.is_running else "stopped",
            "created_at": coordinator.session.start_time.isoformat(),
            "is_complete": coordinator.session.is_complete,
        })
    return sessions


# Session-Scoped Control Endpoints

@app.post("/api/v1/{session_id}/pause")
async def pause_session(session_id: str):
    """Pause orchestration session."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    coordinator.pause()
    return {"status": "paused"}


@app.post("/api/v1/{session_id}/resume")
async def resume_session(session_id: str):
    """Resume orchestration session."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    coordinator.resume()
    return {"status": "resumed"}


@app.post("/api/v1/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop orchestration session."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    coordinator.stop()
    return {"status": "stopped"}


@app.post("/api/v1/{session_id}/review")
async def trigger_review(session_id: str):
    """Manually trigger a peer review."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    all_events = coordinator.worker_manager.get_all_events()
    coordinator.conduct_peer_review(all_events)

    return {"status": "review_triggered"}


# Session-Scoped Data Access Endpoints

@app.get("/api/v1/{session_id}/state")
async def get_session_state(session_id: str):
    """Get full current state snapshot."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "user_prompt": coordinator.user_prompt,
        "is_running": coordinator.is_running,
        "is_paused": coordinator.is_paused,
        "is_complete": coordinator.session.is_complete,
        "workers": {
            name.value: {
                "status": state.status.value,
                "progress": state.progress,
                "task": state.task,
                "error_count": state.error_count,
            }
            for name, state in coordinator.session.workers.items()
        },
        "decisions": [
            {
                "action": d.action.value,
                "reason": d.reason,
                "next_steps": d.next_steps,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in coordinator.session.decisions
        ],
        "recovery_actions": [
            {
                "worker": a.worker.value,
                "issue": a.issue,
                "action": a.action,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in coordinator.session.recovery_actions
        ],
    }


@app.get("/api/v1/{session_id}/logs/{agent_name}")
async def get_agent_logs(session_id: str, agent_name: str):
    """Get raw logs for a specific agent."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        agent = AgentName(agent_name.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent name: {agent_name}")

    log_path = coordinator.workspace_dir / f"{agent.value}.jsonl"

    if not log_path.exists():
        return {"logs": []}

    # Read log file
    logs = []
    with open(log_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    return {"logs": logs}


# SSE Stream Endpoint

@app.get("/api/v1/{session_id}/events")
async def event_stream(session_id: str, request: Request):
    """Server-Sent Events stream for real-time updates."""
    coordinator = active_sessions.get(session_id)
    if not coordinator:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generate():
        """Generate SSE events."""
        last_event_counts = {agent: 0 for agent in AgentName}
        event_id = 0

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from session {session_id}")
                    break

                # Get new events from all workers
                all_events = coordinator.worker_manager.get_all_events()

                # Stream individual agent events
                for agent_name, events in all_events.items():
                    # Skip if no new events
                    new_event_count = len(events)
                    if new_event_count <= last_event_counts[agent_name]:
                        continue

                    # Send new events
                    for event in events[last_event_counts[agent_name]:]:
                        event_id += 1
                        event_data = {
                            "type": "agent_event",
                            "agent": event.agent.value,
                            "msg_type": event.type.value,
                            "timestamp": event.timestamp.isoformat(),
                            "payload": {
                                "text": event.payload.text,
                                "progress": event.payload.progress,
                                "file": event.payload.file,
                                "data": event.payload.data,
                            }
                        }

                        yield f"id: {event_id}\n"
                        yield f"event: agent_event\n"
                        yield f"data: {json.dumps(event_data)}\n\n"

                    last_event_counts[agent_name] = new_event_count

                # Send recovery events
                if coordinator.session.recovery_actions:
                    for action in coordinator.session.recovery_actions:
                        event_id += 1
                        recovery_data = {
                            "type": "recovery_event",
                            "worker": action.worker.value,
                            "issue": action.issue,
                            "action": action.action,
                            "status": "success",
                            "timestamp": action.timestamp.isoformat(),
                        }

                        yield f"id: {event_id}\n"
                        yield f"event: recovery_event\n"
                        yield f"data: {json.dumps(recovery_data)}\n\n"

                # Send decision events
                if coordinator.session.decisions:
                    latest_decision = coordinator.session.decisions[-1]
                    event_id += 1
                    decision_data = {
                        "type": "decision_event",
                        "trigger": "MILESTONE",
                        "verdict": latest_decision.action.value,
                        "reason": latest_decision.reason,
                        "timestamp": latest_decision.timestamp.isoformat(),
                    }

                    yield f"id: {event_id}\n"
                    yield f"event: decision_event\n"
                    yield f"data: {json.dumps(decision_data)}\n\n"

                # Send heartbeat
                yield f": heartbeat\n\n"

                await asyncio.sleep(1)  # Update every second

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def run_coordinator_loop(coordinator: Coordinator):
    """Run coordinator monitoring loop in background."""
    try:
        # Run in thread pool to avoid blocking
        import concurrent.futures
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, coordinator.monitor_loop)
    except Exception as e:
        logger.error(f"Error in coordinator loop: {e}")


def set_coordinator(session_id: str, coord: Coordinator) -> None:
    """Set a coordinator for a session."""
    active_sessions[session_id] = coord


def get_coordinator(session_id: str) -> Optional[Coordinator]:
    """Get a coordinator for a session."""
    return active_sessions.get(session_id)


def get_active_sessions() -> Dict[str, Coordinator]:
    """Get all active sessions."""
    return active_sessions.copy()
