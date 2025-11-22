"""Sandbox and security policy enforcement for worker agents."""

import logging
import re
from pathlib import Path
from typing import List, Optional, Set

from .models import SandboxConfig

logger = logging.getLogger(__name__)


class SandboxMonitor:
    """Monitors worker command execution for security violations."""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.violations: List[str] = []
        self.allowed_dirs = set(Path(d).resolve() for d in config.allowed_dirs)

    def is_path_allowed(self, path: str) -> bool:
        """Check if a file path is within allowed directories."""
        try:
            resolved = Path(path).resolve()

            # Check if path is within any allowed directory
            for allowed_dir in self.allowed_dirs:
                try:
                    resolved.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue

            return False
        except Exception as e:
            logger.warning(f"Error checking path {path}: {e}")
            return False

    def is_command_blocked(self, command: str) -> bool:
        """Check if a command is blocked by the sandbox policy."""
        # Check for blocked commands
        for blocked in self.config.blocked_commands:
            if blocked in command:
                logger.warning(f"Blocked command detected: {blocked}")
                self.violations.append(f"Blocked command: {blocked}")
                return True

        # Check for suspicious patterns
        for pattern in self.config.monitor_patterns:
            if re.search(pattern, command):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                self.violations.append(f"Suspicious pattern: {pattern}")
                return True

        return False

    def requires_confirmation(self, command: str) -> bool:
        """Check if a command requires user confirmation."""
        for cmd in self.config.require_confirm:
            if cmd in command:
                logger.info(f"Command requires confirmation: {cmd}")
                return True
        return False

    def validate_file_operation(self, operation: str, path: str) -> bool:
        """Validate a file operation against sandbox policy."""
        if not self.is_path_allowed(path):
            logger.warning(f"File operation blocked: {operation} on {path}")
            self.violations.append(f"Unauthorized access: {path}")
            return False

        return True

    def get_violations(self) -> List[str]:
        """Get list of security violations."""
        return self.violations.copy()

    def clear_violations(self) -> None:
        """Clear violation history."""
        self.violations.clear()

    def get_violation_count(self) -> int:
        """Get total number of violations."""
        return len(self.violations)


class CommandFilter:
    """Filters and sanitizes commands before execution."""

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",  # Recursive delete from root
        r"dd\s+if=.*of=/dev/",  # Disk operations
        r"mkfs\.",  # Format filesystem
        r"fdisk",  # Disk partitioning
        r":\(\)\{.*\|\1&\};:",  # Fork bomb
        r">/dev/sd[a-z]",  # Direct disk write
        r"curl.*\|\s*sh",  # Download and execute
        r"wget.*\|\s*sh",  # Download and execute
        r"chmod\s+777",  # Overly permissive
        r"sudo\s+rm",  # Sudo delete
    ]

    # Commands that should never be allowed
    BLACKLIST = [
        "format",
        "mkfs",
        "fdisk",
        "parted",
        ":(){:|:&};:",  # Fork bomb
    ]

    @classmethod
    def is_dangerous(cls, command: str) -> bool:
        """Check if command is dangerous."""
        # Check blacklist
        for blocked in cls.BLACKLIST:
            if blocked in command.lower():
                return True

        # Check patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        return False

    @classmethod
    def sanitize_command(cls, command: str) -> Optional[str]:
        """Sanitize a command, return None if too dangerous."""
        if cls.is_dangerous(command):
            logger.error(f"Dangerous command blocked: {command}")
            return None

        # Remove potentially dangerous shell features
        sanitized = command

        # Remove background execution if not explicitly allowed
        # (We'll handle this separately for legitimate background tasks)

        return sanitized

    @classmethod
    def extract_file_paths(cls, command: str) -> List[str]:
        """Extract file paths from a command."""
        # Simple pattern matching for common file paths
        # This is a basic implementation - production would need more sophisticated parsing

        paths = []

        # Look for common file patterns
        path_patterns = [
            r'"([^"]+)"',  # Quoted paths
            r"'([^']+)'",  # Single-quoted paths
            r"/[\w/.-]+",  # Unix paths
            r"~/[\w/.-]+",  # Home directory paths
        ]

        for pattern in path_patterns:
            matches = re.findall(pattern, command)
            paths.extend(matches)

        return paths


