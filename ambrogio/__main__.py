import argparse
import os
from typing import Dict

from dotenv import load_dotenv

from ambrogio.ambr_docstring import AmbrogioDocstring, DEFAULT_MAX_API_CALLS
from ambrogio.ambr_coverage import CoverageAnalyzer
from ambrogio.repo_manager import RepoPathManager


def run_ambrogio(
    repo_path=None,
    api_key=None,
    model="gpt-4o-mini",
    max_api_calls=DEFAULT_MAX_API_CALLS,
    api_base=None,
) -> list[str]:
    """Run the Ambrogio process to modify documentation strings in a repository.

    This function initializes the environment for Ambrogio, ensuring that
    the necessary API key is available, and then processes the specified
    repository to update its documentation strings using the OpenAI API.

    Args:
        repo_path (str, optional): The path to the repository to be processed.
                                    If not provided, defaults to the current directory.
        api_key (str, optional): The OpenAI API key for authentication.
                                  If not provided, it will attempt to use the
                                  OPENAI_API_KEY environment variable.
        model (str, optional): The model to use for API calls. Defaults to "gpt-4o-mini".
        max_api_calls (int, optional): The maximum number of API calls to make.
                                        Default is set by DEFAULT_MAX_API_CALLS.
        api_base (str, optional): The base URL for the OpenAI API. If not provided,
                                  the default OpenAI endpoint will be used.

    Returns:
        list[str]: A list of modified file paths that were updated during the process."""

    # Get API key from args or environment
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    # Initialize repo path manager
    repo_manager = RepoPathManager()
    repo_manager.initialize(repo_path)

    # Initialize and run Ambrogio
    ambrogio = AmbrogioDocstring(
        api_key=api_key,
        model=model,
        max_api_calls=max_api_calls,
        api_base=api_base,
    )
    modified_files = ambrogio.run()
    print("\nAmbrogio: my work is done here, going to take a pizza 🍕")
    return modified_files


def run_coverage(
    repo_path=None,
    api_key=None,
    model="gpt-4",
    max_api_calls=12,
    api_base=None,
) -> Dict[str, float]:
    """Run the coverage analysis on a repository.

    Args:
        repo_path (str, optional): The path to the repository to be analyzed.
                                    If not provided, defaults to the current directory.
        api_key (str, optional): API key for test generation.
        model (str, optional): Model to use for generating tests.
        max_api_calls (int, optional): Maximum number of API calls for test generation.
        api_base (str, optional): Optional base URL for the API endpoint.

    Returns:
        Dict[str, float]: A dictionary mapping file paths to their coverage percentage.
    """
    analyzer = CoverageAnalyzer(
        repo_path=repo_path,
        api_key=api_key,
        model=model,
        max_api_calls=max_api_calls,
        api_base=api_base,
    )
    coverage_data = analyzer.analyze_coverage()

    print("\nCoverage Analysis Results:")
    for file_path, coverage in coverage_data.items():
        print(f"{file_path}: {coverage:.2f}% coverage")
        if coverage < 100:
            print(f"\nGenerating tests for {file_path}...")
            test_file, message = analyzer.generate_tests(file_path)
            print(f"  {message}")
            print()

    return coverage_data


def main():
    """Main entry point for Ambrogio.

    This function sets up the command-line interface for the Ambrogio tool,
    allowing users to specify options for the repository path, API key,
    model type, maximum API calls, and API base URL. It loads environment
    variables, parses command-line arguments, validates the API key, and
    then invokes the core functionality to run the docstring fixer.

    Args:
        --path (str, optional): Repository path. If not provided, uses the current directory.
        --api-key (str, optional): LLM provider API key. If not provided, attempts to use
            the OPENAI_API_KEY from the environment.
        --model (str, optional): LLM model to use for generating docstrings. Defaults to "gpt-4o-mini".
        --max-api-calls (int, optional): Maximum number of API calls to make. Defaults to
            DEFAULT_MAX_API_CALLS.
        --api-base (str, optional): Optional base URL for the API endpoint.

    Raises:
        ValueError: If the API key is not provided through arguments or environment variables.

    Returns:
        None"""

    load_dotenv()

    parser = argparse.ArgumentParser(description="Ambrogio - dev agent")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Docstring command
    docstring_parser = subparsers.add_parser(
        "docstring", help="Add docstrings to your code"
    )
    docstring_parser.add_argument(
        "--path",
        type=str,
        help="Repository path. If not provided, uses current directory",
        default=None,
    )
    docstring_parser.add_argument(
        "--api-key",
        type=str,
        help="LLM provider API key. If not provided, will try to use OPENAI_API_KEY from environment",
        default=None,
    )
    docstring_parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use for generating docstrings",
        default="gpt-4o-mini",
    )
    docstring_parser.add_argument(
        "--max-api-calls",
        type=int,
        help=f"Maximum number of API calls to make (default: {DEFAULT_MAX_API_CALLS})",
        default=DEFAULT_MAX_API_CALLS,
    )
    docstring_parser.add_argument(
        "--api-base",
        type=str,
        help="Optional base URL for the API endpoint",
        default=None,
    )

    # Coverage command
    coverage_parser = subparsers.add_parser(
        "coverage", help="Analyze code coverage and generate missing tests"
    )
    coverage_parser.add_argument(
        "--path",
        type=str,
        help="Repository path. If not provided, uses current directory",
        default=None,
    )
    coverage_parser.add_argument(
        "--api-key",
        type=str,
        help="LLM provider API key for test generation. If not provided, will try to use OPENAI_API_KEY from environment",
        default=None,
    )
    coverage_parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use for generating tests",
        default="gpt-4",
    )
    coverage_parser.add_argument(
        "--max-api-calls",
        type=int,
        help="Maximum number of API calls for test generation",
        default=12,
    )
    coverage_parser.add_argument(
        "--api-base",
        type=str,
        help="Optional base URL for the API endpoint",
        default=None,
    )

    args = parser.parse_args()

    if args.command == "docstring":
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key must be provided either as argument or in OPENAI_API_KEY environment variable"
            )

        run_ambrogio(
            repo_path=args.path,
            api_key=api_key,
            model=args.model,
            max_api_calls=args.max_api_calls,
            api_base=args.api_base,
        )
    elif args.command == "coverage":
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        run_coverage(
            repo_path=args.path,
            api_key=api_key,
            model=args.model,
            max_api_calls=args.max_api_calls,
            api_base=args.api_base,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
