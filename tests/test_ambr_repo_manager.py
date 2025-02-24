import pytest
from pathlib import Path
from ambrogio.repo_manager.repo_manager import RepoPathManager


@pytest.fixture
def mock_path_exists(mocker):
    """Fixture to mock Path methods for testing.

    This fixture overrides the behavior of certain methods in the `Path` class
    from the `ambrogio.repo_manager.repo_manager` module to simulate a file
    system where a specific path exists and is treated as a directory. It
    allows tests to run without needing actual file system access.

    The following methods are mocked:
        - Path.exists: Always returns True.
        - Path.is_dir: Always returns True.
        - Path.glob: Returns a list containing a mock file ("file.py").
        - Path.resolve: Returns a mock resolved path ("/mock/path").
        - Path.__truediv__: Simulates path joining to return
          ("/mock/path/file.py").

    Args:
        mocker: The pytest-mock fixture used to create the mocks.

    Returns:
        None"""
    mocker.patch("ambrogio.repo_manager.repo_manager.Path.exists", return_value=True)
    mocker.patch("ambrogio.repo_manager.repo_manager.Path.is_dir", return_value=True)
    mocker.patch(
        "ambrogio.repo_manager.repo_manager.Path.glob", return_value=[Path("file.py")]
    )
    mocker.patch(
        "ambrogio.repo_manager.repo_manager.Path.resolve",
        return_value=Path("/mock/path"),
    )
    mocker.patch(
        "ambrogio.repo_manager.repo_manager.Path.__truediv__",
        return_value=Path("/mock/path/file.py"),
    )


def test_initialize_valid_repo(mock_path_exists):
    """Test the initialization of a valid repository path.

    This test verifies that the `RepoPathManager` correctly initializes
    with a specified path and that the path can be retrieved as expected.

    Args:
        mock_path_exists: A mock fixture that simulates the existence of
            the specified path.

    Raises:
        AssertionError: If the initialized path does not match the expected
            path after initialization."""
    RepoPathManager.initialize("/mock/path")
    assert RepoPathManager.path() == Path("/mock/path")
