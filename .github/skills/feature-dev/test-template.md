# Test Template for QA

Use this template to draft test cases that codify acceptance criteria.

```python
"""Tests for [feature name]."""

import pytest
from unittest.mock import patch, MagicMock
import asyncio

# For async Chainlit/LangChain code:
# pytest-asyncio must be installed: uv sync --extra dev


class TestFeatureName:
    """Test suite for [feature]."""

    def test_acceptance_criterion_1(self):
        """
        Test: [AC1 description]
        
        Arrange: Set up preconditions.
        Act: Perform the action.
        Assert: Verify the expected outcome.
        """
        # Arrange
        input_data = ...
        expected_output = ...

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output

    def test_acceptance_criterion_2(self):
        """Test: [AC2 description]"""
        # Arrange
        # Act
        # Assert

    def test_edge_case(self):
        """Test: [Edge case or error handling]"""
        # Arrange
        # Act
        # Assert

    @patch("module.external_api")
    def test_with_mock(self, mock_api):
        """Test: [Feature with mocked external dependency]"""
        # Arrange
        mock_api.return_value = MagicMock(status="ok")

        # Act
        result = function_that_calls_api()

        # Assert
        assert result is not None
        mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_behavior(self):
        """Test: [Async feature] (for Chainlit/LangChain)"""
        # Arrange
        # Act
        result = await async_function()

        # Assert
        assert result is not None


# Guideline: One test per acceptance criterion, plus edge cases.
# No OpenAI API key required — use mocks for LLM calls.
```

## Tips

1. **Test naming:** `test_<acceptance_criterion>_<context>` or `test_<edge_case>`
2. **AAA pattern:** Always use Arrange, Act, Assert
3. **Mocking:** Use `unittest.mock.patch` to mock external APIs (OpenAI, databases, etc.)
4. **Async tests:** Mark with `@pytest.mark.asyncio` and use `await`
5. **Fixtures:** Define reusable setup in `conftest.py`

## Run Locally

```bash
uv sync --extra dev
uv run pytest tests/test_[feature].py -v
```

## Verify Tests Fail (TDD)

Before implementation, tests should fail:
```bash
uv run pytest tests/test_[feature].py -v
# Expected: FAILED tests/test_[feature].py::TestFeatureName::test_acceptance_criterion_1
```

After implementation, tests should pass:
```bash
uv run pytest tests/test_[feature].py -v
# Expected: PASSED tests/test_[feature].py::TestFeatureName::test_acceptance_criterion_1
```
