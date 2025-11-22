"""Tests for review decision tree logic."""

import pytest
from orchestrator.models import AgentName, Verdict, PeerReview, Action
from orchestrator.review_engine import ReviewEngine
from pathlib import Path


@pytest.fixture
def review_engine():
    """Create a review engine instance."""
    workspace = Path("/tmp/workspace")
    return ReviewEngine(workspace)


def test_single_blocker_triggers_stop(review_engine):
    """Test that a single BLOCKER verdict triggers STOP_AND_ESCALATE."""
    reviews = [
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.GEMINI,
            verdict=Verdict.BLOCKER,
            issues=["Critical architecture flaw"],
            recommendations=["Redesign component X"]
        ),
        PeerReview(
            reviewer=AgentName.GEMINI,
            target=AgentName.CLAUDE,
            verdict=Verdict.APPROVED,
            issues=[],
            recommendations=[]
        ),
    ]

    decision = review_engine.evaluate_reviews(reviews)
    assert decision.action == Action.STOP_AND_ESCALATE


def test_majority_concerns_triggers_pause(review_engine):
    """Test that 2+ CONCERNS verdicts trigger PAUSE_AND_CLARIFY."""
    reviews = [
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.GEMINI,
            verdict=Verdict.CONCERNS,
            issues=["Minor issue 1"],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.GEMINI,
            target=AgentName.CLAUDE,
            verdict=Verdict.CONCERNS,
            issues=["Minor issue 2"],
            recommendations=[]
        ),
    ]

    decision = review_engine.evaluate_reviews(reviews)
    assert decision.action == Action.PAUSE_AND_CLARIFY


def test_single_concern_triggers_warning(review_engine):
    """Test that a single CONCERNS verdict triggers LOG_WARNING."""
    reviews = [
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.GEMINI,
            verdict=Verdict.CONCERNS,
            issues=["Minor issue"],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.GEMINI,
            target=AgentName.CLAUDE,
            verdict=Verdict.APPROVED,
            issues=[],
            recommendations=[]
        ),
    ]

    decision = review_engine.evaluate_reviews(reviews)
    assert decision.action == Action.LOG_WARNING


def test_all_approved_triggers_continue(review_engine):
    """Test that all APPROVED verdicts trigger CONTINUE."""
    reviews = [
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.GEMINI,
            verdict=Verdict.APPROVED,
            issues=[],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.GEMINI,
            target=AgentName.CLAUDE,
            verdict=Verdict.APPROVED,
            issues=[],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.CLAUDE,
            verdict=Verdict.APPROVED,
            issues=[],
            recommendations=[]
        ),
    ]

    decision = review_engine.evaluate_reviews(reviews)
    assert decision.action == Action.CONTINUE


def test_blocker_overrides_concerns(review_engine):
    """Test that BLOCKER takes precedence over CONCERNS."""
    reviews = [
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.GEMINI,
            verdict=Verdict.BLOCKER,
            issues=["Critical issue"],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.GEMINI,
            target=AgentName.CLAUDE,
            verdict=Verdict.CONCERNS,
            issues=["Minor issue"],
            recommendations=[]
        ),
        PeerReview(
            reviewer=AgentName.CODEX,
            target=AgentName.CLAUDE,
            verdict=Verdict.CONCERNS,
            issues=["Another minor issue"],
            recommendations=[]
        ),
    ]

    decision = review_engine.evaluate_reviews(reviews)
    assert decision.action == Action.STOP_AND_ESCALATE


def test_parse_review_response_with_blocker_keyword(review_engine):
    """Test parsing review response with 'blocker' keyword."""
    response_text = "This is a blocker issue that must be fixed immediately."

    review = review_engine.parse_review_response(
        AgentName.CODEX,
        AgentName.GEMINI,
        response_text
    )

    assert review.verdict == Verdict.BLOCKER


def test_parse_review_response_with_concern_keyword(review_engine):
    """Test parsing review response with 'concern' keyword."""
    response_text = "I have a concern about this implementation approach."

    review = review_engine.parse_review_response(
        AgentName.CODEX,
        AgentName.GEMINI,
        response_text
    )

    assert review.verdict == Verdict.CONCERNS


def test_parse_review_response_approved(review_engine):
    """Test parsing review response with no issues."""
    response_text = "Everything looks good. Well done!"

    review = review_engine.parse_review_response(
        AgentName.CODEX,
        AgentName.GEMINI,
        response_text
    )

    assert review.verdict == Verdict.APPROVED


def test_review_summary(review_engine):
    """Test review summary generation."""
    summary = review_engine.get_review_summary()

    assert "total_reviews" in summary
    assert "by_reviewer" in summary
    assert "by_verdict" in summary
    assert "decisions" in summary
