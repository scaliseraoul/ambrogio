import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from coverage import Coverage

from ambrogio.repo_manager import RepoPathManager
from .ambr_test_generator import AmbrogioTestGenerator
from .pytest_reportert import silence_stdout


class CoverageAnalyzer:
    """Analyzes and provides insights about code coverage in Python projects."""

    def __init__(
        self,
        repo_path: Optional[Path] = None,
    ):
        """Initialize the coverage analyzer.

        Args:
            repo_path: Path to the repository root. If not provided, uses current directory.
        """
        self.repo_manager = RepoPathManager()
        self.repo_manager.initialize(repo_path)
        self.repo_path = Path(self.repo_manager.path)
        self.coverage = Coverage(
            data_file=str(self.repo_path / ".coverage"),
            config_file=True,
            source=[str(self.repo_path)],
        )

        self.test_generator = AmbrogioTestGenerator(base_path=self.repo_path)

    @silence_stdout
    def analyze_coverage(self) -> Dict[str, float]:
        """Run coverage analysis on the project.

        Returns:
            Dict mapping file paths to their coverage percentage
        """
        self.coverage.start()

        # Find and run all test files
        test_files = self._find_test_files()
        for test_file in test_files:
            try:
                self._run_test_file(test_file)
            except Exception as e:
                print(f"Error running tests in {test_file}: {e}")

        self.coverage.stop()
        self.coverage.save()

        # Get coverage data
        self.coverage.load()
        file_coverage = {}

        for filename in self.coverage.get_data().measured_files():
            _, statements, _, missing, _ = self.coverage.analysis2(filename)
            if not statements:
                continue

            executed = len(statements) - len(missing)
            coverage_percent = (executed / len(statements)) * 100
            rel_path = os.path.abspath(filename)
            file_coverage[rel_path] = coverage_percent

        return file_coverage

    def get_uncovered_lines(self, file_path: Path) -> List[int]:
        """Get line numbers that are not covered by tests.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of line numbers that lack test coverage
        """
        self.coverage.load()

        _, _, _, missing, _ = self.coverage.analysis2(str(file_path))
        return missing

    def generate_tests(
        self,
        source_file_path: Path,
        test_execution_error: str = None,
        test_file_path: Path = None,
    ) -> Tuple[Path, str]:
        """Generates a test file for the specified source file based on uncovered lines.

        This method identifies uncovered lines in the provided source file and
        generates a corresponding test file. If a test execution error is specified,
        it is included in the generated test content. The test file is created if it
        does not already exist.

        Args:
            source_file_path (Path): The path to the source file for which tests are to be generated.
            test_execution_error (str, optional): An error message to include in the generated test file, if any.
            test_file_path (Path, optional): The path where the generated test file should be saved.
                                              If not provided, the default location will be used.

        Returns:
            Tuple[Path, str]: A tuple containing the path to the generated test file and its content as a string."""
        uncovered_lines = self.get_uncovered_lines(source_file_path)

        test_file, test_content = self.test_generator.generate_test_file(
            source_file_path=source_file_path,
            uncovered_lines=uncovered_lines,
            test_execution_error=test_execution_error,
            test_file_path=test_file_path,
        )

        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write(test_content)
        return test_file, test_content

    def clean_tests(
        self, test_execution_error: str = None, test_file_path: Path = None
    ) -> Tuple[Path, str]:
        """Cleans and generates a test file based on the provided execution error and file path.

        This method utilizes the test generator to clean the contents of a test file
        and saves the cleaned content to a specified location. It ensures that the
        necessary directories are created if they do not exist.

        Args:
            test_execution_error (str, optional): An optional error message related to the test execution.
            test_file_path (Path, optional): The path to the test file to be cleaned.

        Returns:
            Tuple[Path, str]: A tuple containing the path to the cleaned test file and its content as a string."""

        test_file, test_content = self.test_generator.clean_test_file(
            test_execution_error=test_execution_error, test_file_path=test_file_path
        )

        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, "w") as f:
            f.write(test_content)
        return test_file, test_content

    def _find_test_files(self) -> List[Path]:
        """Find all test files in the project.

        Returns:
            List of paths to test files
        """
        test_files = []
        for python_file in self.repo_path.rglob("test_*.py"):
            if "venv" not in str(python_file):
                test_files.append(python_file)
        return test_files

    def _run_test_file(self, test_file: Path) -> None:
        """Run a single test file.

        Args:
            test_file: Path to the test file to run
        """
        import pytest

        pytest.main([str(test_file)])
