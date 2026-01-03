# Contributing to FastAuth

Thank you for your interest in contributing to FastAuth!

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=fastauth --cov-report=html

# Specific test
poetry run pytest tests/core/test_users.py -v

# Watch mode
poetry run pytest-watch
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint
poetry run ruff check .

# Fix linting issues
poetry run ruff check --fix .

# Run all checks
poetry run pre-commit run --all-files
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes

### Scopes

- `core`: Core business logic
- `adapters`: Database adapters
- `api`: API routes and dependencies
- `security`: Security features
- `email`: Email providers
- `tests`: Test suite

### Examples

```bash
feat(core): add user role management
fix(api): correct token refresh endpoint
docs(readme): update installation instructions
test(adapters): add MongoDB adapter tests
```

### Emoji Prefix (Optional)

- ✨ `:sparkles:` - `feat`
- 🐛 `:bug:` - `fix`
- 📝 `:memo:` - `docs`
- 🧪 `:test_tube:` - `test`
- ♻️ `:recycle:` - `refactor`
- ⚡ `:zap:` - `perf`
- 🔧 `:wrench:` - `chore`
- 🔖 `:bookmark:` - Version tags

## Pull Request Process

### Before Submitting

1. Create a feature branch from `main`
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation
5. Run pre-commit hooks
6. Write clear commit messages

### Branch Naming

```
feat/feature-name
fix/bug-description
docs/documentation-update
refactor/code-improvement
```

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Code formatted (Black)
- [ ] Linting passing (Ruff)
- [ ] No breaking changes (or documented)
- [ ] CHANGELOG.md updated

### PR Title

Use conventional commit format:

```
feat(core): add two-factor authentication
fix(api): resolve token expiration issue
docs(examples): add OAuth2 example
```

### PR Description

Use the provided template. Include:

- What changed
- Why it changed
- How to test
- Breaking changes (if any)

## Code Guidelines

### Architecture

- Core logic must be database-agnostic
- Business logic goes in `fastauth/core/`
- Database code goes in adapters
- No business logic in adapters
- Use dependency injection

### Testing

- Write tests for all new features
- Maintain >90% code coverage
- Use fixtures for common setup
- Test edge cases and errors
- Keep tests isolated

### Documentation

- Add docstrings to public APIs
- Update README for new features
- Add examples when helpful
- Keep docs up to date

### Security

- Never commit secrets
- Follow OWASP guidelines
- Use parameterized queries
- Validate all inputs
- Hash sensitive data

## Project Structure

```
fastauth/
├── fastauth/           # Main package
│   ├── core/          # Business logic (DB-agnostic)
│   ├── adapters/      # Database adapters
│   ├── api/           # FastAPI routes
│   ├── security/      # Security utilities
│   └── email/         # Email providers
├── tests/             # Test suite
├── examples/          # Example applications
└── docs/             # Documentation
```

## Need Help?

- Check existing issues and PRs
- Ask questions in Discussions
- Read the documentation
- Look at examples

## Additional Resources

- **[Code of Conduct](https://github.com/sreekarnv/fastauth/blob/main/CODE_OF_CONDUCT.md)** - Community guidelines
- **[Changelog](https://github.com/sreekarnv/fastauth/blob/main/CHANGELOG.md)** - Version history and changes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
