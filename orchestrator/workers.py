"""Worker agent launcher and process management."""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO

from .models import AgentName, Event, WorkerState, WorkerStatus, EventType, EventPayload, SandboxConfig
from .safety import SafetyEnforcer, create_default_sandbox

logger = logging.getLogger(__name__)


class WorkerProcess:
    """Manages a single worker agent process."""

    def __init__(
        self,
        name: AgentName,
        task: str,
        workspace_dir: Path,
        target_project_dir: Path,
        orchestrator_dir: Path,
        skip_git_check: bool = True
    ):
        self.name = name
        self.task = task
        self.workspace_dir = workspace_dir
        self.target_project_dir = target_project_dir
        self.orchestrator_dir = orchestrator_dir
        self.process: Optional[subprocess.Popen] = None
        self.output_file: Optional[TextIO] = None
        self.state = WorkerState(name=name, status=WorkerStatus.IDLE)
        self._stdout_offset = 0
        self._stderr_buffer: List[str] = []
        self.skip_git_check = skip_git_check

        # Initialize safety enforcer for Claude workers
        self.safety_enforcer: Optional[SafetyEnforcer] = None
        if name == AgentName.CLAUDE:
            sandbox_config = create_default_sandbox(
                workspace_dir, target_project_dir, orchestrator_dir
            )
            self.safety_enforcer = SafetyEnforcer(sandbox_config)
            logger.info(f"Safety enforcer initialized for {name.value}")

    def build_command(self) -> List[str]:
        """Build the command to launch the worker agent."""
        if self.name == AgentName.GEMINI:
            return self._build_gemini_command()
        elif self.name == AgentName.CODEX:
            return self._build_codex_command()
        elif self.name == AgentName.CLAUDE:
            return self._build_claude_command()
        else:
            raise ValueError(f"Unknown agent: {self.name}")

    def _build_gemini_command(self) -> List[str]:
        """Build Gemini worker command with all required permissions."""
        cmd = [
            "gemini",
            "--yolo",
            "--output-format", "json"
        ]

        # Add all directory permissions
        for dir_path in [self.workspace_dir, self.target_project_dir, self.orchestrator_dir]:
            cmd.extend(["--include-directories", str(dir_path)])

        cmd.append(self.task)
        return cmd

    def _build_codex_command(self) -> List[str]:
        """Build Codex worker command with working directory."""
        cmd = [
            "codex", "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox"
        ]

        # Add git check skip flag if enabled
        if self.skip_git_check:
            cmd.append("--skip-git-repo-check")

        cmd.extend([
            "-C", str(self.target_project_dir),
            self.task
        ])
        return cmd

    def _build_claude_command(self) -> List[str]:
        """Build Claude worker command with sandbox restrictions."""
        cmd = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            "--strict-mcp-config",
            "--add-dir", str(self.workspace_dir),
            "--add-dir", str(self.target_project_dir),
            "--add-dir", str(self.orchestrator_dir),
            "--output-format", "json",
            self.task
        ]
        return cmd

    def launch(self, command_override: Optional[List[str]] = None) -> None:
        """Launch the worker process and redirect output to JSONL file."""
        output_path = self.workspace_dir / f"{self.name.value}.jsonl"

        logger.info(f"Launching {self.name.value} worker...")
        logger.debug(f"Command: {' '.join(command_override or self.build_command())}")
        logger.debug(f"Output: {output_path}")

        # Open output file
        self.output_file = open(output_path, "w")

        # Launch process
        cmd = command_override or self.build_command()
        self.process = subprocess.Popen(
            cmd,
            stdout=self.output_file,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )

        # Update state
        self.state.status = WorkerStatus.RUNNING
        self.state.process_id = self.process.pid
        self.state.task = self.task

        logger.info(f"{self.name.value} worker launched (PID: {self.process.pid})")

    def is_running(self) -> bool:
        """Check if the worker process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self) -> None:
        """Stop the worker process."""
        if self.process and self.is_running():
            logger.info(f"Stopping {self.name.value} worker...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {self.name.value} worker...")
                self.process.kill()
                self.process.wait()

        if self.output_file:
            self.output_file.close()
            self.output_file = None

        self.state.status = WorkerStatus.IDLE
        self.state.process_id = None

    def read_events(self) -> List[Event]:
        """Read new events from the worker's JSONL output file."""
        output_path = self.workspace_dir / f"{self.name.value}.jsonl"

        if not output_path.exists():
            return []

        events = []
        try:
            with open(output_path, "r") as f:
                # Seek to last read position
                f.seek(self._stdout_offset)

                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Convert to Event model
                        event = self._parse_event(data)
                        if event:
                            events.append(event)
                    except json.JSONDecodeError as e:
                        logger.error(f"Malformed JSON from {self.name.value}: {e} - Line: {line[:100]}")
                        # Create error event for malformed JSON
                        events.append(Event(
                            type=EventType.ERROR,
                            agent=self.name,
                            payload=EventPayload(text=f"Malformed JSON: {line[:200]}")
                        ))
                        continue

                # Update offset to current position
                self._stdout_offset = f.tell()
        except Exception as e:
            logger.error(f"Error reading events from {self.name.value}: {e}")

        return events

    def _parse_event(self, data: Dict) -> Optional[Event]:
        """Parse raw JSON data into Event model."""
        try:
            # Handle different event formats from different agents
            event_type = data.get("type")

            # If no type field, this is malformed - don't default to "status"
            if not event_type:
                logger.error(f"Event missing 'type' field from {self.name.value}: {data}")
                return None

            # Map event types to our EventType enum
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                # Unknown event type - log error instead of defaulting
                logger.error(f"Unknown event type '{event_type}' from {self.name.value}")
                return None

            # Extract payload
            payload_data = data.get("payload", {})
            if isinstance(payload_data, str):
                payload_data = {"text": payload_data}
            elif not isinstance(payload_data, dict):
                payload_data = {"text": str(payload_data)}

            # Ensure text field exists
            if "text" not in payload_data:
                payload_data["text"] = data.get("message", str(data))

            payload = EventPayload(**payload_data)

            # Extract timestamp if present
            timestamp = datetime.utcnow()
            if "timestamp" in data:
                try:
                    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()

            return Event(
                type=event_type_enum,
                agent=self.name,
                payload=payload,
                timestamp=timestamp
            )
        except Exception as e:
            logger.warning(f"Failed to parse event from {self.name.value}: {e}")
            return None

    def get_stderr(self) -> str:
        """Get stderr output from the process."""
        if self.process and self.process.stderr:
            try:
                return self.process.stderr.read()
            except:
                return ""
        return ""

    def read_stderr_lines(self) -> List[str]:
        """Read new stderr lines from the process."""
        new_lines = []
        if self.process and self.process.stderr:
            try:
                # Non-blocking read
                import select
                import sys

                # Check if stderr has data available
                if sys.platform != "win32":
                    ready, _, _ = select.select([self.process.stderr], [], [], 0)
                    if ready:
                        while True:
                            line = self.process.stderr.readline()
                            if not line:
                                break
                            new_lines.append(line.strip())
                            self._stderr_buffer.append(line.strip())
                else:
                    # Windows doesn't support select on pipes
                    # Use readline with timeout
                    line = self.process.stderr.readline()
                    if line:
                        new_lines.append(line.strip())
                        self._stderr_buffer.append(line.strip())
            except:
                pass
        return new_lines

    def check_safety_violations(self) -> List[str]:
        """Check for safety violations (Claude workers only)."""
        if self.safety_enforcer and self.process:
            # Monitor resource usage
            if not self.safety_enforcer.monitor_process(self.process.pid):
                logger.warning(f"Worker {self.name.value} exceeded resource limits")
                return [f"Resource limit exceeded for worker {self.name.value}"]

            # Get any security violations
            violations = self.safety_enforcer.get_violations()
            if violations:
                logger.warning(f"Security violations detected for {self.name.value}: {violations}")
                return violations

        return []

    def get_safety_report(self) -> Optional[dict]:
        """Get safety report for Claude workers."""
        if self.safety_enforcer:
            return self.safety_enforcer.get_safety_report()
        return None


