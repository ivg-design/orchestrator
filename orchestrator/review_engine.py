"""Peer review engine for coordinating agent reviews."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    Action,
    AgentName,
    Event,
    EventType,
    OrchestratorDecision,
    PeerReview,
    ReviewRequest,
    Verdict,
)

logger = logging.getLogger(__name__)


class ReviewEngine:
    """Manages peer review system with event-based triggers."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.reviews_dir = workspace_dir / "reviews"
        self.reviews_dir.mkdir(exist_ok=True)
        self.reviews: List[PeerReview] = []
        self.decisions: List[OrchestratorDecision] = []
        self.last_review_time: Optional[datetime] = None
        self.review_counter = 0

    def should_trigger_review(
        self,
        events: Dict[AgentName, List[Event]],
        force: bool = False,
    ) -> bool:
        """Determine if a review should be triggered based on events."""
        if force:
            return True

        # Check for explicit review triggers
        for agent_events in events.values():
            for event in agent_events:
                if event.type in [
                    EventType.MILESTONE,
                    EventType.BLOCKER,
                ]:
                    logger.info(f"Review triggered by {event.type.value} event")
                    return True

                # Check for explicit review request in payload
                if "review" in event.payload.text.lower():
                    logger.info("Review triggered by review request in event")
                    return True

        # Fallback: No events for 15 minutes
        if self.last_review_time is not None:
            time_since_review = datetime.utcnow() - self.last_review_time
            if time_since_review > timedelta(minutes=15):
                logger.info("Review triggered by 15-minute fallback")
                return True

        return False

    def create_review_request(
        self,
        reviewer: AgentName,
        targets: List[AgentName],
        focus: str,
        context: Dict[str, str],
    ) -> ReviewRequest:
        """Create a review request for an agent."""
        request = ReviewRequest(
            reviewer=reviewer,
            targets=targets,
            focus=focus,
            context=context,
            max_words=200,
        )

        logger.info(
            f"Created review request: {reviewer.value} reviewing {[t.value for t in targets]}"
        )

        return request

    def parse_review_response(
        self, reviewer: AgentName, target: AgentName, response_text: str
    ) -> PeerReview:
        """Parse a review response from an agent."""
        # Simple parsing logic - in production, this would be more sophisticated
        verdict = Verdict.APPROVED
        issues = []
        recommendations = []

        # Check for keywords
        response_lower = response_text.lower()

        if "blocker" in response_lower or "critical" in response_lower:
            verdict = Verdict.BLOCKER
        elif "concern" in response_lower or "issue" in response_lower:
            verdict = Verdict.CONCERNS

        # Extract issues and recommendations
        # This is a simplified version - production would use NLP or structured output
        lines = response_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                if "issue" in line.lower() or "problem" in line.lower():
                    issues.append(line[2:])
                elif "recommend" in line.lower() or "suggest" in line.lower():
                    recommendations.append(line[2:])

        review = PeerReview(
            reviewer=reviewer,
            target=target,
            verdict=verdict,
            issues=issues,
            recommendations=recommendations,
        )

        self.reviews.append(review)
        self._save_review(review)

        logger.info(
            f"Parsed review: {reviewer.value} -> {target.value} = {verdict.value}"
        )

        return review

    def evaluate_reviews(self, reviews: List[PeerReview]) -> OrchestratorDecision:
        """Evaluate peer reviews and make a decision."""
        blockers = [r for r in reviews if r.verdict == Verdict.BLOCKER]
        concerns = [r for r in reviews if r.verdict == Verdict.CONCERNS]
        approved = [r for r in reviews if r.verdict == Verdict.APPROVED]

        # RULE 1: Any blocker → STOP
        if len(blockers) > 0:
            decision = OrchestratorDecision(
                action=Action.STOP_AND_ESCALATE,
                reason=f"{len(blockers)} blocker(s) detected",
                next_steps="Present issue to user, await decision",
            )

        # RULE 2: Majority concerns (2+) → PAUSE
        elif len(concerns) >= 2:
            decision = OrchestratorDecision(
                action=Action.PAUSE_AND_CLARIFY,
                reason="Majority have concerns",
                next_steps="Orchestrator clarifies requirements, agents resume",
            )

        # RULE 3: Single concern → LOG_WARNING
        elif len(concerns) == 1:
            decision = OrchestratorDecision(
                action=Action.LOG_WARNING,
                reason="One agent has concerns",
                next_steps="Continue but monitor closely, review again in 10 min",
            )

        # RULE 4: All approved → CONTINUE
        elif len(approved) == len(reviews):
            decision = OrchestratorDecision(
                action=Action.CONTINUE,
                reason="All reviews positive",
                next_steps="Continue work, next review on event trigger",
            )

        else:
            # Default case - continue with warning
            decision = OrchestratorDecision(
                action=Action.LOG_WARNING,
                reason="Mixed or unclear review results",
                next_steps="Continue with caution",
            )

        self.decisions.append(decision)
        self.last_review_time = datetime.utcnow()

        logger.info(f"Decision: {decision.action.value} - {decision.reason}")

        return decision

    def _save_review(self, review: PeerReview) -> None:
        """Save review to disk."""
        self.review_counter += 1
        review_path = self.reviews_dir / f"review_{self.review_counter:03d}.json"

        with open(review_path, "w") as f:
            json.dump(review.to_json_dict(), f, indent=2)

        logger.debug(f"Saved review to {review_path}")

    def get_review_summary(self) -> Dict:
        """Get summary of all reviews."""
        return {
            "total_reviews": len(self.reviews),
            "by_reviewer": self._count_by_reviewer(),
            "by_verdict": self._count_by_verdict(),
            "decisions": [
                {
                    "action": d.action.value,
                    "reason": d.reason,
                    "timestamp": d.timestamp.isoformat(),
                }
                for d in self.decisions
            ],
        }

    def _count_by_reviewer(self) -> Dict[str, int]:
        """Count reviews by reviewer."""
        counts = {}
        for review in self.reviews:
            reviewer = review.reviewer.value
            counts[reviewer] = counts.get(reviewer, 0) + 1
        return counts

    def _count_by_verdict(self) -> Dict[str, int]:
        """Count reviews by verdict."""
        counts = {}
        for review in self.reviews:
            verdict = review.verdict.value
            counts[verdict] = counts.get(verdict, 0) + 1
        return counts

    def get_latest_reviews(self, limit: int = 10) -> List[PeerReview]:
        """Get the latest N reviews."""
        return self.reviews[-limit:]

    def get_latest_decision(self) -> Optional[OrchestratorDecision]:
        """Get the most recent decision."""
        if self.decisions:
            return self.decisions[-1]
        return None


