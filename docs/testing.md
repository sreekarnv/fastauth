# Testing Guide

This guide covers testing practices, running tests, and understanding test coverage for FastAuth.

## Quick Reference

### Run All Tests
```bash
# Basic test run
poetry run pytest

# With coverage (recommended)
poetry run test-cov

# Quiet mode
poetry run test-cov -q

# Verbose mode
poetry run pytest -v
```

### Run Specific Tests
```bash
# Single test file
poetry run pytest tests/core/test_oauth.py

# Single test function
poetry run pytest tests/core/test_oauth.py::test_initiate_oauth_flow_basic

# Test pattern matching
poetry run pytest -k "oauth"

# Test by marker
poetry run pytest -m "slow"
```

## Test Organization

### Directory Structure
```
tests/
├── adapters/
│   └── sqlalchemy/         # SQLAlchemy adapter tests
│       ├── test_user_adapter.py
│       ├── test_oauth_accounts.py
│       └── conftest.py     # Shared fixtures
├── api/                    # API endpoint tests
│   ├── test_auth_flow.py
│   ├── test_oauth.py
│   └── conftest.py
├── core/                   # Core business logic tests
│   ├── test_users.py
│   ├── test_oauth.py
│   └── test_roles.py
├── security/               # Security module tests
│   ├── test_jwt.py
│   ├── test_oauth_security.py
│   └── test_rate_limit.py
└── fakes/                  # Fake/mock adapters for testing
    ├── oauth_accounts.py
    └── oauth_states.py
```

### Test Categories

**Unit Tests** (`tests/core/`)
- Test business logic in isolation
- Use fake adapters to avoid database
- Fast execution
- Example: `tests/core/test_users.py`

**Integration Tests** (`tests/adapters/`)
- Test adapter implementations
- Use in-memory SQLite database
- Verify database operations
- Example: `tests/adapters/sqlalchemy/test_user_adapter.py`

**API Tests** (`tests/api/`)
- Test HTTP endpoints end-to-end
- Use FastAPI TestClient
- Verify request/response handling
- Example: `tests/api/test_auth_flow.py`

## Test Reports

### Report Structure

All test reports are automatically generated in timestamped folders:

```
test-results/
└── YYYYMMDD_HHMMSS/
    ├── report.html          # Interactive HTML test report
    ├── junit.xml            # JUnit XML (for CI/CD)
    ├── pytest.log           # Detailed test execution log
    ├── coverage.xml         # Machine-readable coverage
    ├── .coverage            # Coverage database file
    └── htmlcov/             # Interactive HTML coverage browser
        └── index.html
```

### Viewing Reports

**Test Results:**
```bash
# Open latest HTML test report
open test-results/$(ls -t test-results | head -1)/report.html

# On Windows
start test-results/YYYYMMDD_HHMMSS/report.html
```

**Coverage:**
```bash
# Open interactive coverage browser
open test-results/$(ls -t test-results | head -1)/htmlcov/index.html

# On Windows
start test-results/YYYYMMDD_HHMMSS/htmlcov/index.html
```

### CI/CD Integration

The `junit.xml` file can be used in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: poetry run test-cov

