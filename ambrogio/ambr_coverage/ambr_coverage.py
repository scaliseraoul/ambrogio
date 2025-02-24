import os
from pathlib import Path
from typing import Dict, List

import pytest
from coverage import Coverage

from ambrogio.repo_manager import RepoPathManager
from .pytest_reportert import silence_stdout


class CoverageAnalyzer:
    """Analyzes and provides insights about code coverage in Python projects."""

    def __init__(self):
        """Initialize the coverage analyzer.

        Args:
            repo_path: Path to the repository root. If not provided, uses current directory.
        """
        self.repo_manager = RepoPathManager.get_instance()
        self.repo_path = self.repo_manager.path()
        self.coverage = Coverage(
            data_file=str(self.repo_path / ".coverage"),
            config_file=True,
            source=[str(self.repo_path)],
        )

    @silence_stdout
    def analyze_coverage(self) -> Dict[str, float]:
        """Run coverage analysis on the project.

        Returns:
            Dict mapping file paths to their coverage percentage
        """
        self.coverage.start()
        self._run_tests()
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

    def _run_tests(self) -> None:
        """Run all tests in the project using pytest's test discovery."""
        # Use pytest's test discovery by pointing it to the project root
        # It will automatically find and run tests following standard conventions
        pytest.main([str(self.repo_path)])
