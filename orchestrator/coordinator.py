"""Main orchestration coordinator logic."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    Action,
    AgentName,
    Event,
    EventType,
    SessionState,
    TaskAssignment,
    TaskBreakdown,
    WorkerState,
    WorkerStatus,
)
from .recovery import PermissionRecoveryEngine
from .review_engine import ReviewEngine, create_review_context
from .workers import WorkerManager

logger = logging.getLogger(__name__)


class Coordinator:
    """Main orchestration coordinator."""

    def __init__(
        self,
        session_id: str,
        workspace_dir: Path,
        target_project_dir: Path,
        orchestrator_dir: Path,
        user_prompt: str,
    ):
        self.session_id = session_id
        self.workspace_dir = workspace_dir
        self.target_project_dir = target_project_dir
        self.orchestrator_dir = orchestrator_dir
        self.user_prompt = user_prompt

        # Initialize components
        self.worker_manager = WorkerManager(
            workspace_dir, target_project_dir, orchestrator_dir
        )
        self.review_engine = ReviewEngine(workspace_dir)
        self.recovery_engine = PermissionRecoveryEngine(
            workspace_dir, target_project_dir, orchestrator_dir
        )

        # Session state
        self.session = SessionState(
            session_id=session_id,
            workspace_dir=str(workspace_dir),
            target_project_dir=str(target_project_dir),
            user_prompt=user_prompt,
            workers={},
        )

        self.is_running = False
        self.is_paused = False

    def decompose_task(self, user_prompt: str) -> TaskBreakdown:
        """Break down user task into 3 agent assignments."""
        logger.info("Decomposing task into agent assignments")

        # Gemini task - Architecture & Design (60-70% load)
        gemini_task = TaskAssignment(
            agent=AgentName.GEMINI,
            role="architect_designer",
            responsibilities=[
                "Analyze entire codebase structure and dependencies",
                "Design comprehensive architecture and system changes",
                "Create detailed technical specifications",
                "Identify all affected components and integration points",
                "Suggest optimization opportunities and refactoring needs",
                "Document design decisions and rationale",
            ],
            deliverables=[
                "Architecture design document",
                "Component interaction diagrams",
                "Technical specification for implementation",
                "List of files to be created/modified",
                "API contracts and interfaces",
            ],
            complexity="HIGH",
            estimated_tokens="8000-10000",
        )

        # Claude task - Code Implementation (60-70% load)
        claude_task = TaskAssignment(
            agent=AgentName.CLAUDE,
            role="code_writer_implementer",
            responsibilities=[
                "Implement code based on Gemini's architecture",
                "Write all production code and test suites",
                "Perform file operations (create, modify, delete)",
                "Integrate components according to spec",
                "Execute build, test, and validation commands",
                "Handle complex refactoring tasks",
            ],
            deliverables=[
                "Production code implementations",
                "Comprehensive test suites",
                "Integration code",
                "Build and test results",
                "Refactored code (if needed)",
            ],
            complexity="HIGH",
            estimated_tokens="8000-10000",
        )

        # Codex task - Review & Problem Solving (10-20% load)
        codex_task = TaskAssignment(
            agent=AgentName.CODEX,
            role="problem_solver_reviewer",
            responsibilities=[
                "Review Gemini's architecture for potential issues",
                "Review Claude's implementation for bugs and quality",
                "Validate integration points are correct",
                "Solve specific, well-defined technical problems",
                "Provide focused feedback and recommendations",
            ],
            deliverables=[
                "Brief review reports (200 words max)",
                "Specific problem solutions",
                "Validation results",
                "Integration checks",
            ],
            complexity="LOW",
            estimated_tokens="2000-3000",
        )

        breakdown = TaskBreakdown(
            gemini=gemini_task,
            claude=claude_task,
            codex=codex_task,
            user_prompt=user_prompt,
            session_id=self.session_id,
        )

        logger.info("Task breakdown complete")
        return breakdown

    def format_task_prompt(self, assignment: TaskAssignment, user_prompt: str) -> str:
        """Format task prompt for an agent."""
        prompt = f"""TASK: {assignment.role.replace('_', ' ').title()}

