# utilities/env_utils.py

import os


def env_bool(varname: str, default: bool = False) -> bool:
    """
    It is a tiny parsing utility, not a config system.
        - It converts environment variable strings to booleans.
        - Interprets "1", "true", "yes", "on" (case-insensitive) as True.
        - Enforces allowed truthy values
        - Prevents mistakes

    Interpret environment variables like FAIL_ON_EMPTY_LIST or DEBUG
    as boolean flags in a human-friendly way.

    Why:
        Environment variables are always strings (even if set to "true" or "0").
        This helper safely converts them to actual booleans.

    Behavior:
        - If the variable is unset → returns the provided default.
        - If set, trims spaces and lowercases its value.
        - Interprets these strings as True:
              "1", "true", "yes", "on"
          Everything else is treated as False.

    Example:
        >>> os.environ["FAIL_ON_EMPTY_LIST"] = "True"
        >>> env_bool("FAIL_ON_EMPTY_LIST")
        True

        >>> os.environ["FAIL_ON_EMPTY_LIST"] = "0"
        >>> env_bool("FAIL_ON_EMPTY_LIST")
        False

        >>> env_bool("MISSING_VAR", default=True)
        True

    It standardizes meaning:
        - Environment variables are always strings.
        - env_bool() defines what “true” means in your framework.

    Without it:
    | Team    | Value |
    | ------- | ----- |
    | Team A  | TRUE  |
    | Team B  | true  |
    | CI      | 1     |
    | Docker  | yes   |
    | Windows | True  |

    With env_bool():
        - All of them mean the same thing.
    This is not convenience — this is contract enforcement.

    """
    val = os.getenv(varname)
    if val is None:
        return default  # Not set → fallback to default
    return val.strip().lower() in ("1", "true", "yes", "on")


"""
🧩 How it actually works in your test:

In your test_schema_validation, you use a fixture like fail_on_empty_list (from your large_conf.py) that calls 
_env_bool("FAIL_ON_EMPTY_LIST").
So:
- In local runs, if you execute:
pytest --fail-on-empty-list
the CLI flag overrides environment variables.

 - In CI/CD (e.g., GitHub Actions):
 env:
  FAIL_ON_EMPTY_LIST: "true"
→ The helper converts "true" → True.

✅ This ensures the same boolean behavior regardless of where it’s set — CLI, .env, or YAML.
"""