"""Tests for worker command building and process management."""

import pytest
from pathlib import Path
from orchestrator.models import AgentName
from orchestrator.workers import WorkerProcess


def test_gemini_command_builder():
    """Test Gemini worker command building."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    worker = WorkerProcess(
        name=AgentName.GEMINI,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    cmd = worker.build_command()

    assert "gemini" in cmd
    assert "--yolo" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd
    assert "--include-directories" in cmd

    # Check all three directories are included
    assert str(workspace) in cmd
    assert str(target) in cmd
    assert str(orchestrator) in cmd


def test_codex_command_builder():
    """Test Codex worker command building."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    worker = WorkerProcess(
        name=AgentName.CODEX,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    cmd = worker.build_command()

    assert "codex" in cmd
    assert "exec" in cmd
    assert "--json" in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--skip-git-repo-check" in cmd
    assert "-C" in cmd
    assert str(target) in cmd


def test_claude_command_builder():
    """Test Claude worker command building."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    worker = WorkerProcess(
        name=AgentName.CLAUDE,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    cmd = worker.build_command()

    assert "claude" in cmd
    assert "--print" in cmd
    assert "--dangerously-skip-permissions" in cmd
    assert "--strict-mcp-config" in cmd
    assert "--add-dir" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd


def test_codex_skip_git_check_flag():
    """Test that Codex gets skip-git-repo-check flag by default."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    worker = WorkerProcess(
        name=AgentName.CODEX,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
        skip_git_check=True,
    )

    cmd = worker.build_command()
    assert "--skip-git-repo-check" in cmd


def test_claude_has_safety_enforcer():
    """Test that Claude worker gets safety enforcer initialized."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    worker = WorkerProcess(
        name=AgentName.CLAUDE,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    assert worker.safety_enforcer is not None
    assert worker.safety_enforcer.sandbox is not None


def test_other_agents_no_safety_enforcer():
    """Test that non-Claude workers don't get safety enforcer."""
    workspace = Path("/tmp/workspace")
    target = Path("/tmp/target")
    orchestrator = Path("/tmp/orchestrator")

    gemini_worker = WorkerProcess(
        name=AgentName.GEMINI,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    codex_worker = WorkerProcess(
        name=AgentName.CODEX,
        task="Test task",
        workspace_dir=workspace,
        target_project_dir=target,
        orchestrator_dir=orchestrator,
    )

    assert gemini_worker.safety_enforcer is None
    assert codex_worker.safety_enforcer is None
