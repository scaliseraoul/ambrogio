import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from coverage import Coverage

from ambrogio.repo_manager import RepoPathManager
from .ambr_test_generator import AmbrogioTestGenerator


class CoverageAnalyzer:
    """Analyzes and provides insights about code coverage in Python projects."""

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_api_calls: int = 12,
        api_base: Optional[str] = None,
    ):
        """Initialize the coverage analyzer.

        Args:
            repo_path: Path to the repository root. If not provided, uses current directory.
            api_key: API key for test generation. Required if generating tests.
            model: Model to use for generating tests. Defaults to gpt-4.
            max_api_calls: Maximum number of API calls for test generation.
            api_base: Optional base URL for the API endpoint.
        """
        self.repo_manager = RepoPathManager()
        self.repo_manager.initialize(repo_path)
        self.repo_path = Path(self.repo_manager.path)
        self.coverage = Coverage(
            data_file=str(self.repo_path / ".coverage"),
            config_file=True,
            source=[str(self.repo_path)],
        )

        if api_key:
            self.test_generator = AmbrogioTestGenerator(
                api_key=api_key,
                model=model,
                max_api_calls=max_api_calls,
                api_base=api_base,
            )
        else:
            self.test_generator = None

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
            rel_path = os.path.relpath(filename, str(self.repo_path))
            file_coverage[rel_path] = coverage_percent

        return file_coverage

    def get_uncovered_lines(self, file_path: str) -> List[int]:
        """Get line numbers that are not covered by tests.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of line numbers that lack test coverage
        """
        abs_path = str(self.repo_path / file_path)
        self.coverage.load()

        _, _, _, missing, _ = self.coverage.analysis2(abs_path)
        return missing

    def generate_tests(self, file_path: str) -> Tuple[Optional[str], str]:
        """Generate test cases for uncovered code.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Tuple containing:
            - Path to the generated test file (or None if no tests were generated)
            - Status message or error description
        """
        if not self.test_generator:
            return None, "No API key provided for test generation"

        uncovered_lines = self.get_uncovered_lines(file_path)
        if not uncovered_lines:
            return None, "File has complete test coverage!"

        try:
            source_file = self.repo_path / file_path
            test_file, test_content = self.test_generator.generate_test_file(
                source_file, uncovered_lines
            )

            if test_file and test_content:
                # Create test file
                os.makedirs(os.path.dirname(test_file), exist_ok=True)
                with open(test_file, "w") as f:
                    f.write(test_content)
                return test_file, f"Generated test file: {test_file}"
            else:
                return None, test_content

        except Exception as e:
            return None, f"Error generating tests: {str(e)}"

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
