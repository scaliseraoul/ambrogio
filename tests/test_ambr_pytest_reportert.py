import pytest
from io import StringIO
from typing import List
from ambrogio.ambr_coverage.pytest_reportert import PytestReporter


@pytest.fixture
def pytest_reporter():
    """Fixture that provides an instance of the PytestReporter.

    This fixture creates and returns a PytestReporter object, which can be
    used in test cases to report test results and manage output during
    the pytest execution.

    Returns:
        PytestReporter: An instance of the PytestReporter class."""
    return PytestReporter()


def test_pytest_reporter_initialization(pytest_reporter):
    """Tests the initialization of the pytest_reporter.

    This function checks that the `pytest_reporter` object is correctly
    initialized with an empty list for errors and a StringIO object for
    captured output.

    Args:
        pytest_reporter: An instance of the pytest_reporter to be tested.

    Raises:
        AssertionError: If `pytest_reporter.errors` is not a list,
                        if it is not empty, or if `captured_output`
                        is not a StringIO instance."""
    assert isinstance(pytest_reporter.errors, List)
    assert pytest_reporter.errors == []
    assert isinstance(pytest_reporter.captured_output, StringIO)
