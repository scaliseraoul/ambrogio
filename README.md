# ambrogio

# Ambrogio Implementation Guide

## 1. Initial Setup
```bash
# Create project
mkdir ambrogio && cd ambrogio
poetry init \
  --name "ambrogio" \
  --description "GitHub Action to add docstrings using OpenAI" \
  --author "Your Name" \
  --python "^3.10" \
  --dependency openai \
  --dependency libcst \
  --dependency pyyaml
poetry env use python3.10

# Add dev dependencies
poetry add --group dev pytest pytest-cov black isort mypy ruff

# Create project structure
mkdir -p src/ambrogio tests
touch src/ambrogio/__init__.py
```

## 2. Configuration Files

### pyproject.toml
```toml
[tool.poetry]
name = "ambrogio"
version = "0.1.0"
description = "GitHub Action to add docstrings using OpenAI"
authors = ["Your Name <email@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
openai = "^1.12.0"
libcst = "^1.1.0"
pyyaml = "^6.0.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
black = "^24.1.1"
isort = "^5.13.2"
mypy = "^1.8.0"
ruff = "^0.2.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### action.yml
```yaml
name: 'Ambrogio Tech Debt Bot'
description: 'Automatically adds docstrings using OpenAI'
inputs:
  openai_api_key:
    description: 'OpenAI API key'
    required: true
  model:
    description: 'OpenAI model to use'
    default: 'gpt-3.5-turbo'
    required: false
runs:
  using: 'composite'
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Install Poetry
      shell: bash
      run: pipx install poetry
    - name: Install dependencies
      shell: bash
      run: poetry install --no-dev
    - name: Run Ambrogio
      shell: bash
      run: poetry run python src/ambrogio/main.py
      env:
        OPENAI_API_KEY: ${{ inputs.openai_api_key }}
        MODEL: ${{ inputs.model }}
```

## 3. Core Implementation

### src/ambrogio/main.py
```python
import os
import libcst as cst
from openai import OpenAI
from pathlib import Path
from typing import List, Dict

class DocstringGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("MODEL", "gpt-3.5-turbo")
    
    def generate_docstring(self, code: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in Python docstrings. Generate clear, concise docstrings following Google style."},
                {"role": "user", "content": f"Generate a docstring for this Python code:\n\n{code}"}
            ]
        )
        return response.choices[0].message.content

class DocstringTransformer(cst.CSTTransformer):
    def __init__(self, generator: DocstringGenerator):
        self.generator = generator
        self.changes_made = False
    
    def transform_FunctionDef(self, node: cst.FunctionDef) -> cst.FunctionDef:
        if self.needs_docstring(node):
            docstring = self.generator.generate_docstring(node.code)
            return self.add_docstring(node, docstring)
        return node
    
    def needs_docstring(self, node: cst.FunctionDef) -> bool:
        # Check if public method without docstring
        return (not node.name.value.startswith('_') and 
                len(node.body.body) > 0 and
                not isinstance(node.body.body[0], cst.SimpleStatementLine))

def process_file(path: Path) -> bool:
    with open(path) as f:
        source = f.read()
    
    transformer = DocstringTransformer(DocstringGenerator())
    modified = cst.parse_module(source).visit(transformer)
    
    if transformer.changes_made:
        with open(path, 'w') as f:
            f.write(modified.code)
        return True
    return False

def main():
    workspace = Path(os.getenv('GITHUB_WORKSPACE', '.'))
    changes_made = False
    
    for path in workspace.rglob('*.py'):
        if process_file(path):
            changes_made = True
    
    exit(0 if not changes_made else 1)

if __name__ == "__main__":
    main()
```

## 4. Tests

### tests/test_ambrogio.py
```python
import pytest
from pathlib import Path
from ambrogio.main import DocstringTransformer, DocstringGenerator

def test_needs_docstring():
    code = """
    def public_method():
        pass
    """
    tree = cst.parse_module(code)
    transformer = DocstringTransformer(DocstringGenerator())
    assert transformer.needs_docstring(tree.body[0])

def test_private_method_ignored():
    code = """
    def _private_method():
        pass
    """
    tree = cst.parse_module(code)
    transformer = DocstringTransformer(DocstringGenerator())
    assert not transformer.needs_docstring(tree.body[0])
```

## 5. GitHub Workflow Example
```yaml
name: Tech Debt Fix
on:
  push:
    paths:
      - '.github/workflows/ambrogio.yml'
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  fix-tech-debt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: your-username/ambrogio@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

## 6. Release Process
```bash
# Tag version
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# Build package
poetry build

# Test in GitHub Actions
# 1. Create test repository
# 2. Add OpenAI API key to repository secrets
# 3. Add workflow file
# 4. Test manual trigger
```
