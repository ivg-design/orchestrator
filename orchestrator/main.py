#!/usr/bin/env python3
"""Main CLI entry point for the Meta-Orchestrator."""

import argparse
import asyncio
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_session_id() -> str:
    """Create a unique session ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"orch_{timestamp}"


def start_server(port: int = 8000):
    """Start the FastAPI server in background."""
    logger.info(f"Starting FastAPI server on port {port}...")

    # Start uvicorn server
    server_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "orchestrator.server:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--log-level", "info"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    logger.info(f"Server started with PID: {server_process.pid}")
    return server_process


def orchestrate(args):
    """Start a new orchestration session."""
    prompt = args.prompt
    target_dir = Path(args.target_dir).resolve()
    orchestrator_dir = Path(__file__).parent.parent.resolve()

    # Create session
    session_id = create_session_id()
    workspace_dir = orchestrator_dir / "workspace" / session_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting orchestration session: {session_id}")
    logger.info(f"Target directory: {target_dir}")
    logger.info(f"Workspace: {workspace_dir}")
    logger.info(f"User prompt: {prompt}")

    # Start server if not running
    server_process = None
    if not args.no_server:
        try:
            server_process = start_server(args.port)
            import time
            time.sleep(2)  # Give server time to start
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            logger.info("Continuing without server (dashboard will not be available)")

    # Initialize coordinator
    from .coordinator import Coordinator

    coordinator = Coordinator(
        session_id=session_id,
        workspace_dir=workspace_dir,
        target_project_dir=target_dir,
        orchestrator_dir=orchestrator_dir,
        user_prompt=prompt,
    )

    # Set coordinator in server (if running)
    if server_process:
        from .server import set_coordinator
        set_coordinator(session_id, coordinator)

    # Display info
    print("\n" + "="*70)
    print(f"Meta-Orchestration Session Started")
    print("="*70)
    print(f"Session ID: {session_id}")
    print(f"Target: {target_dir}")
    print(f"Workspace: {workspace_dir}")
    if not args.no_server:
        print(f"Dashboard: http://localhost:{args.port}/?session={session_id}")
    print("="*70 + "\n")

    # Decompose task
    print("Decomposing task across agents...")
    breakdown = coordinator.decompose_task(prompt)

    print(f"\nTask breakdown:")
    print(f"  - Gemini (Architect): {breakdown.gemini.role}")
    print(f"  - Claude (Implementer): {breakdown.claude.role}")
    print(f"  - Codex (Reviewer): {breakdown.codex.role}")
    print()

    # Launch workers
    print("Launching worker agents...")
    coordinator.launch_all_workers(breakdown)

    print("\nWorkers launched:")
    for name, state in coordinator.session.workers.items():
        print(f"  - {name.value}: PID {state.process_id}")
    print()

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down gracefully...")
        coordinator.stop()
        if server_process:
            server_process.terminate()
            server_process.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start monitoring loop
    try:
        print("Starting orchestration monitoring...")
        print("Press Ctrl+C to stop\n")

        coordinator.monitor_loop()

        print("\n" + "="*70)
        print("Orchestration Complete!")
        print("="*70)

        # Display summary
        summary = coordinator.get_summary()
        print(f"\nSession: {summary['session_id']}")
        print(f"Status: {'Complete' if summary['is_complete'] else 'Incomplete'}")
        print(f"\nWorkers:")
        for name, state in summary['workers'].items():
            print(f"  - {name}: {state['status']} ({state['progress']}%)")

        print(f"\nDecisions: {summary['decisions']}")
        print(f"Recoveries: {summary['recoveries']['total_recoveries']}")

        if summary['reviews']['total_reviews'] > 0:
            print(f"\nReviews:")
            print(f"  Total: {summary['reviews']['total_reviews']}")
            for verdict, count in summary['reviews']['by_verdict'].items():
                print(f"  {verdict}: {count}")

        print(f"\nResults saved in: {workspace_dir}")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        coordinator.stop()
        if server_process:
            server_process.terminate()
            server_process.wait()


def resume(args):
    """Resume a paused orchestration session."""
    session_id = args.session_id
    orchestrator_dir = Path(__file__).parent.parent.resolve()
    workspace_dir = orchestrator_dir / "workspace" / session_id

    if not workspace_dir.exists():
        logger.error(f"Session not found: {session_id}")
        sys.exit(1)

    logger.info(f"Resuming session: {session_id}")

    # TODO: Implement resume logic
    # Would need to:
    # 1. Read session state from workspace
    # 2. Recreate coordinator with saved state
    # 3. Resume monitoring loop

    print(f"Resume functionality not yet implemented")
    print(f"Session workspace: {workspace_dir}")


def status(args):
    """Show status of active sessions."""
    orchestrator_dir = Path(__file__).parent.parent.resolve()
    workspace_dir = orchestrator_dir / "workspace"

    if not workspace_dir.exists():
        print("No sessions found")
        return

    sessions = sorted(workspace_dir.glob("orch_*"))

    if not sessions:
        print("No sessions found")
        return

    print("\nActive Sessions:")
    print("="*70)

    for session_path in sessions:
        session_id = session_path.name

        # Try to read state
        # For now, just show basic info
        print(f"\nSession: {session_id}")
        print(f"Workspace: {session_path}")

        # Check for agent logs
        logs = list(session_path.glob("*.jsonl"))
        if logs:
            print(f"Agent logs: {', '.join(log.stem for log in logs)}")

    print("="*70 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Meta-Orchestrator: Multi-agent task orchestration system"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Orchestrate command
    orch_parser = subparsers.add_parser(
        "orchestrate",
        help="Start a new orchestration session"
    )
    orch_parser.add_argument(
        "prompt",
        type=str,
        help="Natural language task description"
    )
    orch_parser.add_argument(
        "--target-dir", "-C",
        type=str,
        default=".",
        help="Target project directory (default: current directory)"
    )
    orch_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    orch_parser.add_argument(
        "--no-server",
        action="store_true",
        help="Don't start the web server"
    )

    # Resume command
    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume a paused session"
    )
    resume_parser.add_argument(
        "session_id",
        type=str,
        help="Session ID to resume"
    )

    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show status of sessions"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "orchestrate":
        orchestrate(args)
    elif args.command == "resume":
        resume(args)
    elif args.command == "status":
        status(args)


if __name__ == "__main__":
    main()
