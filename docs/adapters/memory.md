# Memory Adapter

An in-memory user adapter for **testing and development**. No database, no setup — data lives in a Python dict and is lost when the process exits.

## Usage

```python
from fastauth.adapters.memory import MemoryUserAdapter

config = FastAuthConfig(
    adapter=MemoryUserAdapter(),
    ...
)
```

## When to use it

- Unit tests — fast, zero-dependency fixtures
- Prototyping — spin up a working auth server without any database
- CI pipelines — no external services needed

## Limitations

- Data is not persisted between restarts
- No `token_adapter`, `oauth_adapter`, or `role_adapter` implementations
  (use the `SQLAlchemyAdapter` when you need those)
- Not suitable for multi-process deployments (each process has its own memory)

## Memory session backend

For OAuth state storage or database-session strategy in tests, use the memory session backend:

```python
from fastauth.session_backends.memory import MemorySessionBackend

config = FastAuthConfig(
    ...,
    oauth_state_store=MemorySessionBackend(),
)
```
