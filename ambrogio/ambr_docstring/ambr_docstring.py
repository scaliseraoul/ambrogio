from pathlib import Path
from typing import Dict

import libcst as cst
from openai import OpenAI

from ambrogio.repo_manager import FileGetter, RepoPathManager
from .node_collector import NodeCollector


class DocstringTransformer(cst.CSTTransformer):
    """Transform AST to add docstrings to functions and classes."""

    def __init__(self, docstring_map: Dict[str, str]):
        """Initialize transformer with docstring mapping.

        Args:
            docstring_map: Mapping of function/class names to their generated docstrings
        """
        self.docstring_map = docstring_map

    def _make_docstring(self, docstring: str) -> cst.SimpleStatementLine:
        """Create a docstring node."""
        # Extract just the docstring part from the code block
        docstring = docstring.split('"""')[1].split('"""')[0].strip()
        return cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(value=f'"""{docstring}"""'))]
        )

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        """Process a class definition node to potentially add a docstring.

    If the class defined by `original_node` has a corresponding docstring 
    in the `docstring_map` and `updated_node` does not already have a 
    docstring, this method will add the appropriate docstring to 
    `updated_node`.

    Args:
        original_node (cst.ClassDef): The original class definition node.
        updated_node (cst.ClassDef): The updated class definition node.

    Returns:
        cst.CSTNode: The updated class definition node, potentially with a 
        new docstring added."""
        qualified_name = original_node.name.value
        if qualified_name in self.docstring_map and not self._has_docstring(updated_node):
            print(f"  Adding docstring to class {qualified_name}")
            return self._add_docstring(updated_node, self.docstring_map[qualified_name])
        return updated_node

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.CSTNode:
        """Adds a docstring to a function definition if it is missing and a corresponding 
    docstring exists in the docstring map.

    This method checks if the original function definition has a name that 
    exists in the docstring map. If it does, and the updated function definition 
    lacks a docstring, it adds the appropriate docstring from the map.

    Args:
        original_node (cst.FunctionDef): The original function definition node.
        updated_node (cst.FunctionDef): The updated function definition node.

    Returns:
        cst.CSTNode: The updated function definition node, potentially with a new docstring."""
        qualified_name = original_node.name.value
        if qualified_name in self.docstring_map and not self._has_docstring(updated_node):
            print(f"  Adding docstring to function {qualified_name}")
            return self._add_docstring(updated_node, self.docstring_map[qualified_name])
        return updated_node

    def _has_docstring(self, node: cst.CSTNode) -> bool:
        """Check if node already has a docstring."""
        if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
            if node.body.body and isinstance(node.body.body[0], cst.SimpleStatementLine):
                stmt = node.body.body[0]
                if len(stmt.body) == 1 and isinstance(stmt.body[0], cst.Expr):
                    return isinstance(stmt.body[0].value, cst.SimpleString)
        return False

    def _add_docstring(self, node: cst.CSTNode, docstring: str) -> cst.CSTNode:
        """Add docstring to a node."""
        if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
            new_body = [self._make_docstring(docstring)] + list(node.body.body)
            return node.with_changes(body=node.body.with_changes(body=new_body))
        return node


# Default maximum number of OpenAI API calls per run
DEFAULT_MAX_API_CALLS = 12


class AmbrogioDocstring:
    """Main class for fixing missing docstrings using OpenAI."""

    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo", max_api_calls: int = DEFAULT_MAX_API_CALLS):
        """Initialize the docstring fixer.

        Args:
            openai_api_key: OpenAI API key for generating docstrings
            model: OpenAI model to use (default: gpt-3.5-turbo)
            max_api_calls: Maximum number of OpenAI API calls to make (default: 12)
        """
        self.file_getter = FileGetter()
        self.repo_manager = RepoPathManager()
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.max_api_calls = max_api_calls
        self.api_calls_made = 0

    def _generate_docstring(self, code: str, name: str) -> str:
        """Generate docstring using OpenAI API.

        Args:
            code: Source code of the function or class
            name: Name of the function or class

        Returns:
            Generated docstring

        Raises:
            RuntimeError: If maximum API calls limit has been reached
        """

        prompt = f"""Generate a concise but informative docstring for this Python {code}. 
        The docstring should follow Google style and include Args and Returns sections if applicable.
        Focus on explaining what the code does, not how it does it.
        """

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates clear and concise Python docstrings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500  # Increased to allow for longer docstrings
        )

        self.api_calls_made += 1
        
        return response.choices[0].message.content.strip()

    def _fix_file_docstrings(self, file_path: Path) -> None:
        """Fix missing docstrings in a single file.

        Args:
            file_path: Path to the Python file to fix
        """
        # Read the file
        source_code = file_path.read_text()
        tree = cst.parse_module(source_code)

        # First pass: collect nodes that need docstrings
        collector = NodeCollector()
        tree.visit(collector)
        nodes_needing_docstrings = collector.nodes_needing_docstrings
        
        if not nodes_needing_docstrings:
            print("  No missing docstrings found in this file")
            return
            
        print(f"  Found {len(nodes_needing_docstrings)} items needing docstrings")

        docstring_map = {}
        for name, code in nodes_needing_docstrings.items():
            if self.api_calls_made >= self.max_api_calls:
                print(
                    f"Maximum number of API calls ({self.max_api_calls}) reached. "
                    "Increase the limit with --max-api-calls if needed."
                )
                break
            docstring = self._generate_docstring(code, name)
            docstring_map[name] = docstring

        # Second pass: add docstrings
        transformer = DocstringTransformer(docstring_map)
        modified_tree = tree.visit(transformer)

        # Write the modified code back to the file
        modified_code = modified_tree.code
        print(f"  Writing changes to {file_path}...")
        file_path.write_text(modified_code)
        print("  Successfully updated file with new docstrings")


    def run(self) -> None:
        """Run the docstring fixer on all files missing docstrings."""
        initial_stats = self.file_getter.get_coverage_stats()
        files = self.file_getter.get_files_without_docstrings()
        if not files:
            print("No files need docstring improvements!")
            return

        print(f"Files missing docstrings: {len(files)}")

        for file_path, coverage in files.items():
            abs_path = self.repo_manager.get_absolute_path(file_path)
            print(f"\nFixing docstrings in {file_path} (current coverage: {coverage:.1f}%)")
            self._fix_file_docstrings(abs_path)

        # Show coverage improvement
        final_stats = self.file_getter.get_coverage_stats()
        improvement = final_stats.coverage_percentage - initial_stats.coverage_percentage
        
        # Handle improvement calculation when initial coverage was 0
        improvement_str = (
            f"+{improvement:.1f}%" if initial_stats.coverage_percentage > 0
            else "(new coverage)" if improvement > 0
            else "(no improvement)"
        )

        print("\n📊 Coverage Report:")
        print(f"  Objects still missing docstrings: {final_stats.missing_count}")
        print(f"  Coverage: {final_stats.coverage_percentage:.1f}% {improvement_str}")