USER REQUEST: {user_prompt}

RESPONSIBILITIES:
{chr(10).join(f'- {r}' for r in assignment.responsibilities)}

DELIVERABLES:
{chr(10).join(f'- {d}' for d in assignment.deliverables)}

COMPLEXITY: {assignment.complexity}
ESTIMATED TOKENS: {assignment.estimated_tokens}

Please emit JSON events for progress tracking:
- {{"type": "milestone", "payload": {{"text": "Major phase complete"}}}}
- {{"type": "progress", "payload": {{"text": "Working...", "progress": 50}}}}
- {{"type": "blocker", "payload": {{"text": "Blocked on X"}}}}
- {{"type": "finding", "payload": {{"text": "Discovered Y"}}}}

Begin work now.
"""
        return prompt

    def launch_all_workers(self, breakdown: TaskBreakdown) -> None:
        """Launch all worker agents."""
        logger.info("Launching all workers")

        # Prepare environments
        for agent_name in [AgentName.GEMINI, AgentName.CODEX, AgentName.CLAUDE]:
            self.recovery_engine.prepare_worker_environment(agent_name)

        # Launch Gemini
        try:
            gemini_prompt = self.format_task_prompt(breakdown.gemini, breakdown.user_prompt)
            gemini_worker = self.worker_manager.launch_worker(AgentName.GEMINI, gemini_prompt)
            self.session.workers[AgentName.GEMINI] = gemini_worker.state
            logger.info("Gemini worker launched")
        except Exception as e:
            logger.error(f"Failed to launch Gemini: {e}")

        # Launch Claude
        try:
            claude_prompt = self.format_task_prompt(breakdown.claude, breakdown.user_prompt)
            claude_worker = self.worker_manager.launch_worker(AgentName.CLAUDE, claude_prompt)
            self.session.workers[AgentName.CLAUDE] = claude_worker.state
            logger.info("Claude worker launched")
        except Exception as e:
            logger.error(f"Failed to launch Claude: {e}")

        # Launch Codex
        try:
            codex_prompt = self.format_task_prompt(breakdown.codex, breakdown.user_prompt)
            codex_worker = self.worker_manager.launch_worker(AgentName.CODEX, codex_prompt)
            self.session.workers[AgentName.CODEX] = codex_worker.state
            logger.info("Codex worker launched")
        except Exception as e:
            logger.error(f"Failed to launch Codex: {e}")

    def monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Starting monitoring loop")
        self.is_running = True

        while self.is_running and not self.is_paused:
            # Check for events from all workers
            all_events = self.worker_manager.get_all_events()

            # Update worker states from parsed events
            self._update_worker_states_from_events(all_events)

            # Check for permission errors and attempt recovery
            for agent_name, events in all_events.items():
                worker = self.worker_manager.get_worker(agent_name)
                if worker:
                    error_type = self.recovery_engine.check_for_errors(worker, events)
                    if error_type:
                        logger.warning(
                            f"Detected error in {agent_name.value}: {error_type}"
                        )
                        recovery_action = self.recovery_engine.attempt_recovery(worker, error_type)
                        if recovery_action:
                            self.session.recovery_actions.append(recovery_action)

            # Check if review should be triggered
            if self.review_engine.should_trigger_review(all_events):
                self.conduct_peer_review(all_events)

            # Check if all workers are complete
            if self.check_completion():
                logger.info("All workers complete")
                self.is_running = False
                self.session.is_complete = True
                break

            # Sleep before next iteration
            time.sleep(5)

        logger.info("Monitoring loop ended")

    def _update_worker_states_from_events(self, all_events: Dict[AgentName, List[Event]]) -> None:
        """Update worker states based on parsed events."""
        for agent_name, events in all_events.items():
            if agent_name not in self.session.workers:
                continue

            worker_state = self.session.workers[agent_name]
            worker = self.worker_manager.get_worker(agent_name)

            def sync_progress(value: int) -> None:
                new_progress = max(worker_state.progress, value)
                worker_state.progress = new_progress
                if worker:
                    worker.state.progress = new_progress

            def sync_status(status: WorkerStatus) -> None:
                worker_state.status = status
                if worker:
                    worker.state.status = status

            # Process each event
            for event in events:
                # Update last event
                worker_state.last_event = event

                # Update progress from event payload
                if event.payload.progress is not None:
                    sync_progress(event.payload.progress)

                # Update status based on event type
                if event.type == EventType.PROGRESS:
                    sync_status(WorkerStatus.RUNNING)
                elif event.type == EventType.STATUS:
                    sync_status(WorkerStatus.RUNNING)
                elif event.type == EventType.BLOCKER:
                    sync_status(WorkerStatus.BLOCKED)
                elif event.type == EventType.ERROR:
                    worker_state.error_count += 1
                    if "blocker" in event.payload.text.lower():
                        sync_status(WorkerStatus.BLOCKED)
                elif event.type == EventType.MILESTONE:
                    # Calculate progress based on milestones
                    sync_progress(min(worker_state.progress + 20, 90))
                elif event.type == EventType.RECOVERY:
                    sync_status(WorkerStatus.RECOVERING)

                # Check for completion indicators
                if "complete" in event.payload.text.lower() or "done" in event.payload.text.lower():
                    sync_status(WorkerStatus.COMPLETED)
                    sync_progress(100)

            # Update worker process status
            if worker:
                if not worker.is_running():
                    if worker_state.status == WorkerStatus.RUNNING:
                        # Worker stopped - check if completed or failed
                        if worker_state.progress >= 90:
                            sync_status(WorkerStatus.COMPLETED)
                        else:
                            sync_status(WorkerStatus.FAILED)

                # Keep process state in sync with session state
                worker.state.progress = worker_state.progress
                worker.state.status = worker_state.status
                worker.state.last_event = worker_state.last_event
                worker.state.error_count = worker_state.error_count

    def conduct_peer_review(self, all_events: Dict[AgentName, List[Event]]) -> None:
        """Conduct peer review cycle with full decision tree."""
        logger.info("Conducting peer review")

        # Create review context
        context = create_review_context(all_events)

        # Create review requests for each agent to review others
        reviews = []

        # Gemini reviews Claude's implementation
        if AgentName.GEMINI in self.worker_manager.workers and AgentName.CLAUDE in self.worker_manager.workers:
            gemini_review_request = self.review_engine.create_review_request(
                reviewer=AgentName.GEMINI,
                targets=[AgentName.CLAUDE],
                focus="Review Claude's code implementation for quality, correctness, and adherence to architecture",
                context=context
            )
            # For now, simulate review response (in production, would send to agent)
            gemini_review = self._simulate_review_response(
                AgentName.GEMINI, AgentName.CLAUDE, all_events.get(AgentName.CLAUDE, [])
            )
            if gemini_review:
                reviews.append(gemini_review)

        # Codex reviews Gemini's architecture
        if AgentName.CODEX in self.worker_manager.workers and AgentName.GEMINI in self.worker_manager.workers:
            codex_review_request = self.review_engine.create_review_request(
                reviewer=AgentName.CODEX,
                targets=[AgentName.GEMINI],
                focus="Review Gemini's architecture for potential issues and design flaws",
                context=context
            )
            codex_review = self._simulate_review_response(
                AgentName.CODEX, AgentName.GEMINI, all_events.get(AgentName.GEMINI, [])
            )
            if codex_review:
                reviews.append(codex_review)

        # Codex reviews Claude's implementation
        if AgentName.CODEX in self.worker_manager.workers and AgentName.CLAUDE in self.worker_manager.workers:
            codex_claude_review = self.review_engine.create_review_request(
                reviewer=AgentName.CODEX,
                targets=[AgentName.CLAUDE],
                focus="Review Claude's implementation for bugs and quality issues",
                context=context
            )
            codex_claude = self._simulate_review_response(
                AgentName.CODEX, AgentName.CLAUDE, all_events.get(AgentName.CLAUDE, [])
            )
            if codex_claude:
                reviews.append(codex_claude)

        # Evaluate all reviews and make a decision using the 4-rule decision tree
        if reviews:
            decision = self.review_engine.evaluate_reviews(reviews)
            self.session.decisions.append(decision)
            logger.info(f"Review decision: {decision.action.value} - {decision.reason}")

            # Take action based on decision
            if decision.action == Action.STOP_AND_ESCALATE:
                logger.warning("STOPPING orchestration due to blockers")
                self.pause()
            elif decision.action == Action.PAUSE_AND_CLARIFY:
                logger.warning("PAUSING orchestration for clarification")
                self.pause()
            elif decision.action == Action.LOG_WARNING:
                logger.warning(f"Continuing with warning: {decision.reason}")
        else:
            # No reviews - continue
            from .models import OrchestratorDecision, Action
            decision = OrchestratorDecision(
                action=Action.CONTINUE,
                reason="No reviews to evaluate",
                next_steps="Continue monitoring",
            )
            self.session.decisions.append(decision)
            logger.info("No reviews conducted - continuing")

    def _simulate_review_response(
        self, reviewer: AgentName, target: AgentName, target_events: List[Event]
    ) -> Optional['PeerReview']:
        """
        Simulate a review response by analyzing target agent's events.
        In production, this would send a request to the reviewer agent and parse the response.
        """
        from .models import Verdict, PeerReview

        # Analyze events to determine verdict
        error_events = [e for e in target_events if e.type == EventType.ERROR]
        blocker_events = [e for e in target_events if e.type == EventType.BLOCKER]

        verdict = Verdict.APPROVED
        issues = []
        recommendations = []

        # Check for blockers
        if blocker_events:
            verdict = Verdict.BLOCKER
            issues = [e.payload.text for e in blocker_events[:3]]  # Top 3
            recommendations.append("Address blocker issues before continuing")

        # Check for multiple errors
        elif len(error_events) >= 3:
            verdict = Verdict.CONCERNS
            issues = [e.payload.text for e in error_events[:3]]  # Top 3
            recommendations.append("Investigate and fix error patterns")

        # Minor concerns
        elif len(error_events) > 0:
            verdict = Verdict.CONCERNS if len(error_events) >= 2 else Verdict.APPROVED
            if verdict == Verdict.CONCERNS:
                issues = [e.payload.text for e in error_events]
                recommendations.append("Monitor error patterns")

        review = PeerReview(
            reviewer=reviewer,
            target=target,
            verdict=verdict,
            issues=issues,
            recommendations=recommendations
        )

        return review

    def check_completion(self) -> bool:
        """Check if all workers have completed their tasks."""
        if not self.session.workers:
            return False

        # Check if all workers have emitted completion milestone
        all_complete = True
        for agent_name, worker_state in self.session.workers.items():
            if worker_state.status not in [
                WorkerStatus.COMPLETED,
                WorkerStatus.FAILED,
            ]:
                # Check if worker process is still running
                worker = self.worker_manager.get_worker(agent_name)
                if worker and worker.is_running():
                    all_complete = False
                    break

        return all_complete

    def stop(self) -> None:
        """Stop all workers and coordination."""
        logger.info("Stopping coordinator")
        self.is_running = False
        self.worker_manager.stop_all()

    def pause(self) -> None:
        """Pause orchestration."""
        logger.info("Pausing orchestration")
        self.is_paused = True

    def resume(self) -> None:
        """Resume orchestration."""
        logger.info("Resuming orchestration")
        self.is_paused = False

    def get_session_state(self) -> SessionState:
        """Get current session state."""
        return self.session

    def get_summary(self) -> Dict:
        """Get orchestration summary."""
        return {
            "session_id": self.session_id,
            "user_prompt": self.user_prompt,
            "start_time": self.session.start_time.isoformat(),
            "is_complete": self.session.is_complete,
            "workers": {
                name.value: {
                    "status": state.status.value,
                    "progress": state.progress,
                }
                for name, state in self.session.workers.items()
            },
            "reviews": self.review_engine.get_review_summary(),
            "recoveries": self.recovery_engine.get_recovery_summary(),
            "decisions": len(self.session.decisions),
        }


def create_session_id() -> str:
    """Create a unique session ID."""
    from datetime import datetime

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"orch_{timestamp}"
