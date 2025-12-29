# Contributing to FastAuth

Thank you for your interest in contributing to FastAuth! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/yourusername/fastauth.git
   cd fastauth
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Install pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and ensure tests pass:
   ```bash
   poetry run pytest
   ```

3. **Run code quality checks**:
   ```bash
   poetry run black .
   poetry run ruff check .
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use Ruff for linting
- Write Google-style docstrings for all public functions and classes
- Add type hints to all function signatures

## Testing

- Write tests for all new features
- Maintain or improve test coverage (target: 80%+)
- Use pytest for all tests
- Place tests in the `tests/` directory mirroring the source structure

## Commit Messages

Follow conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test changes
- `refactor:` for refactoring
- `chore:` for maintenance tasks

## Pull Request Process

1. Update documentation for any new features
2. Add tests for bug fixes and new features
3. Ensure all tests pass and coverage is maintained
4. Update the CHANGELOG.md if applicable
5. Request review from maintainers

## Questions?

Feel free to open an issue for any questions or concerns.
