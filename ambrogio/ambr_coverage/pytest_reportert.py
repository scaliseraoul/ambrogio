import sys
import traceback
from functools import wraps
from io import StringIO
from typing import List, Optional

from _pytest.reports import CollectReport, TestReport


class PytestReporter:
    """A reporter for capturing and formatting errors encountered during pytest runs.

    This class collects error messages and their associated tracebacks from pytest test
    collection and test execution phases. It stores these errors for later retrieval or
    reporting.

    Attributes:
        errors (List[str]): A list of formatted error messages.
        captured_output (StringIO): A buffer for capturing output during test execution.

    Methods:
        _format_error(error_msg: str, tb: Optional[str] = None) -> str:
            Formats an error message with an optional traceback.

        pytest_collectreport(report: CollectReport):
            Processes errors from test collection reports and stores them.

        pytest_runtest_logreport(report: TestReport):
            Processes errors from individual test run reports and stores them.

        pytest_exception_interact(node, call, report):
            Captures and formats exceptions that occur during test execution."""

    def __init__(self):
        """Initializes a new instance of the class.

        This constructor sets up an empty list to capture error messages
        and initializes a StringIO object to capture output.

        Args:
            None

        Returns:
            None"""
        self.errors: List[str] = []
        self.captured_output = StringIO()

    @staticmethod
    def _format_error(error_msg: str, tb: Optional[str] = None) -> str:
        """Formats an error message with an optional traceback.

        Args:
            error_msg (str): The error message to be formatted.
            tb (Optional[str], optional): The traceback information to include. Defaults to None.

        Returns:
            str: The formatted error message, optionally including the traceback."""
        formatted = f"Error: {error_msg}"
        if tb:
            formatted += f"\nTraceback:\n{tb}"
        return formatted

    def pytest_collectreport(self, report: CollectReport):
        """Process the collection report from pytest.

        This method is called when pytest collects a report. If the report indicates
        a failure, it extracts the error message and traceback, formats the error,
        and appends it to the internal errors list.

        Args:
            report (CollectReport): The report object containing details about the
                collection process, including any failures.

        Returns:
            None"""
        if report.failed:
            tb = getattr(report.longrepr, "reprtraceback", None)
            error_msg = str(report.longrepr)
            self.errors.append(self._format_error(error_msg, str(tb) if tb else None))

    def pytest_runtest_logreport(self, report: TestReport):
        """Handle the logging of test report results.

        This method processes the test report and captures error messages
        for failed tests. If the test has failed, it extracts the error message
        and the traceback, if available, and appends a formatted error entry
        to the errors list.

        Args:
            report (TestReport): The report object containing the test result
                                 information, including failure status and
                                 details.

        Returns:
            None"""
        if report.failed:
            if hasattr(report.longrepr, "reprcrash"):
                error_msg = report.longrepr.reprcrash.message
                tb = str(report.longrepr)
            else:
                error_msg = str(report.longrepr)
                tb = None
            self.errors.append(self._format_error(error_msg, tb))

    def pytest_exception_interact(self, node, call, report):
        """Handle exceptions during pytest interactions.

        This method processes exceptions raised during test execution, formats
        the error message and traceback, and appends the formatted error to a list of errors.

        Args:
            node: The test node where the exception occurred.
            call: The call object containing information about the test execution.
            report: The report object that captures the result of the test.

        Returns:
            None"""
        if call.excinfo:
            error_msg = str(call.excinfo.value)
            tb = "".join(traceback.format_tb(call.excinfo.tb))
            self.errors.append(self._format_error(error_msg, tb))


def silence_stdout(func):
    """Decorator that suppresses standard output and error for a given function.

    This decorator redirects `stdout` and `stderr` to prevent any output from being printed to the console while the decorated function is executing. It restores the original `stdout` and `stderr` after the function completes, regardless of success or failure.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: A wrapper function that suppresses output during execution of the decorated function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wraps a function to capture its standard output and error.

        This decorator temporarily redirects the standard output (stdout) and
        standard error (stderr) streams to StringIO objects, allowing for
        capturing any output generated by the wrapped function. After the
        function execution, the original stdout and stderr are restored.

        Args:
            *args: Positional arguments passed to the wrapped function.
            **kwargs: Keyword arguments passed to the wrapped function.

        Returns:
            The return value of the wrapped function.

        Notes:
            Any output written to stdout or stderr during the execution of
            the wrapped function will be captured and can be accessed
            from the StringIO objects."""
        # Redirect stdout/stderr
        stdout = StringIO()
        stderr = StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Restore stdout/stderr
            sys.stdout, sys.stderr = old_stdout, old_stderr

    return wrapper
