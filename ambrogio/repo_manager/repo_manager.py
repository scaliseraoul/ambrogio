from pathlib import Path
from typing import Optional, Union


class RepoPathManager:
    """Singleton manager for handling repository paths.

    This class provides functionality to initialize and manage repository paths.
    It follows a simple pattern:
    1. Initialize once with RepoPathManager.initialize(path)
    2. Access from anywhere with RepoPathManager.get_instance()

    Example:
        >>> RepoPathManager.initialize("/path/to/repo")
        >>> manager = RepoPathManager.get_instance()
        >>> manager.path
        Path('/path/to/repo')

    Methods:
        initialize(path: Optional[str] = None) -> None:
            Class method to initialize the repository path.

        get_instance() -> RepoPathManager:
            Get the singleton instance.

        path() -> Path:
            Get the repository root path.

    Raises:
        ValueError: If operations are attempted before initialization."""

    _instance: Optional["RepoPathManager"] = None
    _repo_path: Optional[Path] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "RepoPathManager":
        """Get the singleton instance of RepoPathManager.

        Returns:
            RepoPathManager: The singleton instance.

        Raises:
            ValueError: If the repository path hasn't been initialized.

        Example:
            >>> manager = RepoPathManager.get_instance()
            >>> print(manager.path)  # Access the repository path"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, path: Optional[str] = None) -> None:
        """Initialize the repository path.

        Args:
            path: Optional path to repository root. If not provided, will attempt to detect.

        Raises:
            ValueError: If the path doesn't exist or is not a valid repository.
        """
        if path:
            # Convert to absolute path and resolve any symlinks
            repo_path = Path(path).resolve()

            # Verify path exists
            if not repo_path.exists():
                raise ValueError(f"Path does not exist: {repo_path}")
            if not repo_path.is_dir():
                raise ValueError(f"Path is not a directory: {repo_path}")

            # Check for valid project markers
            has_git = (repo_path / ".git").exists()
            has_poetry = (repo_path / "pyproject.toml").exists()
            has_python = any(
                p
                for p in repo_path.glob("**/*.py")
                if ".venv" not in str(p) and "__pycache__" not in str(p)
            )

            if has_git or has_poetry or has_python:
                cls._repo_path = repo_path
            else:
                raise ValueError(
                    f"Path {repo_path} is not a valid git repository, poetry project, or Python project"
                )
        else:
            # Try to find repository from current directory
            current_path = Path.cwd()
            while current_path != current_path.parent:
                if (current_path / ".git").exists() or (
                    current_path / "pyproject.toml"
                ).exists():
                    cls._repo_path = current_path
                    return
                current_path = current_path.parent

            # If no markers found, check for Python files
            cwd = Path.cwd()
            if any(
                p
                for p in cwd.glob("**/*.py")
                if ".venv" not in str(p) and "__pycache__" not in str(p)
            ):
                cls._repo_path = cwd
            else:
                raise ValueError("Current directory is not a valid repository")

    @classmethod
    def path(cls) -> Path:
        """Get the repository root path.

        Returns:
            Path: The absolute path to the repository root.

        Raises:
            ValueError: If path hasn't been initialized.
        """
        if cls._repo_path is None:
            raise ValueError("Repository path not initialized")
        return cls._repo_path

    @classmethod
    def get_relative_path(cls, file_path: Union[str, Path]) -> Path:
        """Get path relative to repository root.

        Args:
            file_path: Absolute or relative path to convert

        Returns:
            Path: The path relative to the repository root.

        Raises:
            ValueError: If path is outside repository or repo not initialized.
        """
        abs_path = Path(file_path).resolve()
        try:
            return abs_path.relative_to(cls.path())
        except ValueError:
            raise ValueError(f"Path {file_path} is outside repository")

    @classmethod
    def get_absolute_path(cls, relative_path: Union[str, Path]) -> Path:
        """Convert repository-relative path to absolute path.

        Args:
            relative_path: Path relative to repository root

        Returns:
            Path: The absolute path.

        Raises:
            ValueError: If repo path not initialized.
        """
        return cls.path() / Path(relative_path)

    def get_repo_structure(self) -> str:
        """Get a string representation of the repository structure.

        Returns:
            str: A string containing information about the repository structure,
                 including Python files, their exports (classes/functions), and imports.
        """
        import ast
        from typing import Set, List

        def extract_imports(tree: ast.AST) -> Set[str]:
            """Extracts imported module names from an Abstract Syntax Tree (AST).

            This function traverses the given AST and collects all the names of
            modules and symbols that are imported using `import` and `from ... import`
            statements. The imported names are returned as a set to ensure uniqueness.

            Args:
                tree (ast.AST): The root node of the AST to be analyzed.

            Returns:
                Set[str]: A set containing the names of all imported modules and symbols."""
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ""
                    for name in node.names:
                        if module:
                            imports.add(f"{module}.{name.name}")
                        else:
                            imports.add(name.name)
            return imports

        def extract_exports(tree: ast.AST) -> List[str]:
            """Extracts the names of all classes and functions defined in an AST.

            This function traverses an Abstract Syntax Tree (AST) and collects the names of
            all class and function definitions. The extracted names can be used to identify
            the exported members of a module.

            Args:
                tree (ast.AST): The Abstract Syntax Tree to traverse.

            Returns:
                List[str]: A list of names of classes and functions found in the AST."""
            exports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    exports.append(node.name)
            return exports

        structure = []
        structure.append(f"Repository Root: {self.path}")

        # Find all Python files
        for py_file in self.path.rglob("*.py"):
            # Skip virtual environments and hidden directories
            if any(
                part.startswith(".") or part in {"venv", "env", "__pycache__"}
                for part in py_file.parts
            ):
                continue

            try:
                rel_path = self.get_relative_path(py_file)
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the file
                tree = ast.parse(content)

                # Extract information
                imports = extract_imports(tree)
                exports = extract_exports(tree)

                # Add to structure string
                structure.append(f"\nFile: {rel_path}")
                if exports:
                    structure.append("  Exports:")
                    for export in sorted(exports):
                        structure.append(f"    - {export}")
                if imports:
                    structure.append("  Imports:")
                    for import_stmt in sorted(imports):
                        structure.append(f"    - {import_stmt}")

            except Exception as e:
                structure.append(f"\nFile: {rel_path} (Error: {str(e)})")

        return "\n".join(structure)