def analyze_work_summary(events: List[Event]) -> str:
    """Analyze events to create a work summary for review context."""
    if not events:
        return "No activity yet"

    # Extract key information from events
    milestones = [e for e in events if e.type == EventType.MILESTONE]
    tasks = [e for e in events if e.type == EventType.TASK]
    findings = [e for e in events if e.type == EventType.FINDING]

    summary_parts = []

    if milestones:
        summary_parts.append(
            f"Completed {len(milestones)} milestone(s): {milestones[-1].payload.text}"
        )

    if tasks:
        summary_parts.append(f"Working on {len(tasks)} task(s): {tasks[-1].payload.text}")

    if findings:
        summary_parts.append(
            f"Found {len(findings)} finding(s): {findings[-1].payload.text}"
        )

    # Get latest progress
    progress_events = [e for e in events if e.payload.progress is not None]
    if progress_events:
        latest_progress = progress_events[-1].payload.progress
        summary_parts.append(f"Progress: {latest_progress}%")

    return " | ".join(summary_parts) if summary_parts else "Working..."


def create_review_context(
    all_events: Dict[AgentName, List[Event]]
) -> Dict[str, str]:
    """Create context dictionary for review requests."""
    context = {}

    for agent_name, events in all_events.items():
        context[f"{agent_name.value}_summary"] = analyze_work_summary(events)

    return context
