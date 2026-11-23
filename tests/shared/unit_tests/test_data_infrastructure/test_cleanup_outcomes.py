"""Exercise teardown with simulated WooCommerce DELETE responses."""

from collections import Counter, defaultdict
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from EcommerceAPI.plugins.cleanup_reporting import EntityCleanup
from EcommerceAPI.src.shared.helpers.cleanup_helpers import cleanup_items

pytestmark = [pytest.mark.shared, pytest.mark.unit, pytest.mark.pr]


def test_cleanup_counts_only_confirmed_deletions_and_continues_after_failure():
    delete = Mock(
        side_effect=[
            SimpleNamespace(status_code=403),
            TimeoutError("no response for ID 4040"),
            SimpleNamespace(status_code=404),
            SimpleNamespace(status_code=200),
            SimpleNamespace(status_code=204),
        ]
    )
    summary = []
    outcomes = Counter()

    deleted = cleanup_items(
        "coupons",
        [1, 2, 3, 4, 4, 5, 6],
        delete,
        summary_log=summary,
        total_created=6,
        already_deleted_ids={6},
        outcomes=outcomes,
    )

    assert delete.call_args_list == [
        call(f"coupons/{i}", params={"force": True}) for i in (1, 2, 3, 4, 5)
    ]
    assert deleted == {4, 5}
    assert outcomes == {"deleted": 2, "missing": 1, "failed": 2, "skipped": 1}
    assert summary == [
        "coupon: 2 deleted, 1 not found (HTTP 404), "
        "1 skipped (already deleted during test execution), "
        "1 skipped (duplicate), 2 failed (6 registered)"
    ]


@pytest.fixture
def cleanup_totals():
    # Simulated DELETEs belong only to this test's report.
    totals = defaultdict(EntityCleanup)
    yield totals
    assert totals["customers"].registered == {"7", "8"}
    assert totals["customers"].outcomes == Counter(deleted=1, failed=1)


@pytest.fixture
def all_resources():
    """Observe the real UI finalizer through its module-registry interface."""
    delete = Mock(
        side_effect=[SimpleNamespace(status_code=500), SimpleNamespace(status_code=200)]
    )
    mark_deleted = Mock()
    yield SimpleNamespace(
        entities={"customers": SimpleNamespace(delete_method=delete)},
        mark_deleted=mark_deleted,
    )
    assert delete.call_args_list == [
        call("customers/7", params={"force": True}),
        call("customers/8", params={"force": True}),
    ]
    mark_deleted.assert_called_once_with("customers", "8")


def test_ui_teardown_marks_only_confirmed_ids(ui_resources):
    ui_resources("customers", "7")
    ui_resources("customers", "8")
    ui_resources("customers", "8")
