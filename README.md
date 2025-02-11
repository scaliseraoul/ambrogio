[![PyPI Downloads](https://static.pepy.tech/badge/ambrogio)](https://pepy.tech/projects/ambrogio)

# Ambrogio - tech debt agent

Ambrogio is an opinionated dev agent who tackles tech debt. Starting with docstring improvements, it systematically enhances code quality and maintainability through automated analysis and improvements.

## Mission

Our mission is to help development teams maintain high-quality codebases by automagically identifying and addressing technical debt, starting with comprehensive and accurate docstrings.

## Roadmap

### Current Feature
- ✅ **Add docstrings** to classes and methods that lack them. Making your code readable for humans and LLMs.

### Upcoming Features
  - Pre-PR test runs to prevent regressions
  - Improve existing docstrings in modified methods
  - Documentation generation for easier understanding and maintenance
  - Unit test generation and enhancement
  - Type safety refactoring
  - Spaghetti code cleanup
  - Stability improvements (static methods, code reliability)
  - Code formatting
  - Type annotations
  - Best practices enforcement

## Installation

```bash
# Install using pip
pip install ambrogio
```

## Usage

### Basic Usage

```bash
# Run on current directory
ambrogio

# Run on specific directory with custom options
ambrogio \
  --path /path/to/your/project \
  --openai-key sk-your-key \
  --model gpt-4 \
  --max-api-calls 20
```

### Available Options

```
--path           Path to the Python project (default: current directory)
--openai-key     Your OpenAI API key (required unless set via OPENAI_API_KEY env var)
--model          OpenAI model to use (default: gpt-3.5-turbo)
--max-api-calls  Maximum number of API calls per run (default: 12)
```

### Required Secrets

- `OPENAI_API_KEY`: Your OpenAI API key


## Maintainers

- [Raoul Scalise](https://www.linkedin.com/in/raoul-scalise/)
- [Saro Lovito](https://www.linkedin.com/in/saroantonellolovito/)