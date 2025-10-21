# Contributing to Better Paperless

Thank you for your interest in Better Paperless! We welcome contributions from the community.

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/better-paperless.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Install dependencies: `poetry install --with dev`
5. Make your changes
6. Test: `poetry run pytest`
7. Commit: `git commit -m "feat: Description"`
8. Push: `git push origin feature/your-feature`
9. Create a Pull Request

## 📋 Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/better-paperless.git
cd better-paperless

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/
```

## 🧪 Testing

```bash
# All tests
poetry run pytest

# With coverage report
poetry run pytest --cov=better_paperless --cov-report=html

# Unit tests only
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# Specific test file
poetry run pytest tests/unit/test_api_client.py
```

## 📝 Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Check everything at once
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run flake8 src/ tests/
poetry run mypy src/
```

## 🏗️ Project Structure

```
better-paperless/
├── src/better_paperless/     # Main code
│   ├── api/                   # Paperless API Client
│   ├── llm/                   # LLM Providers
│   ├── processors/            # Document Processing
│   ├── core/                  # Core Utilities
│   └── cli/                   # CLI Commands
├── tests/                     # Tests
│   ├── unit/                  # Unit Tests
│   ├── integration/           # Integration Tests
│   └── fixtures/              # Test Fixtures
├── config/                    # Configuration
└── docker/                    # Docker Files
```

## 🎯 Contribution Guidelines

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update dependencies
```

Examples:
```
feat: Add support for Anthropic Claude
fix: Fix metadata extraction for invoices
docs: Update README with new examples
test: Add tests for tag engine
```

### Pull Requests

**Before creating a PR:**
1. ✅ All tests pass
2. ✅ Code is formatted (black, isort)
3. ✅ No linter warnings
4. ✅ Type hints are present
5. ✅ Documentation is updated

**PR description should include:**
- What was changed and why
- Which issues are being closed
- Screenshots (for UI changes)
- Breaking changes (if any)

**Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug Fix
- [ ] New Feature
- [ ] Breaking Change
- [ ] Documentation

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code is formatted
- [ ] All tests pass

## Related Issues
Closes #123
```

## 🐛 Bug Reports

Use [GitHub Issues](https://github.com/Kenny1338/better-paperless-ngx/issues) with:

**Template:**
```markdown
**Description**
Clear description of the bug

**Reproduction**
1. Steps to reproduce
2. Expected behavior
3. Actual behavior

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.11.5]
- Better Paperless Version: [e.g., 1.0.0]
- LLM Provider: [e.g., OpenAI GPT-4]

**Logs**
```
Relevant log output
```
```

## 💡 Feature Requests

Use [GitHub Discussions](https://github.com/Kenny1338/better-paperless-ngx/discussions) for:
- Feature ideas
- Discussions
- Questions

## 📚 Documentation

Documentation can be improved in:
- `README.md` - Main documentation
- `ARCHITECTURE.md` - Architecture details
- Docstrings in code
- Type hints

## 🔍 Code Review Process

1. **Automatic checks** must pass
2. **At least 1 approval** from a maintainer
3. **All comments** must be addressed
4. **CI/CD pipeline** must succeed

## 🏅 Recognition

Contributors will be recognized in:
- README.md credits
- Release notes
- Contributors graph

## 📞 Questions?

- 💬 [GitHub Discussions](https://github.com/Kenny1338/better-paperless-ngx/discussions)

## 📜 Code of Conduct

We expect respectful interaction. Please read our [Code of Conduct](CODE_OF_CONDUCT.md).

---

**Thank you for your contributions! 🎉**