- name: Upload test results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test-results/*/junit.xml
```

## Coverage

### Current Coverage

- **Total Coverage**: 85%
- **Total Tests**: 195
- **All Tests Passing**: ✅

### Coverage Goals

- **Minimum**: 80% (✅ Achieved)
- **Target**: 85% (✅ Achieved)
- **Stretch**: 90%

### Viewing Coverage

**Terminal Summary:**
```bash
poetry run test-cov
# Coverage summary appears at the end
```

**HTML Report (Recommended):**
```bash
poetry run test-cov
# Open the latest htmlcov/index.html in your browser
```

The HTML coverage report shows:
- Line-by-line coverage visualization
- Branch coverage
- Missing lines highlighted in red
- Partial coverage in yellow

### Coverage by Module

**100% Coverage** (38 files):
- All core authentication flows
- All test fixtures and fakes
- Session management
- Account management
- RBAC functions

**85%+ Coverage**:
- Core OAuth flows (82%)
- API dependencies (85%)
- Account API (92%)
- Email verification (89%)

**Areas for Improvement** (<40%):
- OAuth API endpoints (32%)
- OAuth adapters (33-39%)
- Email providers (38-70%)
- Google OAuth provider (39%)

## Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_create_user_success():
    # Arrange
    users = FakeUserAdapter()
    email = "test@example.com"
    password = "password123"

    # Act
    user = create_user(users=users, email=email, password=password)

    # Assert
    assert user.email == email
    assert user.hashed_password != password  # Password should be hashed
    assert user.is_active is True
```

### Using Fixtures

**Session Fixture** (database tests):
```python
def test_user_adapter(session):
    # session is an in-memory SQLite database
    adapter = SQLAlchemyUserAdapter(session)
    user = adapter.create_user(
        email="test@example.com",
        hashed_password="hashed..."
    )
    assert user.id is not None
```

**Client Fixture** (API tests):
```python
def test_register_endpoint(client):
    # client is a FastAPI TestClient
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
```

### Testing Async Code

For async OAuth flows:

```python
import pytest

@pytest.mark.asyncio
async def test_complete_oauth_flow_new_user(session):
    # Test async OAuth completion
    user, is_new = await complete_oauth_flow(...)
    assert is_new is True
```

### Testing Error Cases

Always test both success and failure paths:

```python
def test_create_user_duplicate_email():
    users = FakeUserAdapter()
    email = "test@example.com"

    # Create first user
    create_user(users=users, email=email, password="pass1")

    # Attempt to create duplicate
    with pytest.raises(UserAlreadyExistsError):
        create_user(users=users, email=email, password="pass2")
```

## Best Practices

### 1. Test Independence

Each test should be independent:

```python
# Good - independent
def test_user_creation():
    users = FakeUserAdapter()  # Fresh adapter
    user = create_user(users=users, email="test@example.com", password="pass")
    assert user is not None

# Bad - depends on previous state
user_adapter = FakeUserAdapter()  # Shared state

def test_first():
    create_user(users=user_adapter, ...)  # Modifies shared state

def test_second():
    # Assumes test_first ran first
    user = user_adapter.get_by_email(...)
```

### 2. Descriptive Test Names

Use clear, descriptive names:

```python
# Good
def test_login_fails_if_email_not_verified():
    ...

def test_refresh_token_rotation_on_use():
    ...

# Bad
def test_login():
    ...

def test_token():
    ...
```

### 3. Test One Thing

Each test should verify one specific behavior:

```python
# Good - tests one thing
def test_password_is_hashed_on_user_creation():
    users = FakeUserAdapter()
    password = "plaintext"
    user = create_user(users=users, email="test@example.com", password=password)
    assert user.hashed_password != password

# Bad - tests multiple things
def test_user_creation_and_login_and_token_refresh():
    # Too much in one test
    ...
```

### 4. Use Fake Adapters for Unit Tests

For core logic tests, use fake adapters:

```python
# tests/fakes/users.py
class FakeUserAdapter(UserAdapter):
    def __init__(self):
        self.users = {}

    def create_user(self, email, hashed_password):
        user = User(email=email, hashed_password=hashed_password)
        self.users[email] = user
        return user
```

Benefits:
- No database required
- Faster test execution
- Easier to control test scenarios
- True unit testing

### 5. Use Real Database for Integration Tests

For adapter tests, use real database:

```python
@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()  # Clean up
```

## Continuous Integration

FastAuth uses GitHub Actions for CI/CD:

```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.11", "3.12", "3.13"]
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    - name: Run tests
      run: poetry run pytest --cov=fastauth --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### CI Test Results

- Tests run on every push and PR
- Matrix testing across Python 3.11, 3.12, 3.13
- Coverage reports uploaded to Codecov
- Status badges in README

## Troubleshooting

### ResourceWarnings

If you see ResourceWarnings about unclosed database connections:

```python
# Ensure engine disposal in fixtures
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

    # Important: Dispose engine to close connections
    engine.dispose()
```

### Test Isolation Issues

If tests pass individually but fail when run together:

```python
# Use fresh fixtures for each test
@pytest.fixture
def users():
    return FakeUserAdapter()  # New instance each time

# Not this
users = FakeUserAdapter()  # Shared across tests
```

### Slow Tests

For slow tests (e.g., OAuth network requests):

```python
# Mark slow tests
@pytest.mark.slow
def test_real_oauth_provider():
    ...

# Skip slow tests by default
pytest -m "not slow"

# Run only slow tests
pytest -m "slow"
```

### Coverage Not Updated

If coverage isn't updating:

```bash
# Clear coverage cache
rm -rf .coverage htmlcov/

# Run tests fresh
poetry run test-cov
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
