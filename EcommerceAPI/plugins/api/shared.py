import logging
import pytest

from EcommerceAPI.src.shared.helpers.cleanup_helpers import set_default_api_client
from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.utils.credentials_utility import (
    get_wc_api_keys,
    MissingCredentialsError,
)

log = logging.getLogger(__name__)


# -------------------------
# api_client fixture
# -------------------------
@pytest.fixture(scope="session")
def api_client(api_base_url: str):
    """
    Provide a session-scoped APIClient instance (transport + orchestration layer).

    Parameters
    ----------
    api_base_url : str
        Service-specific API base URL injected from the test layer.

    What it does:
    --------
    - Constructs a shared APIClient instance.
    - Performs a ONE-TIME environment validation (fail-fast gate).
    - Ensures API is reachable and credentials are valid BEFORE any test runs.
    - Prevents cascading failures (pagination loops, retry storms, noisy test runs).
    - Wires the instance into legacy cleanup helpers (best-effort).

    🔥 Environment Gate (critical behavior):
    --------------------------------------
    This fixture acts as a SESSION-LEVEL ENVIRONMENT VALIDATION GATE.

    It executes a lightweight, service-agnostic API call (`system_status`)
    to verify:
        - API is reachable
        - Authentication is valid
        - Service is operational

    If validation fails:
        → pytest.exit() is called immediately
        → test session is aborted
        → NO further tests are executed

    Design rationale:
    ----------------
    - Fail-safe by default (cannot be bypassed by tests or fixtures)
    - Runs once per session (efficient and deterministic)
    - Prevents N× repeated failures across test suite
    - Avoids CI duplication (no separate environment stage required)
    - Keeps preflight tests pure (they do not request api_client)

    Notes:
    ------
    - This is NOT a business logic check.
    - This is NOT a contract test.
    - This is infrastructure / environment validation.
    - The fixture intentionally controls global test execution flow.
    - Preflight tests remain unaffected (they do not request api_client).

    """

    import requests  # local import to avoid unnecessary dependency at module load

    # ------------------------------------------------------------------
    # 🔐 CREDENTIAL VALIDATION (RUN FIRST — BEFORE ANYTHING)
    # ------------------------------------------------------------------
    try:
        wc_key, wc_secret = get_wc_api_keys()
    except MissingCredentialsError as exc:
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            "Error: Missing WooCommerce credentials\n\n"
            "Detected issue:\n"
            f"- {exc}\n\n"
            "Expected configuration:\n"
            "- WC_KEY=<your_consumer_key>\n"
            "- WC_SECRET=<your_consumer_secret>\n\n"
            "Possible causes:\n"
            "- .env file not loaded\n"
            "- Environment variables not exported\n"
            "- Typo in variable names (WC_KEY / WC_SECRET)\n"
            "- Running outside configured environment\n",
            returncode=10,
        )

    if not wc_key.strip() or not wc_secret.strip():
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            "Error: WooCommerce credentials are EMPTY\n\n"
            "Detected issue:\n"
            f"- WC_KEY={'<empty>' if not wc_key.strip() else '<set>'}\n"
            f"- WC_SECRET={'<empty>' if not wc_secret.strip() else '<set>'}\n\n"
            "Expected configuration:\n"
            "- WC_KEY=<your_consumer_key>\n"
            "- WC_SECRET=<your_consumer_secret>\n\n"
            "Possible causes:\n"
            "- WC_KEY=\n"
            "- WC_SECRET=\n"
            "- Incorrect .env formatting (missing values)\n"
            "- Quoted empty values in environment\n",
            returncode=10,
        )

    # ------------------------------------------------------------------
    # 🚀 ONLY NOW create API client
    # ------------------------------------------------------------------
    api_client = APIClient(base_url=api_base_url)

    # ------------------------------------------------------------------
    # 🔥 ENVIRONMENT VALIDATION GATE (runs once per session)
    # ------------------------------------------------------------------
    try:
        resp = api_client.get(
            "system_status"
        )  # system_status" is a real, valid WooCommerce REST API endpoint
    except (requests.RequestException, RuntimeError) as exc:
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            f"Error: Unable to reach API ({exc})\n\n"
            "Possible causes:\n"
            "- API service is down\n"
            "- Incorrect API_BASE_URL\n"
            "- Network/DNS issues\n",
            returncode=10,
        )

    # ------------------------------------------------------------------
    # Explicit status validation (fail by inclusion, not exclusion)
    # ------------------------------------------------------------------
    if resp.status_code == 401:
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            "Error: Authentication failed (401 Unauthorized)\n\n"
            "Possible causes:\n"
            "- Missing or invalid WC_KEY / WC_SECRET\n"
            "- Incorrect environment configuration (.env)\n\n"
            f"Response:\n{resp.text}\n",
            returncode=10,
        )

    elif resp.status_code >= 500:
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            f"Error: Server returned {resp.status_code}\n\n"
            "Possible causes:\n"
            "- WooCommerce is not fully initialized\n"
            "- Backend service failure\n\n"
            f"Response:\n{resp.text}\n",
            returncode=10,
        )

    elif resp.status_code != 200:
        pytest.exit(
            "\n"
            "🚨 ENVIRONMENT GATE FAILED — NOT A TEST FAILURE\n\n"
            f"API URL: {api_base_url}\n"
            f"Error: Unexpected status {resp.status_code} on system_status check\n\n"
            "Possible causes:\n"
            "- system_status endpoint not available in this environment\n"
            "- Wrong API_ENV or base URL misconfiguration\n\n"
            f"Response:\n{resp.text}\n",
            returncode=10,
        )

    log.info(
        "✅ Environment validation passed (API reachable, auth OK). Base URL: %s",
        api_base_url,
    )

    # ------------------------------------------------------------------
    # Best-effort wiring into legacy cleanup helpers.
    # ------------------------------------------------------------------
    if callable(set_default_api_client):
        try:
            set_default_api_client(api_client)
        except Exception as exc:
            log.warning("Failed to wire default API client: %s", exc)

    return api_client
