from pathlib import Path
from typing import Optional, Union
import os


class RepoPathManager:
    """Singleton manager for handling repository paths.

    This class provides functionality to initialize, retrieve, and manipulate
    the path to a repository, ensuring that it is a valid git repository or
    contains Python files. It supports both explicit path initialization and
    automatic detection from the environment or local directory structure.

    Methods:
        initialize(path: Optional[str] = None) -> None:
            Initializes the repository path.

        path() -> Path:
            Returns the repository root path.

        get_relative_path(file_path: Union[str, Path]) -> Path:
            Returns the path relative to the repository root.

        get_absolute_path(relative_path: Union[str, Path]) -> Path:
            Converts a repository-relative path to an absolute path.

    Raises:
        ValueError: If the repository path is not valid or has not been
        initialized properly."""

    _instance: Optional["RepoPathManager"] = None

    def __new__(cls) -> "RepoPathManager":
        """Create and return a singleton instance of RepoPathManager.

        If an instance of RepoPathManager does not already exist, it creates
        one and initializes the _repo_path attribute to None. If an instance
        already exists, it returns that instance.

        Args:
            cls (type): The class being instantiated.

        Returns:
            RepoPathManager: The singleton instance of RepoPathManager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._repo_path: Optional[Path] = None
        return cls._instance

    def initialize(self, path: Optional[str] = None) -> None:
        """Initialize the repository path.

        Args:
            path: Optional explicit path to the repository. If None, will attempt to
                 detect from environment or local directory.

        Raises:
            ValueError: If the path doesn't exist, isn't a git repository, or doesn't contain Python files.
        """
        if path:
            # Convert to absolute path and resolve any symlinks
            repo_path = Path(path).resolve()

            # Verify path exists
            if not repo_path.exists():
                raise ValueError(f"Path does not exist: {repo_path}")
            if not repo_path.is_dir():
                raise ValueError(f"Path is not a directory: {repo_path}")

            # Check if it's a git repository or contains Python files
            has_git = (repo_path / ".git").exists()
            has_python = any(repo_path.glob("**/*.py"))

            if has_git or has_python:
                self._repo_path = repo_path
            else:
                raise ValueError(
                    f"Path {repo_path} is neither a git repository nor contains Python files"
                )
        else:
            # GitHub Actions environment
            if "GITHUB_WORKSPACE" in os.environ:
                self._repo_path = Path(os.environ["GITHUB_WORKSPACE"])
                return

            # Try to find git repository from current directory
            current_path = Path.cwd()
            while current_path != current_path.parent:
                if (current_path / ".git").exists():
                    self._repo_path = current_path
                    return
                current_path = current_path.parent

            # If no git repo found, check if current directory has Python files
            cwd = Path.cwd()
            if any(cwd.glob("**/*.py")):
                self._repo_path = cwd
            else:
                raise ValueError(
                    "Current directory is not in a git repository and contains no Python files"
                )

    @property
    def path(self) -> Path:
        """Get the repository root path.

        Returns:
            Path object pointing to repository root.

        Raises:
            ValueError: If path hasn't been initialized.
        """
        if self._repo_path is None:
            raise ValueError("Repository path not initialized")
        return self._repo_path

    def get_relative_path(self, file_path: Union[str, Path]) -> Path:
        """Get path relative to repository root.

        Args:
            file_path: Absolute or relative path to convert

        Returns:
            Path relative to repository root

        Raises:
            ValueError: If path is outside repository
        """
        abs_path = Path(file_path).resolve()
        try:
            return abs_path.relative_to(self.path)
        except ValueError:
            raise ValueError(f"Path {file_path} is outside repository")

    def get_absolute_path(self, relative_path: Union[str, Path]) -> Path:
        """Convert repository-relative path to absolute path.

        Args:
            relative_path: Path relative to repository root

        Returns:
            Absolute path
        """
        return self.path / Path(relative_path)
