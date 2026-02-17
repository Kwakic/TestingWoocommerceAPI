# config_loader.py

"""
Shared configuration loader for all microservice test suites.

This module provides unified access to:
    - Active ENV (test/dev/staging/prod)
    - Active MACHINE (machine1/docker/etc.)
    - Base URL per microservice (loaded from service-specific config file)
    - DB configuration (securely provided via .env only)
    - API credentials
    - Auto-detection of microservice directory based on test execution path

Key design principles:
    ✔ No hardcoded microservice names
    ✔ Auto-import service config (API_HOSTS) dynamically
    ✔ Secure DB settings (NO DB_HOST inside repo service configs)
    ✔ One loader used across all plugins and utilities
"""

from __future__ import annotations

import os
import importlib
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Always load .env (safe no-op if missing)
load_dotenv()

# =====================================================================
#  SECTION 1: ENV + MACHINE
# =====================================================================

ENV = os.getenv("ENV", "test").lower()
MACHINE = os.getenv("MACHINE", "machine1").lower()


# =====================================================================
#  SECTION 2: Auto-detect microservice based on working directory
# =====================================================================

@lru_cache(maxsize=None)
def detect_service() -> str:
    """
    Detects the current microservice name.

    Detection order:
      1. SERVICE environment variable, if set.
      2. Look for 'tests/<service>/configs/config_<service>.py' starting
         from the current working directory and its parents.
      3. If cwd path contains '.../tests/<service>/...' extract <service>.
      4. If multiple candidates are present and the above heuristics cannot
         pick one, raise a RuntimeError with guidance.

    Returns:
        service name in lowercase (e.g. 'customers').

    Raises:
        RuntimeError when the service cannot be determined automatically.
    """
    # 1) Environment override
    svc_env = os.getenv("SERVICE")
    if svc_env:
        return svc_env.lower()

    cwd = Path.cwd()

    # 2) If cwd path includes tests/<service>/..., extract that service first
    parts = cwd.parts
    for idx, part in enumerate(parts[:-1]):
        if part == "tests" and idx + 1 < len(parts):
            candidate = parts[idx + 1]
            candidate_path = Path(*parts[: idx + 2])
            if _config_module_exists(candidate_path):
                return candidate.lower()
            # fallback: still keep candidate for later verification

    # 3) Walk ancestors to find a 'tests' directory with service configs
    candidates = _find_service_candidates_from_ancestors(cwd)
    if not candidates:
        raise RuntimeError(
            "Unable to auto-detect microservice. No 'tests/<service>/configs/config_<service>.py' "
            "modules were found in the current working directory or any parent directories. "
            "Please set the SERVICE environment variable to the target service (e.g. export SERVICE=customers) "
            "or run tests from the repository root."
        )

    # If only one candidate, return it
    if len(candidates) == 1:
        return next(iter(candidates)).lower()

    # If multiple candidates, try to pick one that matches cwd path
    for cand in candidates:
        if f"/tests/{cand}/" in str(cwd) or str(cwd).endswith(f"/tests/{cand}"):
            return cand.lower()

    # Ambiguous: present helpful error listing candidates
    sorted_list = sorted(candidates)
    raise RuntimeError(
        "Multiple microservice candidates found but none could be unambiguously selected.\n"
        f"Candidates: {sorted_list}\n"
        "Please set the SERVICE environment variable to one of the above (e.g. export SERVICE=customers)."
    )


def _find_service_candidates_from_ancestors(start: Path) -> set[str]:
    """
    Walk up from start to filesystem root and collect service names that
    appear under a 'tests' directory with the expected config file.

    Returns:
        A set of candidate service names (possibly empty).
    """
    found: set[str] = set()
    for ancestor in [start] + list(start.parents):
        tests_dir = ancestor / "tests"
        if tests_dir.is_dir():
            for entry in tests_dir.iterdir():
                if entry.is_dir():
                    cfg = entry / "configs" / f"config_{entry.name}.py"
                    if cfg.exists():
                        found.add(entry.name)
        # stop early if we found at least one candidate in this ancestor
        if found:
            return found
    return found


