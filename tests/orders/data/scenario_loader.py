"""Load and validate JSON scenarios used by the Orders integration tests.

The loader owns scenario-file access and structural validation only. Tests keep
scenario setup, API calls, transport checks, and behavioral assertions.
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


COUPON_SCENARIO_FILE = Path(__file__).with_name("coupon_scenarios.json")
REQUIRED_SCENARIO_FIELDS = {
    "name",
    "discount_type",
    "amount",
    "minimum_amount",
    "product_price_offset",
    "expected_outcome",
}


def load_coupon_scenarios(
    scenario_file: Path = COUPON_SCENARIO_FILE,
) -> list[dict[str, Any]]:
    """Read and validate the Coupon scenarios used by Order tests.

    The default file path is resolved relative to this module, so test
    collection does not depend on the current working directory.

    Args:
        scenario_file: JSON file containing the scenario records.

    Returns:
        A non-empty list of validated scenario mappings.

    Raises:
        FileNotFoundError: If the scenario JSON file is missing.
        ValueError: If the JSON is invalid or a scenario is incomplete or
            malformed.
    """
    try:
        scenarios = json.loads(scenario_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in Order Coupon scenario file {scenario_file}: {error}"
        ) from error

    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(f"Expected a non-empty JSON array in {scenario_file}.")

    scenario_names: set[str] = set()

    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ValueError(
                f"Scenario at index {index} in {scenario_file} must be an object."
            )

        missing_fields = REQUIRED_SCENARIO_FIELDS - scenario.keys()
        if missing_fields:
            raise ValueError(
                f"Scenario at index {index} is missing required field(s): "
                f"{', '.join(sorted(missing_fields))}."
            )

        name = scenario["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Scenario at index {index} must have a non-empty name.")
        if name in scenario_names:
            raise ValueError(f"Duplicate scenario name {name!r}.")
        scenario_names.add(name)

        for field in (
            "amount",
            "minimum_amount",
            "product_price_offset",
        ):
            if not isinstance(scenario[field], str):
                raise ValueError(
                    f"Scenario {name!r} field {field!r} must be a decimal string."
                )
            try:
                Decimal(scenario[field])
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError(
                    f"Scenario {name!r} field {field!r} must be a decimal string."
                ) from None

        if scenario["discount_type"] not in {"percent", "fixed_cart"}:
            raise ValueError(
                f"Scenario {name!r} has unsupported discount_type "
                f"{scenario['discount_type']!r}."
            )

        if scenario["expected_outcome"] == "applied":
            required_applied_fields = {
                "expected_discount",
                "expected_shipping_total",
            }
            missing_applied_fields = required_applied_fields - scenario.keys()
            if missing_applied_fields:
                raise ValueError(
                    f"Applied scenario {name!r} is missing field(s): "
                    f"{', '.join(sorted(missing_applied_fields))}."
                )
            for field in ("expected_discount", "expected_shipping_total"):
                if not isinstance(scenario[field], str):
                    raise ValueError(
                        f"Scenario {name!r} field {field!r} must be a decimal string."
                    )
                try:
                    Decimal(scenario[field])
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError(
                        f"Scenario {name!r} field {field!r} must be a decimal string."
                    ) from None
            if "free_shipping" in scenario and not isinstance(
                scenario["free_shipping"], bool
            ):
                raise ValueError(
                    f"Scenario {name!r} field 'free_shipping' must be a boolean."
                )

        elif scenario["expected_outcome"] == "rejected_below_minimum":
            required_error_fields = {
                "expected_error_code",
                "expected_error_message_contains",
            }
            missing_error_fields = required_error_fields - scenario.keys()
            if missing_error_fields:
                raise ValueError(
                    f"Rejected scenario {name!r} is missing field(s): "
                    f"{', '.join(sorted(missing_error_fields))}."
                )
        else:
            raise ValueError(
                f"Scenario {name!r} has unsupported expected_outcome "
                f"{scenario['expected_outcome']!r}."
            )

    return scenarios
