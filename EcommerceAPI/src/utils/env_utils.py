# utils/env_utils.py

import os
from pathlib import Path

from dotenv import load_dotenv


def profile_dotenv_path(
    api_env: str | None = None,
    project_root: Path | None = None,
) -> Path:
    """Return the private environment file for the selected execution profile.

    WAMP is deliberately isolated in `.env.wamp`; selecting it must never
    fall back to the Docker `.env` if the WAMP file is missing.
    """
    profile = (
        (api_env or os.getenv("API_ENV") or os.getenv("ENV", "test")).strip().lower()
    )
    filename = ".env.wamp" if profile == "local" else ".env"
    root = project_root or Path(__file__).resolve().parents[3]
    return root / filename


def load_profile_dotenv(
    api_env: str | None = None,
    project_root: Path | None = None,
) -> Path | None:
    """Load only the dotenv file belonging to the selected API profile."""
    profile = (
        (api_env or os.getenv("API_ENV") or os.getenv("ENV", "test")).strip().lower()
    )
    env_path = profile_dotenv_path(api_env=profile, project_root=project_root)
    if not env_path.is_file():
        if profile == "local":
            raise FileNotFoundError(
                "API_ENV=local requires the ignored .env.wamp file. "
                "Copy .env.wamp.example to .env.wamp and fill in the existing WAMP settings."
            )
        return None
    # The dedicated WAMP profile is authoritative: it must not inherit Docker
    # credentials accidentally exported in the parent shell or IDE process.
    if profile == "local":
        for name in tuple(os.environ):
            if name.startswith(("DB_", "WC_", "WP_ADMIN_", "UI_")) or name in {
                "GRAPHQL_URL",
            }:
                os.environ.pop(name, None)
    load_dotenv(dotenv_path=env_path, override=(profile == "local"))
    return env_path


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
