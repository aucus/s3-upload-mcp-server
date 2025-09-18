# Contributing to AWS S3 Upload MCP Server

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- `uv` package manager (recommended)
- Git
- AWS Account (for integration tests)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/s3-upload-mcp-server.git
   cd s3-upload-mcp-server
   ```

2. **Install dependencies**
   ```bash
   uv sync --dev
   ```

3. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your AWS credentials
   ```

4. **Run tests**
   ```bash
   uv run pytest
   ```

## 📝 Development Guidelines

### Code Style

- **Formatting**: Use Black with line length 88
- **Linting**: Use Ruff for code quality
- **Type Checking**: Use mypy with strict settings
- **Imports**: Use isort for import organization

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type check
uv run mypy src

# Sort imports
uv run ruff check --select I src tests
```

### Testing

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test with real AWS S3 (marked with `@pytest.mark.aws`)
- **Coverage**: Maintain >80% test coverage

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only unit tests
uv run pytest tests/unit/

# Run integration tests (requires AWS credentials)
uv run pytest tests/integration/ -m aws
```

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: maintenance tasks
```

Examples:
- `feat: add WebP conversion support`
- `fix: handle empty file list in batch upload`
- `docs: update README with new features`

## 🐛 Reporting Issues

When reporting issues, please include:

1. **Environment details**
   - Python version
   - Operating system
   - Package versions

2. **Steps to reproduce**
   - Clear, numbered steps
   - Expected vs actual behavior

3. **Error messages**
   - Full stack trace
   - Log output

4. **Additional context**
   - Screenshots if applicable
   - Related issues

## 🔧 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new functionality
   - Update documentation
   - Follow code style guidelines

3. **Test your changes**
   ```bash
   uv run pytest
   uv run black --check src tests
   uv run ruff check src tests
   uv run mypy src
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Request review from maintainers

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🏗️ Architecture

### Project Structure
```
src/s3_upload_mcp/
├── server.py          # FastMCP server entry point
├── tools.py           # MCP tools implementation
├── s3_client.py       # AWS S3 client wrapper
├── image_processor.py # Image processing utilities
└── models.py          # Pydantic data models
```

### Key Components

- **FastMCP Server**: Main MCP server using FastMCP v2
- **S3 Client**: Async wrapper around boto3
- **Image Processor**: PIL-based image optimization
- **Models**: Pydantic models for type safety

## 🔍 Code Review Process

1. **Automated Checks**
   - CI/CD pipeline runs on every PR
   - Code quality checks (linting, formatting, type checking)
   - Test coverage validation

2. **Manual Review**
   - At least one maintainer review required
   - Focus on code quality, architecture, and testing
   - Discussion and iteration as needed

3. **Approval and Merge**
   - All checks must pass
   - At least one approval required
   - Squash and merge preferred

## 📚 Documentation

- **README.md**: Project overview and quick start
- **API Documentation**: Inline docstrings
- **Examples**: In `docs/` directory
- **Architecture**: In `docs/architecture.md`

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: Contact maintainers directly

Thank you for contributing! 🎉
