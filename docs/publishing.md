# Publishing to PyPI Guide

This guide covers publishing FastAuth to the Python Package Index (PyPI).

## Prerequisites

### 1. PyPI Account Setup

**Create accounts on both PyPI and TestPyPI:**

- **PyPI** (production): https://pypi.org/account/register/
- **TestPyPI** (testing): https://test.pypi.org/account/register/

### 2. Configure API Tokens

**Generate API tokens** (recommended over passwords):

1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: "FastAuth CLI"
4. Scope: "Entire account" (or specific project after first upload)
5. Copy the token (starts with `pypi-`)

**Repeat for TestPyPI**: https://test.pypi.org/manage/account/token/

### 3. Configure Poetry

Store tokens in Poetry config:

```bash
# TestPyPI token
poetry config pypi-token.testpypi your-testpypi-token

# PyPI token
poetry config pypi-token.pypi your-pypi-token
```

Or create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
```

### 4. Install Build Tools

```bash
pip install --upgrade build twine
```

## Pre-Publication Checklist

Before publishing, ensure everything is ready:

### Code Quality
- [ ] All tests passing (`poetry run test-cov`)
- [ ] Coverage at 85%+
- [ ] Linting passing (`poetry run ruff check .`)
- [ ] Code formatted (`poetry run black .`)
- [ ] No security vulnerabilities

### Documentation
- [ ] README.md is complete and accurate
- [ ] CHANGELOG.md is updated
- [ ] All docs/ files are current
- [ ] API reference is complete
- [ ] Examples are tested and working

### Package Configuration
- [ ] Version number bumped in `pyproject.toml`
- [ ] Dependencies are correct and minimal
- [ ] Package metadata is accurate (author, description, keywords, etc.)
- [ ] License is specified (MIT)
- [ ] README is referenced
- [ ] Python version requirement is correct (>=3.11)

### Manual Testing
- [ ] All endpoints tested manually (see [manual-testing.md](manual-testing.md))
- [ ] OAuth flow tested end-to-end
- [ ] RBAC tested with roles/permissions
- [ ] Session management tested
- [ ] Account management tested
- [ ] Error handling verified

### Legal/Compliance
- [ ] No secrets in code
- [ ] No copyrighted material
- [ ] License file included
- [ ] Third-party licenses reviewed

## Version Numbering

FastAuth follows [Semantic Versioning](https://semver.org/):

**Format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Current Version Plan

- **v0.1.0**: Initial release (completed)
- **v0.2.0**: OAuth 2.0 + test infrastructure (current)
- **v0.3.0**: Additional OAuth providers (planned)
- **v1.0.0**: Production-ready stable release (future)

### Bumping Version

Edit `pyproject.toml`:

```toml
[tool.poetry]
name = "fastauth"
version = "0.2.0"  # Update this
```

Also update in:

```toml
[project]
version = "0.2.0"  # Update this too
```

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info

# Or on Windows
rmdir /s dist
rmdir /s build
```

### 2. Build with Poetry

```bash
# Build both wheel and source distribution
poetry build
```

**Output**:
```
Building fastauth (0.2.0)
  - Building sdist
  - Built fastauth-0.2.0.tar.gz
  - Building wheel
  - Built fastauth-0.2.0-py3-none-any.whl
```

**Verify build**:
```bash
ls -l dist/
# Should show:
# fastauth-0.2.0-py3-none-any.whl
# fastauth-0.2.0.tar.gz
```

### 3. Inspect the Package

```bash
# Check package contents
tar -tzf dist/fastauth-0.2.0.tar.gz | head -20

# Or for wheel
unzip -l dist/fastauth-0.2.0-py3-none-any.whl | head -20
```

