# Test Commands Reference

## Quick Commands

### Run all tests
```bash
poetry run pytest
```

### Run tests with coverage (recommended)
```bash
poetry run python scripts.py
```

Or using poetry script:
```bash
poetry run test-cov
```

### Run specific test file
```bash
poetry run pytest tests/core/test_oauth.py
```

### Run with verbose output
```bash
poetry run pytest -v
```

### Run quietly
```bash
poetry run python scripts.py -q
```

## Test Reports

All test reports are automatically generated in timestamped folders:
```
test-results/
  └── YYYYMMDD_HHMMSS/
      ├── report.html          # HTML test report
      ├── junit.xml            # JUnit XML (for CI/CD)
      ├── pytest.log           # Detailed test log
      ├── coverage.xml         # Coverage XML
      ├── .coverage            # Coverage data file
      └── htmlcov/             # Interactive HTML coverage
          └── index.html
```

## Coverage Summary

Latest coverage: **85%**

Run `poetry run python scripts.py` and open:
- `test-results/[latest]/htmlcov/index.html` for interactive coverage report
- `test-results/[latest]/report.html` for test results

## Test Statistics

- **Total Tests**: 195
- **OAuth Tests**: 17 (security + core)
- **All Tests Passing**: ✅