class WorkerManager:
    """Manages all worker agent processes."""

    def __init__(
        self,
        workspace_dir: Path,
        target_project_dir: Path,
        orchestrator_dir: Path
    ):
        self.workspace_dir = workspace_dir
        self.target_project_dir = target_project_dir
        self.orchestrator_dir = orchestrator_dir
        self.workers: Dict[AgentName, WorkerProcess] = {}

    def launch_worker(
        self,
        name: AgentName,
        task: str
    ) -> WorkerProcess:
        """Launch a worker agent."""
        worker = WorkerProcess(
            name=name,
            task=task,
            workspace_dir=self.workspace_dir,
            target_project_dir=self.target_project_dir,
            orchestrator_dir=self.orchestrator_dir
        )
        worker.launch()
        self.workers[name] = worker
        return worker

    def stop_worker(self, name: AgentName) -> None:
        """Stop a specific worker."""
        if name in self.workers:
            self.workers[name].stop()
            del self.workers[name]

    def stop_all(self) -> None:
        """Stop all workers."""
        for worker in list(self.workers.values()):
            worker.stop()
        self.workers.clear()

    def get_worker(self, name: AgentName) -> Optional[WorkerProcess]:
        """Get a worker by name."""
        return self.workers.get(name)

    def get_all_events(self) -> Dict[AgentName, List[Event]]:
        """Get all events from all workers."""
        all_events = {}
        for name, worker in self.workers.items():
            all_events[name] = worker.read_events()
        return all_events

    def get_worker_states(self) -> Dict[AgentName, WorkerState]:
        """Get state of all workers."""
        return {name: worker.state for name, worker in self.workers.items()}


def launch_gemini(
    task: str,
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path
) -> WorkerProcess:
    """Launch Gemini worker with full permissions."""
    worker = WorkerProcess(
        name=AgentName.GEMINI,
        task=task,
        workspace_dir=workspace_dir,
        target_project_dir=target_project_dir,
        orchestrator_dir=orchestrator_dir
    )
    worker.launch()
    return worker


def launch_codex(
    task: str,
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path
) -> WorkerProcess:
    """Launch Codex worker with working directory."""
    worker = WorkerProcess(
        name=AgentName.CODEX,
        task=task,
        workspace_dir=workspace_dir,
        target_project_dir=target_project_dir,
        orchestrator_dir=orchestrator_dir
    )
    worker.launch()
    return worker


def launch_claude_worker(
    task: str,
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path
) -> WorkerProcess:
    """Launch Claude worker with sandbox restrictions."""
    worker = WorkerProcess(
        name=AgentName.CLAUDE,
        task=task,
        workspace_dir=workspace_dir,
        target_project_dir=target_project_dir,
        orchestrator_dir=orchestrator_dir
    )
    worker.launch()
    return worker