**Verify**:
- [ ] Source files included (fastauth/*.py)
- [ ] No sensitive files (.env, credentials)
- [ ] No unnecessary files (tests/, examples/)
- [ ] README included
- [ ] LICENSE included

## Testing on TestPyPI

**Always test on TestPyPI first!**

### 1. Publish to TestPyPI

```bash
poetry publish -r testpypi
```

Or with twine:

```bash
twine upload --repository testpypi dist/*
```

**Expected output**:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading fastauth-0.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading fastauth-0.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://test.pypi.org/project/fastauth/0.2.0/
```

### 2. Verify on TestPyPI

Visit: https://test.pypi.org/project/fastauth/

**Check**:
- [ ] Version number is correct
- [ ] Description displays properly
- [ ] README renders correctly
- [ ] Links work (GitHub, documentation)
- [ ] Dependencies are listed
- [ ] Classifiers are correct
- [ ] Files are downloadable

### 3. Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fastauth

# Verify installation
python -c "import fastauth; print(fastauth.__version__)"
# Should print: 0.2.0

# Test basic import
python
>>> from fastauth import auth_router, Settings
>>> from fastauth.core.users import create_user
>>> # Test that imports work
```

### 4. Quick Functional Test

Create `test_install.py`:

```python
from fastapi import FastAPI
from fastauth import auth_router

app = FastAPI()
app.include_router(auth_router)

# Run: uvicorn test_install:app
# Visit: http://localhost:8000/docs
# Verify: All endpoints appear
```

**If any issues**, fix them, bump version to `0.2.1`, rebuild, and republish to TestPyPI.

## Publishing to PyPI (Production)

**Only proceed if TestPyPI testing was successful!**

### 1. Final Checks

- [ ] TestPyPI version tested and working
- [ ] No issues found during testing
- [ ] CHANGELOG updated with release notes
- [ ] Git tag created for release
- [ ] All tests passing

### 2. Create Git Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0: OAuth 2.0 + Test Infrastructure"

# Push tag to GitHub
git push origin v0.2.0
```

### 3. Publish to PyPI

```bash
poetry publish
```

Or with twine:

```bash
twine upload dist/*
```

**Confirmation prompt**:
```
Publishing fastauth (0.2.0) to PyPI
Username: __token__
Password: [hidden]
```

**Expected output**:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading fastauth-0.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uploading fastauth-0.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View at:
https://pypi.org/project/fastauth/0.2.0/
```

### 4. Verify on PyPI

Visit: https://pypi.org/project/fastauth/

**Check**:
- [ ] Version is live
- [ ] Description correct
- [ ] README renders properly
- [ ] Badge links work
- [ ] Download files available

### 5. Test Installation from PyPI

```bash
# New environment
python -m venv prod-test
source prod-test/bin/activate

# Install from PyPI
pip install sreekarnv-fastauth

# Verify
python -c "import fastauth; print(fastauth.__version__)"
```

## Post-Publication Tasks

### 1. Create GitHub Release

1. Go to: https://github.com/yourusername/fastauth/releases/new
2. Tag: `v0.2.0`
3. Title: `v0.2.0 - OAuth 2.0 + Test Infrastructure`
4. Description: Copy from CHANGELOG.md
5. Attach: dist files (optional)
6. Publish release

### 2. Update Documentation

**Update README.md**:
```markdown
## Installation

```bash
pip install sreekarnv-fastauth
```
```

**Update main README** to reference version `0.2.0`.

### 3. Announce Release

**GitHub Discussions**:
- Announce new release
- Highlight key features
- Link to documentation

**Social Media** (if applicable):
- Twitter/X
- Reddit (r/Python, r/FastAPI)
- Dev.to
- LinkedIn

### 4. Monitor

**Check**:
- [ ] Download stats on PyPI
- [ ] GitHub issues for installation problems
- [ ] User feedback
- [ ] Error reports

## Common Issues and Solutions

### "Version already exists"

**Cause**: Version number already published.

**Solution**: Bump version number and rebuild.

```bash
# In pyproject.toml
version = "0.2.1"  # Increment patch version

# Rebuild and republish
poetry build
poetry publish
```

### "Authentication failed"

**Cause**: Invalid or expired API token.

**Solution**: Generate new token and update config.

```bash
poetry config pypi-token.pypi your-new-token
```

### "Invalid package metadata"

**Cause**: Missing or incorrect fields in `pyproject.toml`.

**Solution**: Validate with:

```bash
poetry check
```

Fix any errors in `pyproject.toml`.

### "README not rendering"

**Cause**: Markdown issues or invalid format.

**Solution**:
- Check README locally with Markdown viewer
- Validate on https://commonmark.org/help/
- Ensure `readme = "README.md"` in pyproject.toml

### "Dependencies not installing"

**Cause**: Missing or incorrect dependency specifications.

**Solution**: Check dependency versions:

```toml
dependencies = [
    "fastapi[all] (>=0.125.0,<0.126.0)",
    "sqlmodel (>=0.0.27,<0.0.28)",
    # etc.
]
```

### "File too large"

**Cause**: Package includes large files.

**Solution**: Update `.gitignore` and exclude from package:

```toml
[tool.poetry]
exclude = [
    "tests",
    "examples",
    "docs",
    ".github",
    "*.log",
]
```

## Updating an Existing Release

**You cannot replace a published version.** Must publish new version.

### For Critical Bugs

1. Fix bug
2. Bump patch version: `0.2.0` → `0.2.1`
3. Update CHANGELOG
4. Build and publish
5. (Optional) Yank old version if critically broken

### Yanking a Release

**Use only for critical issues (security, broken package).**

```bash
# Via PyPI web interface
# Project > Manage > Options > Delete/Yank

# Mark as "yanked" (users can still install with specific version)
# Or delete permanently (NOT recommended)
```

## Automation (Optional)

### GitHub Actions for Auto-Publish

`.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: |
          pip install poetry
          poetry config pypi-token.pypi ${{ secrets.PYPI_TOKEN }}

      - name: Build and publish
        run: |
          poetry build
          poetry publish
```

**Setup**:
1. Add PyPI token as GitHub secret: `PYPI_TOKEN`
2. Create GitHub release
3. Package auto-publishes

## Checklist: Ready to Publish?

### Pre-Build
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] All tests passing
- [ ] Manual testing complete
- [ ] Documentation updated
- [ ] Git committed and pushed

### Build
- [ ] Old builds cleaned
- [ ] `poetry build` successful
- [ ] Package contents verified
- [ ] No sensitive files included

### Test on TestPyPI
- [ ] Published to TestPyPI
- [ ] TestPyPI page looks correct
- [ ] Installation from TestPyPI works
- [ ] Basic functionality tested

### Publish to PyPI
- [ ] Git tag created
- [ ] `poetry publish` successful
- [ ] PyPI page verified
- [ ] Installation from PyPI works
- [ ] GitHub release created

### Post-Publish
- [ ] Announcement posted
- [ ] Monitoring set up
- [ ] README reflects new version
- [ ] Celebrate! 🎉

---

## Quick Reference Commands

```bash
# Bump version in pyproject.toml first

# Clean build
rm -rf dist/ build/ *.egg-info

# Build
poetry build

# Test on TestPyPI
poetry publish -r testpypi

# Test install
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fastauth

# Create git tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Publish to PyPI
poetry publish

# Verify
pip install sreekarnv-fastauth
python -c "import fastauth; print(fastauth.__version__)"
```

---

**You're now ready to publish FastAuth to PyPI!** 🚀

Good luck with your first (or next) release!