def _config_module_exists(path: Path) -> bool:
    """
    Helper to determine whether 'tests/<service>/configs/config_<service>.py'
    exists under `path` if path ends with 'tests/<service>' otherwise tries
    to detect under path/tests.
    """
    path = path.resolve()
    # if path itself is tests/<service> (i.e., path.parts ends with ['tests','<service>'])
    if path.name and path.parent.name == "tests":
        service = path.name
        return (path / "configs" / f"config_{service}.py").exists()

    # otherwise, try path/tests/*
    tests_dir = path / "tests"
    if tests_dir.is_dir():
        for entry in tests_dir.iterdir():
            if entry.is_dir() and (entry / "configs" / f"config_{entry.name}.py").exists():
                return True
    return False


# =====================================================================
#  SECTION 3: Dynamic import of per-service config
# =====================================================================

@lru_cache(maxsize=None)
def load_service_config(service: str):
    """
    Dynamically imports the microservice's config module.

    Expected layout:
        tests/<service>/configs/config_<service>.py

    The module must define:
        API_HOSTS = { "test": "...", "prod": "..." }

    Args:
        service: microservice name, e.g. "customers"

    Returns:
        Imported module

    Raises:
        ImportError if config module missing or malformed.
    """
    service = service.lower()
    module_path = f"tests.{service}.configs.config_{service}"

    try:
        module = importlib.import_module(module_path)
    except Exception as exc:
        raise ImportError(
            f"Failed to import config module for service '{service}'. "
            f"Expected module: {module_path}"
        ) from exc

    # Basic validation of the module shape
    if not hasattr(module, "API_HOSTS"):
        raise ImportError(
            f"Config module '{module_path}' does not define 'API_HOSTS'. "
            "Please ensure API_HOSTS is present and is a mapping from ENV->URL."
        )
    if not isinstance(getattr(module, "API_HOSTS"), dict):
        raise ImportError(
            f"'API_HOSTS' in module '{module_path}' must be a dict mapping env->url."
        )

    return module


# =====================================================================
#  SECTION 4: API Host Resolution
# =====================================================================

def get_api_host(service: Optional[str] = None) -> str:
    """
    Returns the shared API URL for the given microservice and active ENV.

    Args:
        service: optional override. If not provided, auto-detect is used.

    Returns:
        Base URL as a string.

    Raises:
        RuntimeError if API_HOSTS missing or ENV not found in API_HOSTS.
    """
    service = (service or detect_service()).lower()

    module = load_service_config(service)

    hosts = getattr(module, "API_HOSTS", None)
    if hosts is None:
        raise RuntimeError(
            f"Config module for '{service}' does not define API_HOSTS"
        )

    if ENV not in hosts:
        raise RuntimeError(
            f"ENV='{ENV}' missing from API_HOSTS in config_{service}"
        )

    return hosts[ENV]


# =====================================================================
#  SECTION 5: DB Configuration (secure from .env only)
# =====================================================================

def get_db_config() -> Dict[str, Any]:
    """
    Loads DB connection configuration from environment variables.
    This avoids storing DB_HOST values inside source code.

    Supported vars:
        DB_HOST
        DB_USER
        DB_PASS
        DB_NAME
        DB_PORT
        DB_SOCKET

    Returns:
        A dictionary with populated values (missing values omitted).
    """

    def get(key: str) -> Optional[str]:
        val = os.getenv(key)
        return val if val not in ("", None) else None

    cfg = {
        "host": get("DB_HOST"),
        "user": get("DB_USER"),
        "password": get("DB_PASS"),
        "database": get("DB_NAME"),
        "port": get("DB_PORT"),
        "socket": get("DB_SOCKET"),
    }

    return {k: v for k, v in cfg.items() if v is not None}


# =====================================================================
#  SECTION 6: Unified Config Object (Convenience)
# =====================================================================

def get_config() -> Dict[str, Any]:
    """
    Returns a strongly structured config dictionary for direct use by tests,
    helpers, and plugins.

    {
        "env": "test",
        "machine": "machine1",
        "service": "customers",
        "api_host": "...",
        "db": {...},
    }
    """
    service = detect_service()
    return {
        "env": ENV,
        "machine": MACHINE,
        "service": service,
        "api_host": get_api_host(service),
        "db": get_db_config()
    }


# =====================================================================
#  SECTION 7: Minimal debug helper
# =====================================================================

def debug_print() -> None:
    """Prints resolved configuration (for troubleshooting only)."""
    c = get_config()
    print("=== Framework Config ===")
    for k, v in c.items():
        print(f"{k}: {v}")
