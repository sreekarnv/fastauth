# Installation

FastAuth can be installed via pip, Poetry, or from source.

## Requirements

- Python 3.11 or higher
- FastAPI 0.125.0 or higher

## Install from PyPI

```bash
pip install fastauth
```

## Install with Poetry

```bash
poetry add fastauth
```

## Install from Source

```bash
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth
pip install .
```

## Development Installation

For development with all dev dependencies:

```bash
git clone https://github.com/sreekarnv/fastauth.git
cd fastauth
poetry install
```

This installs FastAuth along with testing, linting, and documentation tools.

## Verify Installation

```python
import fastauth
print(fastauth.__version__)
```
