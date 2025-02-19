[![PyPI Downloads](https://static.pepy.tech/badge/ambrogio)](https://pepy.tech/projects/ambrogio)

# Ambrogio - tech debt agent

Ambrogio is an intelligent dev agent that helps tackle technical debt in your codebase. Starting with docstring improvements, it systematically enhances code quality and maintainability through automated analysis and improvements.

## 🎯 Mission

Our mission is to help development teams maintain high-quality codebases by automatically identifying and addressing technical debt, starting with comprehensive and accurate docstrings. Ambrogio uses advanced language models to understand your code and generate meaningful documentation.

## ✨ Features

### Current Features
- ✅ **Smart Docstring Generation**: Automatically adds clear, comprehensive docstrings to classes and methods
- ✅ **Multi-Provider Support**: Works with various LLM providers through LiteLLM integration
- ✅ **Flexible Configuration**: Customize the model, API endpoint, and other parameters

### 🚀 Upcoming Features
- Pre-PR test runs to prevent regressions
- Improve existing docstrings in modified methods
- Documentation generation for easier understanding
- Unit test generation and enhancement
- Type safety refactoring
- Spaghetti code cleanup
- Code formatting and best practices enforcement

## 📦 Installation

```bash
pip install ambrogio
```

## 🚀 Usage

### Basic Usage

```bash
# Run with default settings (uses OPENAI_API_KEY from environment)
ambrogio

# Run with custom configuration
ambrogio \
  --path /path/to/your/project \
  --api-key your-api-key \
  --model gpt-4 \
  --max-api-calls 20
```

### Advanced Usage

```bash
# Use Azure OpenAI
ambrogio \
  --api-key your-azure-key \
  --api-base https://your-azure-deployment.openai.azure.com \
  --model gpt-4

# Use Anthropic's Claude
ambrogio \
  --api-key your-anthropic-key \
  --model claude-2
```

### Available Options

```
--path           Path to the Python project (default: current directory)
--api-key        API key for your LLM provider (default: OPENAI_API_KEY from env)
--model          Model to use (default: gpt-4o-mini)
--max-api-calls  Maximum number of API calls per run (default: 12)
--api-base       Base URL for API endpoint (required for Azure, optional for others)
```

### Environment Variables

- `OPENAI_API_KEY`: Default API key if not provided via command line

## 🔧 Supported LLM Providers

Ambrogio uses LiteLLM for multi-provider support. You can use any of these providers:

- OpenAI (GPT-3.5, GPT-4)
- Azure OpenAI
- Anthropic (Claude)
- And many more! Check [LiteLLM's documentation](https://github.com/BerriAI/litellm) for the full list

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is licensed under the GPL-3.0 License - see the LICENSE file for details.


## Maintainers

- [Raoul Scalise](https://www.linkedin.com/in/raoul-scalise/)
- [Saro Lovito](https://www.linkedin.com/in/saroantonellolovito/)