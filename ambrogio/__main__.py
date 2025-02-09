import argparse
import os

from dotenv import load_dotenv

from ambrogio.ambr_docstring import AmbrogioDocstring, DEFAULT_MAX_API_CALLS
from ambrogio.repo_manager import RepoPathManager


def run_ambrogio(
    repo_path=None,
    openai_key=None,
    model="gpt-4o-mini",
    max_api_calls=DEFAULT_MAX_API_CALLS,
):
    """Run Ambrogio docstring fixer with the specified parameters.

    This function initializes the necessary components and runs the docstring fixer process.
    It can be called directly from another Python process.

    Args:
        repo_path (str, optional): Repository path. Defaults to the current directory if not provided.
        openai_key (str, optional): OpenAI API key. Defaults to the value from environment variable
            `OPENAI_API_KEY` if not provided.
        model (str, optional): OpenAI model to use for generating docstrings. Defaults to "gpt-4o-mini".
        max_api_calls (int, optional): Maximum number of OpenAI API calls to make. Defaults to DEFAULT_MAX_CALLS.

    Raises:
        ValueError: If the OpenAI API key is not provided and not found in environment.
    """
    # Get OpenAI API key from args or environment
    openai_key = openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError(
            "OpenAI API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    # Initialize repo path manager
    repo_manager = RepoPathManager()
    repo_manager.initialize(repo_path)

    # Initialize and run Ambrogio
    ambrogio = AmbrogioDocstring(
        openai_api_key=openai_key,
        model=model,
        max_api_calls=max_api_calls,
    )
    ambrogio.run()
    print("Ambrogio: my work is done here, going to take a pizza 🍕")


def main():
    """Command-line entry point for the Ambrogio docstring fixer.

    This function sets up command-line argument parsing to configure the
    behavior of the docstring fixer and calls the main functionality.

    Args:
        None

    Raises:
        ValueError: If the OpenAI API key is not provided and not found in environment.
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ambrogio - Your docstring fixer")
    parser.add_argument(
        "--path",
        type=str,
        help="Repository path. If not provided, uses current directory",
        default=None,
    )
    parser.add_argument(
        "--openai-key",
        type=str,
        help="OpenAI API key. If not provided, will try to use OPENAI_API_KEY from environment",
        default=None,
    )
    parser.add_argument(
        "--model",
        type=str,
        help="OpenAI model to use for generating docstrings",
        default="gpt-4o-mini",
    )
    parser.add_argument(
        "--max-api-calls",
        type=int,
        help=f"Maximum number of OpenAI API calls to make (default: {DEFAULT_MAX_API_CALLS})",
        default=DEFAULT_MAX_API_CALLS,
    )

    args = parser.parse_args()

    openai_key = args.openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError(
            "OpenAI API key must be provided either as argument or in OPENAI_API_KEY environment variable"
        )

    run_ambrogio(
        repo_path=args.path,
        openai_key=openai_key,
        model=args.model,
        max_api_calls=args.max_api_calls,
    )


if __name__ == "__main__":
    main()