class ResourceMonitor:
    """Monitors resource usage of worker processes."""

    def __init__(self, cpu_percent: int = 50, memory_mb: int = 2048):
        self.max_cpu_percent = cpu_percent
        self.max_memory_mb = memory_mb

    def check_limits(self, pid: int) -> bool:
        """Check if process is within resource limits."""
        try:
            import psutil

            process = psutil.Process(pid)

            # Check CPU usage
            cpu = process.cpu_percent(interval=1.0)
            if cpu > self.max_cpu_percent:
                logger.warning(f"Process {pid} exceeding CPU limit: {cpu}%")
                return False

            # Check memory usage
            memory_mb = process.memory_info().rss / (1024 * 1024)
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Process {pid} exceeding memory limit: {memory_mb}MB")
                return False

            return True
        except ImportError:
            logger.warning("psutil not available, skipping resource monitoring")
            return True
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
            return True  # Don't kill process on monitoring errors

    def get_process_stats(self, pid: int) -> dict:
        """Get process resource statistics."""
        try:
            import psutil

            process = psutil.Process(pid)

            return {
                "cpu_percent": process.cpu_percent(interval=1.0),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "num_threads": process.num_threads(),
                "status": process.status(),
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}


class SafetyEnforcer:
    """Main safety enforcement system combining all safety components."""

    def __init__(self, sandbox_config: SandboxConfig):
        self.sandbox = SandboxMonitor(sandbox_config)
        self.command_filter = CommandFilter()
        self.resource_monitor = ResourceMonitor(
            cpu_percent=50,
            memory_mb=2048
        )

    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Validate a command for execution.

        Returns:
            (is_valid, error_message)
        """
        # Check if command is dangerous
        if self.command_filter.is_dangerous(command):
            return False, "Command blocked: Dangerous operation detected"

        # Check if command is blocked by sandbox
        if self.sandbox.is_command_blocked(command):
            return False, "Command blocked: Sandbox policy violation"

        # Extract file paths and validate
        paths = self.command_filter.extract_file_paths(command)
        for path in paths:
            if not self.sandbox.is_path_allowed(path):
                return False, f"Command blocked: Unauthorized access to {path}"

        # Check if confirmation required
        if self.sandbox.requires_confirmation(command):
            return False, "Command requires user confirmation"

        return True, None

    def monitor_process(self, pid: int) -> bool:
        """Monitor process resource usage."""
        return self.resource_monitor.check_limits(pid)

    def get_process_stats(self, pid: int) -> dict:
        """Get process statistics."""
        return self.resource_monitor.get_process_stats(pid)

    def get_violations(self) -> List[str]:
        """Get all security violations."""
        return self.sandbox.get_violations()

    def get_safety_report(self) -> dict:
        """Get comprehensive safety report."""
        return {
            "total_violations": self.sandbox.get_violation_count(),
            "violations": self.sandbox.get_violations(),
            "allowed_directories": [str(d) for d in self.sandbox.allowed_dirs],
        }


def create_default_sandbox(
    workspace_dir: Path,
    target_project_dir: Path,
    orchestrator_dir: Path
) -> SandboxConfig:
    """Create default sandbox configuration."""
    return SandboxConfig(
        allowed_dirs=[
            str(workspace_dir),
            str(target_project_dir),
            str(orchestrator_dir),
        ],
        blocked_commands=[
            "rm -rf /",
            "dd if=",
            "mkfs",
            "format",
            "fdisk",
        ],
        require_confirm=[
            "git push",
            "npm publish",
            "pip install",
            "cargo publish",
            "docker run",
        ],
        monitor_patterns=[
            r"sudo\s+",
            r"curl.*\|\s*sh",
            r"wget.*\|\s*sh",
            r"chmod\s+777",
        ],
    )


def validate_worker_safety(
    worker_name: str,
    command: str,
    safety_enforcer: SafetyEnforcer
) -> tuple[bool, Optional[str]]:
    """
    Validate worker command execution for safety.

    Returns:
        (is_safe, error_message)
    """
    logger.info(f"Validating command for {worker_name}: {command[:100]}...")

    is_valid, error = safety_enforcer.validate_command(command)

    if not is_valid:
        logger.error(f"Safety validation failed for {worker_name}: {error}")

    return is_valid, error
