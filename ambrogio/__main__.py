import argparse
import os

from dotenv import load_dotenv

from ambrogio.ambr_docstring import AmbrogioDocstring, DEFAULT_MAX_API_CALLS
from ambrogio.repo_manager import RepoPathManager


def main():
    """Main entry point for the Ambrogio docstring fixer.

    This function sets up command-line argument parsing to configure the
    behavior of the docstring fixer. It initializes the necessary components,
    including loading the OpenAI API key and setting up the repository path.
    It then runs the docstring fixer process.

    Args:
        --path (str, optional): Repository path. Defaults to the current directory if not provided.
        --openai-key (str, optional): OpenAI API key. Defaults to the value from the environment variable
            `OPENAI_API_KEY` if not provided.
        --model (str, optional): OpenAI model to use for generating docstrings. Defaults to "gpt-4o-mini".
        --max-api-calls (int, optional): Maximum number of OpenAI API calls to make. Defaults to a predefined
            constant value.

    Raises:
        ValueError: If the Open"""
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

    # Get OpenAI API key from args or environment
    openai_key = args.openai_key or os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError(
            "OpenAI API key must be provided either via --openai-key argument "
            "or OPENAI_API_KEY environment variable"
        )

    repo_manager = RepoPathManager()
    repo_manager.initialize(args.path)

    docstring_fixer = AmbrogioDocstring(
        openai_api_key=openai_key, model=args.model, max_api_calls=args.max_api_calls
    )
    docstring_fixer.run()

    print("Ambrogio: my work is done here, going to take a pizza 🍕")


if __name__ == "__main__":
    main()
