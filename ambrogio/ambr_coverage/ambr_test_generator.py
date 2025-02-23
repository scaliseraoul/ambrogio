import os.path
from pathlib import Path
from typing import List, Optional, Tuple

from ambrogio.llm_manager import LLMManager


class AmbrogioTestGenerator:
    """Generates test cases for uncovered code using LLM."""

    def __init__(
        self,
        base_path: Path,
    ):
        """Initialize the test generator.

        Args:
            base_path: Base path for the project
        """
        self.base_path = base_path
        self.llm_manager = LLMManager.get_instance()

    def generate_test_file(
        self,
        source_file_path: Path,
        uncovered_lines: List[int],
        test_execution_error: Optional[str] = None,
        test_file_path: Optional[Path] = None,
    ) -> Tuple[Path, str]:
        """Generates a test file for a given source file based on uncovered lines.

        This method reads the specified source file and generates a test file that aims to cover the lines
        of code that are not yet covered by existing tests. If a test file already exists at the given
        path, it will be read; otherwise, a new test file will be created in the 'tests' directory.

        Args:
            source_file_path (Path): The path to the source file for which to generate tests.
            uncovered_lines (List[int]): A list of line numbers in the source file that are not covered by tests.
            test_execution_error (Optional[str]): An optional error message from previous test executions, if any.
            test_file_path (Optional[Path]): An optional path to an existing test file. If not provided, a new test file will be created.

        Returns:
            Tuple[Path, str]: A tuple containing the path to the generated or existing test file and the generated test content as a string."""

        # Read the source file
        with open(source_file_path, "r") as f:
            source_code = f.read()

        if test_file_path and os.path.exists(test_file_path):
            with open(test_file_path, "r") as f:
                test_code = f.read()
        else:
            # TODO infer this from the repo
            test_dir = self.base_path / "tests"
            test_dir.mkdir(exist_ok=True)
            test_file_path = test_dir / f"test_ambr_{source_file_path.name}"
            test_code = None

        # Generate test content
        test_content = self._generate_test_content(
            source_file_path=source_file_path,
            source_code=source_code,
            uncovered_lines=uncovered_lines,
            test_execution_error=test_execution_error,
            test_file_path=test_file_path,
            test_code=test_code,
        )

        return test_file_path, test_content

    def _generate_test_content(
        self,
        source_file_path: Path,
        source_code: str,
        uncovered_lines: List[int],
        test_execution_error: Optional[str] = None,
        test_file_path: Optional[Path] = None,
        test_code: Optional[str] = None,
    ) -> str:
        """Generate pytest test cases for a given source file based on uncovered lines and optional test execution errors.

        This method constructs a prompt to an AI model to produce valid Python test code that adheres to specified guidelines.
        It ensures that the generated tests focus on uncovered lines in the source code, following best practices for
        naming conventions, import rules, and minimal test design. If there is an error during test execution, it adjusts
        the prompt to include the error details for better test generation.

        Args:
            source_file_path (Path): The path to the source file for which tests are to be generated.
            source_code (str): The actual code from the source file.
            uncovered_lines (List[int]): A list of line numbers in the source code that are not covered by existing tests.
            test_execution_error (Optional[str], optional): An error message from a previous test execution, if any.
            test_file_path (Optional[Path], optional): The path to the test file generated previously.
            test_code (Optional[str], optional): The code content of the previously generated test file.

        Returns:
            str: The generated pytest test cases as a string of valid Python code, or an error message if generation fails."""
        # Find the longest contiguous range of uncovered lines
        contiguous_ranges = []
        current_range = []

        sorted_lines = sorted(uncovered_lines)
        for line in sorted_lines:
            if not current_range or line == current_range[-1] + 1:
                current_range.append(line)
            else:
                if current_range:
                    contiguous_ranges.append(current_range)
                current_range = [line]
        if current_range:
            contiguous_ranges.append(current_range)

        # Select the longest range
        target_range = (
            max(contiguous_ranges, key=len) if contiguous_ranges else sorted_lines
        )
        start_line = target_range[0]
        end_line = target_range[-1]

        base_prompt = f"""Generate a SINGLE pytest test case for {source_file_path}. Focus ONLY on testing lines {start_line}-{end_line}.

{source_file_path} contains this code:
{source_code}

Generate ONE pytest test case with these requirements:

1. IMPORT RULES:
  - Always use full package path (e.g., 'from package.subpackage.module import X')
  - Never use relative imports
  - Only import what exists in the source file

2. FIXTURE SETUP:
  - Define any required fixtures in the same test file
  - For mocking external dependencies, use pytest.fixture and mocker
  - DO NOT use @pytest.mark.usefixtures, pass fixtures as parameters instead
  - Create mock objects using mocker.patch or mocker.Mock()

3. SINGLE TEST FOCUS:
  - Generate exactly ONE test that covers lines {start_line}-{end_line}
  - Test name should clearly indicate what is being tested
  - One or more assertions are allowed if needed for the specific lines

4. Keep test inputs simple:
  - Minimal valid examples
  - Clear expected outputs
  - Avoid overly complex test data

5. Output ONLY valid python code:
  - Include required imports (pytest, unittest.mock if needed)
  - Include fixture definitions
  - Include exactly one test function
  - NO comments or docstrings"""

        if test_execution_error:
            prompt = f"""Fix the test for {source_file_path}, focusing ONLY on lines {start_line}-{end_line}.

Original source code:
{source_code}

Previous test code that failed:
{test_code}

Test execution error:
{test_execution_error}

Generate ONE fixed pytest test case with these requirements:

1. IMPORT RULES:
  - Always use full package path (e.g., 'from package.subpackage.module import X')
  - Never use relative imports
  - Only import what exists in the source file

2. FIXTURE SETUP:
  - Define any required fixtures in the same test file
  - For mocking external dependencies, use pytest.fixture and mocker
  - DO NOT use @pytest.mark.usefixtures, pass fixtures as parameters instead
  - Create mock objects using mocker.patch or mocker.Mock()

3. SINGLE TEST FOCUS:
  - Generate exactly ONE test that covers lines {start_line}-{end_line}
  - Test name should clearly indicate what is being tested
  - One or more assertions are allowed if needed for the specific lines

4. Keep test inputs simple:
  - Minimal valid examples
  - Clear expected outputs
  - Avoid overly complex test data

5. Output ONLY valid python code:
  - Include required imports (pytest, unittest.mock if needed)
  - Include fixture definitions
  - Include exactly one test function
  - NO comments or docstrings"""
        else:
            prompt = base_prompt
        try:
            test_content = self.llm_manager.get_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test generator. Only output valid Python code without any explanations or markdown formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            # Clean up any markdown code blocks
            test_content = (
                test_content.replace("```python", "").replace("```", "").strip()
            )

            return test_content

        except Exception as e:
            return f"# Error generating tests: {str(e)}"

    def clean_test_file(
        self, test_execution_error: str, test_file_path: Path
    ) -> Tuple[Path, str]:
        """Cleans the content of a test file based on the provided execution error.

        This method reads the content of the specified test file, processes it to
        generate cleaned test content based on the provided execution error, and
        returns the original file path along with the cleaned content.

        Args:
            test_execution_error (str): The error message from the test execution.
            test_file_path (Path): The path to the test file to be cleaned.

        Returns:
            Tuple[Path, str]: A tuple containing the original test file path and the
                              cleaned test content."""

        with open(test_file_path, "r") as f:
            test_code = f.read()

        # Generate test content
        test_content = self._clean_test_content(
            test_execution_error=test_execution_error,
            test_file_path=test_file_path,
            test_code=test_code,
        )

        return test_file_path, test_content

    def _clean_test_content(
        self,
        test_execution_error: Optional[str] = None,
        test_file_path: Optional[Path] = None,
        test_code: Optional[str] = None,
    ) -> str:
        """Cleans the provided test code by removing failing tests.

        This method utilizes a language model to analyze the test code and the associated error message,
        returning only the valid Python code while preserving passing tests and imports.

        Args:
            test_execution_error (Optional[str]): The error message indicating which tests are failing.
            test_file_path (Optional[Path]): The file path of the test file (not used in processing).
            test_code (Optional[str]): The complete test code to be cleaned.

        Returns:
            str: The cleaned test code containing only the valid tests and imports, or an error message
            if the cleaning process fails."""
        base_prompt = f"""Please help me clean this code:
{test_code}

Removing the unit tests that are failing based on this error message:
{test_execution_error}

# CLEANUP REQUIREMENTS
- Remove only the failing tests
- Keep working tests intact
- Keep working imports
- Output only valid Python code, no comments or explanations

Output ONLY valid python code:
    - DO NOT include any comments or docstrings about file paths
  - DO NOT include explanatory text
    - DO NOT include text explaining the fix you made
"""
        try:
            test_content = self.llm_manager.get_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a test cleaner. Only output valid Python code without any explanations or markdown formatting.",
                    },
                    {"role": "user", "content": base_prompt},
                ],
                temperature=0.7,
            )

            test_content = (
                test_content.replace("```python", "").replace("```", "").strip()
            )

            return test_content

        except Exception as e:
            return f"# Error generating tests: {str(e)}"
