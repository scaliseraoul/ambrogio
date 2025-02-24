import argparse
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from ambrogio.ambr_coverage.ambr_pipeline import run_pipeline
from ambrogio.ambr_docstring import AmbrogioDocstring
from ambrogio.llm_manager import LLMManager
from ambrogio.repo_manager import RepoPathManager


def run_ambrogio(
    repo_path: str = None,
    api_key: str = None,
    model: str = "gpt-4o-mini",
    max_api_calls: int = 12,
    api_base: str = None,
) -> List[str]:
    """Run the Ambrogio process to modify documentation strings in a repository.

    This function initializes the environment for Ambrogio, ensuring that
    the necessary API key is available, and then processes the specified
    repository to update its documentation strings using the OpenAI API.

    Args:
        repo_path: The path to the repository to be processed.
                  If not provided, defaults to the current directory.
        api_key: The OpenAI API key for authentication.
                If not provided, it will attempt to use the OPENAI_API_KEY environment variable.
        model: The model to use for API calls. Defaults to "gpt-4".
        max_api_calls: The maximum number of API calls to make. Default is 12.
        api_base: The base URL for the OpenAI API. If not provided,
                 the default OpenAI endpoint will be used.

    Returns:
        A list of modified file paths that were updated during the process.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    # Get API key from args or environment
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    # Initialize repo path manager
    RepoPathManager.initialize(path=repo_path)
    # Initialize LLM manager
    LLMManager.initialize(api_key=api_key, model=model, api_base=api_base)

    # Initialize and run Ambrogio
    ambrogio = AmbrogioDocstring(max_api_calls=max_api_calls)
    modified_files = ambrogio.run()
    print("\nAmbrogio: my work is done here, going to take a pizza 🍕")
    return modified_files


def run_coverage(
    repo_path: str = None,
    api_key: str = None,
    model: str = "gpt-4o-mini",
    max_iterations: int = 3,
    api_base: str = None,
) -> (bool, str):
    """Run the coverage analysis on a repository and generate missing tests.

    Args:
        repo_path: The path to the repository to be analyzed.
                  If not provided, defaults to the current directory.
        api_key: API key for test generation.
                If not provided, it will attempt to use the OPENAI_API_KEY environment variable.
        model: Model to use for generating tests. Defaults to "gpt-4".
        max_iterations: Maximum number of test generation attempts per file. Default is 3.
        api_base: Optional base URL for the API endpoint.

    Returns:
        A dictionary mapping file paths to their coverage percentage.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    # Get API key from args or environment
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    RepoPathManager.initialize(path=repo_path)
    # Initialize LLM manager
    LLMManager.initialize(api_key=api_key, model=model, api_base=api_base)

    success, filename = run_pipeline(
        max_iterations=max_iterations, repo_path=Path(repo_path) if repo_path else None
    )

    if success:
        print(f"\n✨ Successfully generated test file: {filename}")
    else:
        print("\n❌ Failed to generate tests. Please check the logs above for details.")

    return success


def main():
    """Main entry point for Ambrogio.

    This function sets up the command-line interface for the Ambrogio tool.
    It provides two main functionalities:
    1. Docstring generation: Add or update docstrings in Python files
    2. Test coverage: Analyze test coverage and generate missing tests

    Args:
        --repo-path: Path to the repository to process. Defaults to current directory.
        --api-key: OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable.
        --model: Model to use for API calls. Default: gpt-4o-mini
        --api-base: Base URL for OpenAI API. If not provided, uses default endpoint.
        --mode: Mode to run in ('docstring' or 'coverage'). Default: docstring

        Docstring mode arguments:
            --max-api-calls: Maximum number of API calls to make. Default: 12

        Coverage mode arguments:
            --max-iterations: Maximum number of test generation attempts per file. Default: 3

    Raises:
        ValueError: If no API key is provided or found in environment.

    Returns:
        None"""

    load_dotenv()

    parser = argparse.ArgumentParser(description="Ambrogio - your AI coding assistant")
    parser.add_argument(
        "--repo-path",
        help="Path to the repository to process. Defaults to current directory.",
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model to use for API calls. Default: gpt-4o-mini",
    )
    parser.add_argument(
        "--api-base",
        help="Base URL for OpenAI API. If not provided, uses default endpoint.",
    )
    parser.add_argument(
        "--mode",
        choices=["docstring", "coverage"],
        default="docstring",
        help="Mode to run in. Default: docstring",
    )

    # Mode-specific arguments
    docstring_group = parser.add_argument_group("Docstring mode arguments")
    docstring_group.add_argument(
        "--max-api-calls",
        type=int,
        default=12,
        help="Maximum number of API calls to make. Default: 12",
    )

    coverage_group = parser.add_argument_group("Coverage mode arguments")
    coverage_group.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of test generation attempts per file. Default: 3",
    )

    args = parser.parse_args()

    # Validate API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    if args.mode == "docstring":
        run_ambrogio(
            repo_path=args.repo_path,
            api_key=args.api_key,
            model=args.model,
            max_api_calls=args.max_api_calls,
            api_base=args.api_base,
        )
    else:
        run_coverage(
            repo_path=args.repo_path,
            api_key=args.api_key,
            model=args.model,
            max_iterations=args.max_iterations,
            api_base=args.api_base,
        )


if __name__ == "__main__":
    main()
