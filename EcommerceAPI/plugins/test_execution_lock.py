"""Prevent local host and Docker test runs from sharing a mutable environment.

The Docker runner temporarily changes the local WordPress home URLs so OAuth
requests use the Docker service hostname. A repository-level lock prevents a
host pytest session from using that same WordPress environment at the same
time. The Makefile owns the lock for its managed workflows; direct pytest
sessions acquire and release it here.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest


LOCK_DIRECTORY = ".test-execution.lock"
LOCK_OWNER_FILE = "owner.txt"
MAKE_LOCK_HELD_ENV = "TEST_EXECUTION_LOCK_HELD_BY_MAKE"

_active_locks: dict[int, tuple[Path, str]] = {}


class ExecutionLockError(RuntimeError):
    """Raised when another test execution already owns the local lock."""


def _read_lock_owner(lock_path: Path) -> str:
    owner_path = lock_path / LOCK_OWNER_FILE
    try:
        return owner_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "owner metadata is not available yet"


def acquire_execution_lock(root: Path, mode: str = "pytest") -> str:
    """Create the repository lock directory atomically and return its token."""
    lock_path = root / LOCK_DIRECTORY

    try:
        lock_path.mkdir()
    except FileExistsError as exc:
        raise ExecutionLockError(
            f"Another test execution holds {lock_path}. "
            f"Owner: {_read_lock_owner(lock_path)}. "
            "Wait for it to finish. If it was interrupted, verify no test is "
            "running before removing the stale lock directory."
        ) from exc

    token = uuid.uuid4().hex
    owner_text = f"token={token}\n" f"pid={os.getpid()}\n" f"mode={mode}\n"
    try:
        (lock_path / LOCK_OWNER_FILE).write_text(owner_text, encoding="utf-8")
    except OSError:
        lock_path.rmdir()
        raise

    return token


def release_execution_lock(root: Path, token: str) -> bool:
    """Release the lock only when its owner token matches this process."""
    lock_path = root / LOCK_DIRECTORY
    owner_path = lock_path / LOCK_OWNER_FILE

    try:
        owner = owner_path.read_text(encoding="utf-8")
    except OSError:
        return False

    if f"token={token}\n" not in owner:
        return False

    try:
        owner_path.unlink()
        lock_path.rmdir()
    except OSError:
        return False

    return True


def pytest_sessionstart(session: pytest.Session) -> None:
    """Acquire a host lock once for the pytest controller process."""
    config = session.config

    # Make owns a wider lock around setup + tests for `make run` and
    # `make test-docker`; xdist workers also rely on their controller's lock.
    if os.getenv(MAKE_LOCK_HELD_ENV) == "1" or hasattr(config, "workerinput"):
        return

    root = Path(config.rootpath)
    try:
        token = acquire_execution_lock(root)
    except ExecutionLockError as exc:
        pytest.exit(str(exc), returncode=2)

    _active_locks[id(config)] = (root, token)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Release a direct pytest session's lock after reporting has finished."""
    active_lock = _active_locks.pop(id(config), None)
    if active_lock is None:
        return

    root, token = active_lock
    if not release_execution_lock(root, token):
        sys.stderr.write(
            f"[WARNING] Could not safely release the test execution lock in {root}.\n"
        )
