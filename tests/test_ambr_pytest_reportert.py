import pytest
from io import StringIO
from typing import List
from ambrogio.ambr_coverage.pytest_reportert import PytestReporter


@pytest.fixture
def reporter():
    """Fixture that provides an instance of PytestReporter.

    This fixture can be used in pytest tests to access a configured
    PytestReporter instance, which can be utilized for reporting test
    results and logs.

    Returns:
        PytestReporter: An instance of the PytestReporter class."""
    return PytestReporter()


def test_pytest_reporter_initialization(reporter):
    """Test the initialization of the pytest reporter.

    This function verifies that the reporter object is initialized correctly
    by checking that its errors attribute is a list and is empty, and that
    its captured_output attribute is an instance of StringIO.

    Args:
        reporter: An instance of the pytest reporter to be tested.

    Raises:
        AssertionError: If the reporter's attributes do not meet the expected conditions."""
    assert isinstance(reporter.errors, List)
    assert reporter.errors == []
    assert isinstance(reporter.captured_output, StringIO)
