from dataclasses import dataclass
from typing import Dict

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

    def get_files_and_coverage(
        self, min_coverage: float = 100.0
    ) -> (Dict[str, float], float):
        """Retrieve files with coverage below a specified threshold and overall coverage percentage.

        Args:
            min_coverage (float): The minimum coverage percentage threshold. Files with coverage below this
                                  value will be included in the results. Defaults to 100.0.

        Returns:
            Tuple[Dict[str, float], float]: A dictionary mapping file paths to their coverage percentages
                                             for files below the threshold, and the overall coverage percentage
                                             of the results."""

        results = self._run_interrogate()

        # Collect files below threshold
        files_below_threshold = []
        for file_result in results.file_results:
            if file_result.perc_covered < min_coverage:
                rel_path = self.repo_manager.get_relative_path(file_result.filename)
                files_below_threshold.append((str(rel_path), file_result.perc_covered))

        # Sort by coverage percentage (ascending)
        files_below_threshold.sort(key=lambda x: x[1])

        # Convert to dictionary maintaining the sorted order
        return dict(files_below_threshold), results.perc_covered
