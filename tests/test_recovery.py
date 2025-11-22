"""Tests for recovery pattern matching and actions."""

import pytest
from pathlib import Path
from orchestrator.models import AgentName, Event, EventType, EventPayload
from orchestrator.recovery import PermissionRecoveryEngine
from orchestrator.workers import WorkerProcess


@pytest.fixture
def recovery_engine():
    """Create a recovery engine instance."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")
    return PermissionRecoveryEngine(workspace, target, orchestrator)


@pytest.fixture
def test_worker():
    """Create a test worker instance."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")
    return WorkerProcess(
        name=AgentName.GEMINI,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )


def test_detect_gemini_permissions_error(recovery_engine):
    """Test detection of Gemini workspace directory error."""
    error_text = "Path must be within one of the workspace directories"
    error_type = recovery_engine._detect_error_type(AgentName.GEMINI, error_text)
    assert error_type == "gemini_permissions"


def test_detect_codex_git_check_error(recovery_engine):
    """Test detection of Codex git repository check error."""
    error_text = "Not inside a trusted directory"
    error_type = recovery_engine._detect_error_type(AgentName.CODEX, error_text)
    assert error_type == "codex_git_check"


def test_detect_codex_git_repo_error(recovery_engine):
    """Test detection of Codex 'not a git repository' error."""
    error_text = "fatal: not a git repository (or any of the parent directories)"
    error_type = recovery_engine._detect_error_type(AgentName.CODEX, error_text)
    assert error_type == "codex_git_check"


def test_detect_generic_permission_error(recovery_engine):
    """Test detection of generic permission denied error."""
    error_text = "Permission denied: /some/path"
    error_type = recovery_engine._detect_error_type(AgentName.CLAUDE, error_text)
    assert error_type == "generic_permission"


def test_no_error_detection(recovery_engine):
    """Test that normal messages don't trigger error detection."""
    normal_text = "Processing file successfully"
    error_type = recovery_engine._detect_error_type(AgentName.GEMINI, normal_text)
    assert error_type is None


def test_check_for_errors_in_events(recovery_engine, test_worker):
    """Test checking for errors in event list."""
    events = [
        Event(
            type=EventType.STATUS,
            agent=AgentName.GEMINI,
            payload=EventPayload(text="Working on task")
        ),
        Event(
            type=EventType.ERROR,
            agent=AgentName.GEMINI,
            payload=EventPayload(text="Path must be within one of the workspace directories")
        ),
    ]

    error_type = recovery_engine.check_for_errors(test_worker, events)
    assert error_type == "gemini_permissions"


def test_recovery_summary(recovery_engine):
    """Test recovery summary generation."""
    summary = recovery_engine.get_recovery_summary()

    assert "total_recoveries" in summary
    assert "by_worker" in summary
    assert "by_issue" in summary
    assert "actions" in summary
    assert summary["total_recoveries"] == 0


def test_prepare_worker_environment_gemini(recovery_engine):
    """Test preparing environment for Gemini worker."""
    config = recovery_engine.prepare_worker_environment(AgentName.GEMINI)

    assert "include_directories" in config
    assert len(config["include_directories"]) == 3


def test_prepare_worker_environment_codex(recovery_engine):
    """Test preparing environment for Codex worker."""
    config = recovery_engine.prepare_worker_environment(AgentName.CODEX)

    assert "working_directory" in config
    assert "flags" in config
    assert "--skip-git-repo-check" in config["flags"]


def test_prepare_worker_environment_claude(recovery_engine):
    """Test preparing environment for Claude worker."""
    config = recovery_engine.prepare_worker_environment(AgentName.CLAUDE)

    assert "sandbox" in config
    assert "allowed_dirs" in config["sandbox"]
    assert "blocked_commands" in config["sandbox"]
