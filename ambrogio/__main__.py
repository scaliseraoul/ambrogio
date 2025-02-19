import argparse
import os

from dotenv import load_dotenv

from ambrogio.ambr_docstring import AmbrogioDocstring, DEFAULT_MAX_API_CALLS
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


def main():
    """Main entry point for the Ambrogio docstring fixer.

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

    parser = argparse.ArgumentParser(description="Ambrogio - Your docstring fixer")
    parser.add_argument(
        "--path",
        type=str,
        help="Repository path. If not provided, uses current directory",
        default=None,
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="LLM provider API key. If not provided, will try to use OPENAI_API_KEY from environment",
        default=None,
    )
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use for generating docstrings",
        default="gpt-4o-mini",
    )
    parser.add_argument(
        "--max-api-calls",
        type=int,
        help=f"Maximum number of API calls to make (default: {DEFAULT_MAX_API_CALLS})",
        default=DEFAULT_MAX_API_CALLS,
    )
    parser.add_argument(
        "--api-base",
        type=str,
        help="Optional base URL for the API endpoint",
        default=None,
    )

    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
