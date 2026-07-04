"""Tests for the TaskClassifier module."""

from __future__ import annotations

import pytest

from arbiterx.router.classifier import ClassifiedTask, TaskClassifier, TaskType


class TestTaskClassifier:
    """Tests for TaskClassifier task string classification."""

    @pytest.fixture
    def classifier(self) -> TaskClassifier:
        """Create a TaskClassifier instance."""
        return TaskClassifier()

    @pytest.mark.parametrize(
        ("task_string", "expected_type"),
        [
            ("fix the bug in the login handler", TaskType.DEBUGGING),
            ("there's an error when users try to register", TaskType.DEBUGGING),
            ("debug the failing test in auth module", TaskType.DEBUGGING),
            ("add a new endpoint for user profiles", TaskType.CODE_GENERATION),
            ("implement pagination for the list API", TaskType.CODE_GENERATION),
            ("create a notification system", TaskType.CODE_GENERATION),
            ("refactor the database connection pool", TaskType.REFACTORING),
            ("clean up the utils module", TaskType.REFACTORING),
            ("extract the validation logic into a separate class", TaskType.REFACTORING),
            ("explain how the caching layer works", TaskType.EXPLANATION),
            ("what does the middleware do?", TaskType.EXPLANATION),
            ("walk me through the auth flow", TaskType.EXPLANATION),
        ],
    )
    def test_classifies_known_tasks(
        self,
        classifier: TaskClassifier,
        task_string: str,
        expected_type: TaskType,
    ) -> None:
        """Known task descriptions should map to the correct TaskType."""
        result = classifier.classify(task_string)
        assert result.task_type == expected_type

    def test_classify_returns_classified_task(self, classifier: TaskClassifier) -> None:
        """classify() should always return a ClassifiedTask instance."""
        result = classifier.classify("do something with the code")
        assert isinstance(result, ClassifiedTask)
        assert isinstance(result.task_type, TaskType)

    def test_classify_is_case_insensitive(self, classifier: TaskClassifier) -> None:
        """Classification should not depend on casing."""
        lower = classifier.classify("fix the bug in auth")
        upper = classifier.classify("FIX THE BUG IN AUTH")
        assert lower.task_type == upper.task_type
