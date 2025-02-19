import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from litellm import completion


class AmbrogioTestGenerator:
    """Generates test cases for uncovered code using LLM."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        max_api_calls: int = 12,
        api_base: Optional[str] = None,
    ):
        """Initialize the test generator.

        Args:
            api_key: API key for the LLM provider
            model: Model to use for generating tests
            max_api_calls: Maximum number of API calls to make
            api_base: Optional base URL for the API endpoint
        """
        self.api_key = api_key
        self.model = model
        self.max_api_calls = max_api_calls
        self.api_base = api_base
        self.api_calls = 0

    def generate_test_file(
        self, source_file: Path, missing_lines: List[int]
    ) -> Tuple[str, str]:
        """Generate a test file for uncovered code.

        Args:
            source_file: Path to the source file
            missing_lines: List of line numbers lacking coverage

        Returns:
            Tuple containing the test file path and generated test content
        """
        if self.api_calls >= self.max_api_calls:
            return "", "Maximum API calls reached"

        # Read the source file
        with open(source_file, "r") as f:
            source_code = f.read()

        # Parse the source code
        tree = ast.parse(source_code)

        # Extract relevant code context
        context = self._extract_context(tree, source_code, missing_lines)
        if not context:
            return "", "No testable code found in uncovered lines"

        # Generate test file path
        test_dir = source_file.parent / "tests"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / f"test_{source_file.name}"

        # Generate test content
        test_content = self._generate_test_content(source_file.name, context)

        return str(test_file), test_content

    def _extract_context(
        self, tree: ast.AST, source_code: str, missing_lines: List[int]
    ) -> List[Dict]:
        """Extract code context for missing lines.

        Args:
            tree: AST of the source file
            source_code: Source code content
            missing_lines: List of uncovered line numbers

        Returns:
            List of dictionaries containing function/class context
        """
        context = []
        missing_set = set(missing_lines)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                try:
                    start_line = node.lineno
                    end_line = self._get_node_end_line(node, source_code)

                    # Check if any missing lines are in this node
                    node_lines = set(range(start_line, end_line + 1))
                    if node_lines & missing_set:
                        node_source = self._get_node_source(node, source_code)
                        if node_source:  # Only add if we got valid source
                            context.append(
                                {
                                    "type": type(node).__name__,
                                    "name": node.name,
                                    "code": node_source,
                                    "missing_lines": sorted(node_lines & missing_set),
                                }
                            )
                except (AttributeError, ValueError, TypeError):
                    continue  # Skip nodes we can't process

        return context

    def _get_node_end_line(self, node: ast.AST, source_code: str) -> int:
        """Get the end line number for an AST node.

        Args:
            node: AST node
            source_code: Complete source code

        Returns:
            End line number for the node
        """
        try:
            lines = source_code.splitlines()
            start_line = node.lineno - 1
            # Find the next non-empty line after the node's body
            for i in range(start_line + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith(
                    " " * (len(lines[start_line]) - len(lines[start_line].lstrip()))
                ):
                    return i - 1
            return len(lines) - 1
        except AttributeError:
            return node.lineno

    def _get_node_source(self, node: ast.AST, source_code: str) -> str:
        """Get source code for an AST node.

        Args:
            node: AST node
            source_code: Complete source code

        Returns:
            Source code for the node
        """
        try:
            start_line = node.lineno - 1
            end_line = self._get_node_end_line(node, source_code)

            lines = source_code.splitlines()
            node_lines = lines[start_line : end_line + 1]

            # Preserve indentation
            if node_lines:
                first_line = node_lines[0]
                indent = len(first_line) - len(first_line.lstrip())
                node_lines = [line[indent:] for line in node_lines]

            return "\n".join(node_lines)
        except (AttributeError, IndexError):
            return ""  # Return empty string if we can't get the source

    def _generate_test_content(self, source_file: str, context: List[Dict]) -> str:
        """Generate test content using LLM.

        Args:
            source_file: Name of the source file
            context: List of code contexts to generate tests for

        Returns:
            Generated test content
        """
        if not context:
            return ""

        prompt = f"""Generate pytest test cases for {source_file}. Focus on testing lines {[c["missing_lines"] for c in context]}.

Code to test:
{self._format_context(context)}

Requirements:
1. ONLY output valid Python code, no explanations or markdown
2. Start with imports (pytest and the module being tested)
3. Use pytest fixtures where needed
4. Include positive and negative test cases
5. Add docstrings explaining each test
6. Use descriptive names: test_<function>_<scenario>
7. Include edge cases and boundary tests
8. Maintain proper indentation
9. DO NOT use markdown code blocks or any other formatting
10. DO NOT include any explanatory text, ONLY output the test code"""

        try:
            response = completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test generator. Only output valid Python code without any explanations or markdown formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                api_key=self.api_key,
                api_base=self.api_base,
            )
            self.api_calls += 1

            test_content = response.choices[0].message.content.strip()

            # Remove any markdown code blocks
            test_content = (
                test_content.replace("```python", "").replace("```", "").strip()
            )

            # Add imports if not present
            imports = []
            if "import pytest" not in test_content:
                imports.append("import pytest")
            module_import = f"from {Path(source_file).stem} import *"
            if module_import not in test_content:
                imports.append(module_import)

            if imports:
                test_content = "\n".join(imports) + "\n\n" + test_content

            return test_content

        except Exception as e:
            return f"# Error generating tests: {str(e)}"

    def _format_context(self, context: List[Dict]) -> str:
        """Format code context for the prompt.

        Args:
            context: List of code contexts

        Returns:
            Formatted context string
        """
        formatted = []
        for item in context:
            formatted.append(f"# {item['type']} {item['name']}")
            formatted.append(f"# Missing coverage on lines: {item['missing_lines']}")
            formatted.append(item["code"])
            formatted.append("")

        return "\n".join(formatted)
