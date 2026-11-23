from pathlib import Path

import pytest

from EcommerceAPI.plugins.test_execution_lock import (
    ExecutionLockError,
    acquire_execution_lock,
    release_execution_lock,
)


pytestmark = [pytest.mark.shared, pytest.mark.unit, pytest.mark.pr]


def test_execution_lock_rejects_a_second_owner(tmp_path: Path) -> None:
    token = acquire_execution_lock(tmp_path, mode="test")

    with pytest.raises(ExecutionLockError, match="Another test execution"):
        acquire_execution_lock(tmp_path, mode="second-test")

    assert release_execution_lock(tmp_path, token)


def test_execution_lock_can_only_be_released_by_its_owner(tmp_path: Path) -> None:
    token = acquire_execution_lock(tmp_path, mode="test")

    assert not release_execution_lock(tmp_path, "not-the-owner")
    assert (tmp_path / ".test-execution.lock").is_dir()
    assert release_execution_lock(tmp_path, token)
