"""Langraph-based test generation pipeline for Ambrogio."""

from pathlib import Path
from typing import Dict, Optional, Any, TypedDict, Annotated

import pytest
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from .ambr_coverage import CoverageAnalyzer
from .pytest_reportert import PytestReporter, silence_stdout


class TestState(TypedDict):
    """State of the test generation pipeline."""

    source_file_path: Annotated[Optional[Path], "last"]
    test_file_path: Annotated[Optional[Path], "last"]
    test_execution_error: Annotated[Optional[str], "last"]
    success: Annotated[bool, "last"]
    cleaning: Annotated[bool, "last"]
    error: Annotated[Optional[str], "last"]
    iteration: Annotated[int, "last"]


def create_test_pipeline(
    max_iterations: int, repo_path: Optional[Path] = None
) -> CompiledStateGraph:
    """Create a langraph pipeline for test generation.

    Args:
        max_iterations: Maximum number of iterations for test refinement
        repo_path: Optional path to the repository root

    Returns:
        A langgraph StateGraph instance representing the pipeline
    """
    # Initialize components
    coverage_analyzer = CoverageAnalyzer(
        repo_path=repo_path,
    )

    def analyze_coverage(state: TestState) -> Dict[str, Any]:
        """Run coverage analysis and find files needing tests."""
        # Run coverage analysis
        coverage_data = coverage_analyzer.analyze_coverage()

        print("\nInitial Coverage Analysis Results:")
        for source_file_path, coverage in coverage_data.items():
            print(f"{source_file_path}: {coverage:.2f}% coverage")

        # Find file with lowest coverage
        lowest_coverage_file = min(coverage_data.items(), key=lambda x: x[1])[0]

        return {"source_file_path": Path(lowest_coverage_file)}

    def generate_test(state: TestState) -> Dict[str, Any]:
        """Generate a test based on the current state.

        This function increments the iteration count in the provided state and attempts
        to generate a test for the specified source file. It utilizes the
        `coverage_analyzer` to create the test content. If the test generation fails,
        an error message is returned.

        Args:
            state (TestState): A dictionary holding the current state, including
                               'source_file_path', 'test_file_path', and any
                               'test_execution_error'.

        Returns:
            Dict[str, Any]: A dictionary containing the following keys:
                - "iteration" (int): The updated iteration count.
                - "test_file_path" (str): The path to the generated test file.
                - "test_execution_error" (None or str): None if no error occurred,
                  or an error message if test generation failed."""
        state["iteration"] += 1

        test_file_path = state.get("test_file_path", None)
        test_execution_error = state.get("test_execution_error", None)

        try:
            test_source_file_path, test_content = coverage_analyzer.generate_tests(
                source_file_path=state["source_file_path"],
                test_file_path=test_file_path,
                test_execution_error=test_execution_error,
            )

            if not test_source_file_path or not test_content:
                return {
                    "error": "Failed to generate test content",
                    "iteration": state["iteration"],
                }

            return {
                "iteration": state["iteration"],
                "test_file_path": test_source_file_path,
                "test_execution_error": None,
            }
        except Exception as e:
            return {
                "error": f"Error generating test: {str(e)}",
                "iteration": state["iteration"],
            }

    def clean_test(state: TestState) -> Dict[str, Any]:
        """Increments the iteration count in the given state and attempts to clean
        the test file specified in the state. It utilizes the coverage analyzer
        to process the test file and handle any execution errors.

        Args:
            state (TestState): A dictionary containing the state of the test,
                               including the current iteration, test file path,
                               and any execution errors.

        Returns:
            Dict[str, Any]: A dictionary containing the updated iteration count,
                             the cleaned test file path, or an error message
                             if the cleaning process fails."""
        state["iteration"] += 1

        test_file_path = state.get("test_file_path", None)
        test_execution_error = state.get("test_execution_error", None)

        try:
            test_source_file_path, test_content = coverage_analyzer.clean_tests(
                test_file_path=test_file_path,
                test_execution_error=test_execution_error,
            )

            if not test_source_file_path or not test_content:
                return {
                    "error": "Failed to clean test content",
                    "iteration": state["iteration"],
                }

            return {
                "iteration": state["iteration"],
                "test_file_path": test_source_file_path,
                "test_execution_error": None,
            }
        except Exception as e:
            return {
                "error": f"Error cleaning test: {str(e)}",
                "iteration": state["iteration"],
            }

    @silence_stdout
    def execute_test(state: TestState) -> Dict[str, Any]:
        """Execute the generated test and return results."""
        try:
            reporter = PytestReporter()
            result = pytest.main([str(state["test_file_path"])], plugins=[reporter])

            return {
                "success": result == 0,
                "test_execution_error": "\n".join(reporter.errors)
                if result != 0
                else None,
                "iteration": state["iteration"],
                "test_file_path": state["test_file_path"],
            }
        except Exception as e:
            return {
                "error": f"Error executing test: {str(e)}",
                "iteration": state["iteration"],
            }

    def error_clean_up(state: TestState) -> Dict[str, Any]:
        """Remove the test file specified in the state if it exists.

        This function checks for the presence of a "test_file_path" key in the
        provided state. If the key exists and the corresponding file exists on
        the filesystem, the file is deleted.

        Args:
            state (TestState): A dictionary-like object containing the state
                               information, including the path to the test file.

        Returns:
            None: This function does not return a value."""
        if "test_file_path" in state:
            test_file = Path(state["test_file_path"])
            if test_file.exists():
                test_file.unlink()

        return {"success": False}

    # Create the graph
    workflow = StateGraph(TestState)

    # Add nodes
    workflow.add_node("analyze_coverage", analyze_coverage)
    workflow.add_node("generate_test", generate_test)
    workflow.add_node("execute_test", execute_test)
    workflow.add_node("error_clean_up", error_clean_up)

    # Define routing function
    def route_next(state: TestState) -> str:
        """Determine the next routing action based on the current state.

        The function evaluates the provided state and returns a string indicating the
        appropriate next action: "success", "error", or "retry". It checks for success
        or error conditions and also considers the maximum number of iterations.

        Args:
            state (TestState): The current state containing information about success,
                               error, and the current iteration count.

        Returns:
            str: The next routing action based on the state conditions.
                  Possible values are "success", "error", or "retry"."""
        if state.get("success"):
            return "success"
        elif state.get("error"):
            return "error"
        elif state.get("iteration") >= max_iterations:
            return "error"
        else:
            return "retry"

    # Build the workflow
    workflow.add_edge(START, "analyze_coverage")
    workflow.add_edge("analyze_coverage", "generate_test")
    workflow.add_edge("generate_test", "execute_test")
    workflow.add_conditional_edges(
        "execute_test",
        route_next,
        {"success": END, "retry": "generate_test", "error": "error_clean_up"},
    )
    workflow.add_edge("error_clean_up", END)
    return workflow.compile()


def run_pipeline(max_iterations, repo_path: Optional[Path] = None) -> (bool, str):
    """Run the test generation pipeline.

    Args:
        max_iterations: Maximum number of iterations for test refinement
        repo_path: Optional path to the repository root
    """
    graph: CompiledStateGraph = create_test_pipeline(max_iterations, repo_path)

    # Initialize state
    state = TestState(
        iteration=0,
        success=False,
        cleaning=False,
        error=None,
        source_file_path=None,
        test_file_path=None,
        test_execution_error=None,
    )

    # Run the pipeline with debug streaming and increased recursion limit
    final_state = None
    for chunk in graph.stream(state, stream_mode="updates"):
        final_state = chunk
        print(f"\n\nAmbrogio action: {chunk}")

    # Get the first dictionary from the state
    first_state = next(iter(final_state.values()))
    return first_state.get("success", False), first_state.get("test_file_path", None)
