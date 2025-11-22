"""Permission recovery and error handling engine."""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    AgentName,
    Event,
    EventType,
    EventPayload,
    PermissionBlocker,
    RecoveryAction,
)
from .workers import WorkerProcess
import json

logger = logging.getLogger(__name__)


class PermissionRecoveryEngine:
    """Monitors worker output streams and automatically fixes permission issues."""

    # Error patterns for each agent
    ERROR_PATTERNS = {
        AgentName.GEMINI: [
            r"Path must be within one of the workspace directories",
            r"File path must be within one of the workspace directories",
            r"Permission denied",
            r"Authentication required",
        ],
        AgentName.CODEX: [
            r"Not inside a trusted directory",
            r"Permission denied",
            r"Repository check failed",
            r"not a git repository",
        ],
        AgentName.CLAUDE: [
            r"Permission denied",
            r"Access blocked",
        ],
    }

    def __init__(
        self,
        workspace_dir: Path,
        target_project_dir: Path,
        orchestrator_dir: Path,
    ):
        self.workspace_dir = workspace_dir
        self.target_project_dir = target_project_dir
        self.orchestrator_dir = orchestrator_dir
        self.recovery_actions: List[RecoveryAction] = []

    def check_for_errors(self, worker: WorkerProcess, events: List[Event]) -> Optional[str]:
        """Check events and stderr for permission errors."""
        # Check JSONL events for errors
        for event in events:
            if event.type == EventType.ERROR:
                error_text = event.payload.text
                error_type = self._detect_error_type(worker.name, error_text)
                if error_type:
                    return error_type

        # Also check stderr for errors
        stderr_lines = worker.read_stderr_lines()
        for line in stderr_lines:
            error_type = self._detect_error_type(worker.name, line)
            if error_type:
                logger.info(f"Detected error in stderr: {line}")
                return error_type

        return None

    def _detect_error_type(self, agent_name: AgentName, error_text: str) -> Optional[str]:
        """Detect the type of error from error text."""
        patterns = self.ERROR_PATTERNS.get(agent_name, [])

        for pattern in patterns:
            if re.search(pattern, error_text, re.IGNORECASE):
                # Return error type based on pattern
                if "workspace directories" in error_text or "workspace directories" in pattern:
                    return "gemini_permissions"
                elif "trusted directory" in error_text or "git repository" in error_text:
                    return "codex_git_check"
                elif "Permission denied" in error_text:
                    return "generic_permission"

        return None

    def attempt_recovery(
        self,
        worker: WorkerProcess,
        error_type: str,
    ) -> Optional[RecoveryAction]:
        """Attempt to recover from the error."""
        logger.info(f"Attempting recovery for {worker.name.value}: {error_type}")

        if error_type == "gemini_permissions":
            return self._fix_gemini_permissions(worker)
        elif error_type == "codex_git_check":
            return self._fix_codex_permissions(worker)
        elif error_type == "generic_permission":
            return self._escalate_permission_issue(worker, "Generic permission error")
        else:
            return None

    def _fix_gemini_permissions(self, worker: WorkerProcess) -> RecoveryAction:
        """Relaunch Gemini with corrected --include-directories flags."""
        logger.info(f"Fixing Gemini permissions for {worker.name.value}")

        # Stop current worker
        worker.stop()

        # Get required directories
        required_dirs = [
            str(self.workspace_dir),
            str(self.target_project_dir),
            str(self.orchestrator_dir),
        ]

        # Relaunch with corrected command
        worker.launch()

        # Create recovery action record
        action = RecoveryAction(
            worker=worker.name,
            issue="gemini_permissions",
            action="relaunched_with_directories",
            directories=required_dirs,
        )

        self.recovery_actions.append(action)
        logger.info(f"Gemini permissions fixed: {action}")

        # Emit recovery event
        self._emit_recovery_event(worker, action, "success")

        return action

    def _fix_codex_permissions(self, worker: WorkerProcess) -> RecoveryAction:
        """Relaunch Codex with --skip-git-repo-check flag."""
        logger.info(f"Fixing Codex permissions for {worker.name.value}")

        # Stop current worker
        worker.stop()

        # Enable skip_git_check flag and relaunch with updated command
        worker.skip_git_check = True
        restart_cmd = worker.build_command()
        worker.launch(command_override=restart_cmd)

        # Create recovery action record
        action = RecoveryAction(
            worker=worker.name,
            issue="codex_git_check",
            action="relaunched_with_skip_flag",
        )

        self.recovery_actions.append(action)
        logger.info(f"Codex permissions fixed: {action}")

        # Emit recovery event
        self._emit_recovery_event(worker, action, "success")

        return action

    def _escalate_permission_issue(
        self, worker: WorkerProcess, error_text: str
    ) -> RecoveryAction:
        """Escalate permission issue to user when auto-fix is not possible."""
        logger.warning(f"Escalating permission issue for {worker.name.value}: {error_text}")

        blocker = PermissionBlocker(
            worker=worker.name,
            error=error_text,
            action_required="Manual intervention needed",
            suggestions=[
                "Check file permissions on target directories",
                "Verify agent authentication status",
                "Review security settings",
            ],
        )

        # Create recovery action record
        action = RecoveryAction(
            worker=worker.name,
            issue="escalated_permission",
            action="user_intervention_required",
        )

        self.recovery_actions.append(action)

        # Emit escalation event
        self._emit_recovery_event(worker, action, "escalated", blocker)

        return action

    def _emit_recovery_event(
        self,
        worker: WorkerProcess,
        action: RecoveryAction,
        status: str,
        blocker: Optional[PermissionBlocker] = None
    ) -> None:
        """Emit a recovery event to the worker's event stream."""
        event_data = {
            "type": EventType.RECOVERY.value,
            "agent": worker.name.value,
            "timestamp": action.timestamp.isoformat(),
            "payload": {
                "text": f"Recovery: {action.issue} - {action.action}",
                "data": {
                    "issue": action.issue,
                    "action": action.action,
                    "status": status,
                    "directories": action.directories,
                }
            }
        }

        # If escalated, include blocker information
        if blocker:
            event_data["payload"]["data"]["blocker"] = {
                "error": blocker.error,
                "action_required": blocker.action_required,
                "suggestions": blocker.suggestions,
            }
            # Also emit a permission blocker event
            blocker_event_data = {
                "type": EventType.PERMISSION_BLOCKER.value,
                "agent": worker.name.value,
                "timestamp": blocker.timestamp.isoformat(),
                "payload": {
                    "text": f"Permission blocker: {blocker.error}",
                    "data": {
                        "error": blocker.error,
                        "action_required": blocker.action_required,
                        "suggestions": blocker.suggestions,
                    }
                }
            }
            # Write blocker event to worker's JSONL
            self._write_event_to_jsonl(worker, blocker_event_data)

        # Write recovery event to worker's JSONL
        self._write_event_to_jsonl(worker, event_data)

    def _write_event_to_jsonl(self, worker: WorkerProcess, event_data: Dict) -> None:
        """Write an event to the worker's JSONL output file."""
        output_path = self.workspace_dir / f"{worker.name.value}.jsonl"
        try:
            with open(output_path, "a") as f:
                f.write(json.dumps(event_data) + "\n")
            logger.debug(f"Wrote recovery event to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write recovery event: {e}")

    def prepare_worker_environment(self, worker_name: AgentName) -> Dict:
        """Ensure all permissions are set BEFORE launching worker."""
        logger.info(f"Preparing environment for {worker_name.value}")

        # 1. Validate directories exist
        required_dirs = [
            self.workspace_dir,
            self.target_project_dir,
            self.orchestrator_dir,
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.info(f"Creating directory: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)

        # 2. Check read/write permissions
        for dir_path in required_dirs:
            if not os.access(dir_path, os.R_OK | os.W_OK):
                logger.warning(f"Fixing permissions for: {dir_path}")
                try:
                    os.chmod(dir_path, 0o755)
                except PermissionError as e:
                    raise PermissionError(
                        f"Cannot access {dir_path}. Manual fix required: {e}"
                    )

        # 3. Worker-specific setup
        if worker_name == AgentName.GEMINI:
            return {
                "include_directories": [str(d) for d in required_dirs]
            }
        elif worker_name == AgentName.CODEX:
            return {
                "working_directory": str(self.target_project_dir),
                "flags": ["--skip-git-repo-check"],
            }
        elif worker_name == AgentName.CLAUDE:
            return {
                "sandbox": {
                    "allowed_dirs": [str(d) for d in required_dirs],
                    "blocked_commands": ["rm -rf", "dd", "mkfs"],
                }
            }

        return {}

    def get_recovery_summary(self) -> Dict:
        """Get summary of all recovery actions taken."""
        return {
            "total_recoveries": len(self.recovery_actions),
            "by_worker": self._count_by_worker(),
            "by_issue": self._count_by_issue(),
            "actions": [action.dict() for action in self.recovery_actions],
        }

    def _count_by_worker(self) -> Dict[str, int]:
        """Count recovery actions by worker."""
        counts = {}
        for action in self.recovery_actions:
            worker_name = action.worker.value
            counts[worker_name] = counts.get(worker_name, 0) + 1
        return counts

    def _count_by_issue(self) -> Dict[str, int]:
        """Count recovery actions by issue type."""
        counts = {}
        for action in self.recovery_actions:
            issue = action.issue
            counts[issue] = counts.get(issue, 0) + 1
        return counts


def validate_environment(
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path,
) -> bool:
    """Validate that all required directories exist and are accessible."""
    required_dirs = [workspace_dir, target_project_dir, orchestrator_dir]

    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Directory does not exist: {dir_path}")
            return False

        if not os.access(dir_path, os.R_OK | os.W_OK):
            logger.error(f"Directory not accessible: {dir_path}")
            return False

    return True


def create_required_directories(
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path,
) -> None:
    """Create all required directories if they don't exist."""
    required_dirs = [workspace_dir, target_project_dir, orchestrator_dir]

    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.info(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
