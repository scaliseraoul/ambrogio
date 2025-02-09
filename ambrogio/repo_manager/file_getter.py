from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple
from interrogate import config, coverage
from .repo_manager import RepoPathManager


@dataclass
class CoverageResult:
    """Result of a docstring coverage analysis."""

    coverage_percentage: float
    missing_count: int


class FileGetter:
    """Class to analyze Python files in the repository for missing docstrings."""

    def __init__(self):
        """Initialize FileGetter with repo path manager."""
        self.repo_manager = RepoPathManager()

    def _get_interrogate_config(self) -> config.InterrogateConfig:
        """Get the standard interrogate configuration.

        Returns:
            InterrogateConfig configured to check only public classes and functions.
        """
        return config.InterrogateConfig(
            ignore_init_method=True,  # Ignore __init__ methods
            ignore_magic=True,  # Ignore magic methods
            ignore_module=True,  # Ignore module docstrings
            ignore_private=True,  # Ignore private objects
            ignore_nested_functions=False,  # Check nested functions
            ignore_nested_classes=False,  # Check nested classes
            ignore_semiprivate=True,  # Ignore _semiprivate objects
        )

    def _run_interrogate(self) -> coverage.InterrogateResults:
        """Run interrogate with standard configuration.

        Returns:
            InterrogateResults containing coverage analysis.
        """
        repo_path = self.repo_manager.path
        conf = self._get_interrogate_config()
        interrogate_coverage = coverage.InterrogateCoverage(
            paths=[str(repo_path)], conf=conf
        )
        return interrogate_coverage.get_coverage()

    def get_coverage_stats(self) -> CoverageResult:
        """Get current docstring coverage statistics for the repository.

        Returns:
            CoverageResult containing the coverage percentage and count of missing docstrings.
        """
        results = self._run_interrogate()
        return CoverageResult(
            coverage_percentage=results.perc_covered, missing_count=results.missing
        )

    def get_files_without_docstrings(
        self, min_coverage: float = 100.0
    ) -> Dict[str, float]:
        """Find Python files that don't meet the docstring coverage threshold.

        Args:
            min_coverage: Minimum required docstring coverage percentage (0-100).
                         Default is 100.0, meaning all functions/classes need docstrings.

        Returns:
            Dictionary mapping file paths (relative to repo root) to their docstring
            coverage percentage for files below the threshold.
        """
        results = self._run_interrogate()

        # Print overall statistics
        initial_stats = CoverageResult(
            coverage_percentage=results.perc_covered, missing_count=results.missing
        )
        print(f"Initial Coverage: {initial_stats.coverage_percentage:.1f}%")
        print(f"Objects missing docstrings: {initial_stats.missing_count}")

        # Filter files below threshold and convert to relative paths
        files_below_threshold = {}
        for file_result in results.file_results:
            if file_result.perc_covered < min_coverage:
                rel_path = self.repo_manager.get_relative_path(file_result.filename)
                files_below_threshold[str(rel_path)] = file_result.perc_covered

        return files_below_threshold
