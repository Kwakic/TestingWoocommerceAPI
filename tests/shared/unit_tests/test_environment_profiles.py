from __future__ import annotations

import os
from pathlib import Path

import pytest

from EcommerceAPI.src.configs.config_graphql import GRAPHQL_HOSTS, get_graphql_host
from EcommerceAPI.src.configs.config_loader import get_api_host, get_db_config
from EcommerceAPI.src.configs.runtime_config import get_config
from EcommerceAPI.src.utils.credentials_utility import get_db_credentials
from EcommerceAPI.src.utils.env_utils import load_profile_dotenv, profile_dotenv_path
from tests.coupons.configs.config_coupons import API_HOSTS as COUPON_HOSTS
from tests.customers.configs.config_customers import API_HOSTS as CUSTOMER_HOSTS
from tests.orders.configs.config_orders import API_HOSTS as ORDER_HOSTS
from tests.products.configs.config_products import API_HOSTS as PRODUCT_HOSTS


EXPECTED_REST_HOSTS = {
    "local": "http://localhost:8888/kwakiweb/wp-json/wc/v3/",
    "test": "http://localhost:8080/wp-json/wc/v3/",
    "docker": "http://wordpress/wp-json/wc/v3/",
    "ci": "http://localhost:8080/wp-json/wc/v3/",
}

EXPECTED_GRAPHQL_HOSTS = {
    "local": "http://localhost:8888/kwakiweb/graphql",
    "test": "http://localhost:8080/graphql",
    "docker": "http://wordpress/graphql",
    "ci": "http://localhost:8080/graphql",
}


@pytest.fixture(autouse=True)
def restore_profile_environment_after_test():
    """Keep profile-loader mutations local to each environment test."""
    profile_prefixes = ("DB_", "WC_", "WP_ADMIN_", "UI_")
    profile_names = {"API_ENV", "GRAPHQL_URL"}
    original_environment = {
        name: value
        for name, value in os.environ.items()
        if name.startswith(profile_prefixes) or name in profile_names
    }

    yield

    for name in tuple(os.environ):
        if name.startswith(profile_prefixes) or name in profile_names:
            os.environ.pop(name, None)
    os.environ.update(original_environment)


@pytest.mark.unit
def test_all_rest_entity_profiles_use_the_expected_endpoints():
    for hosts in (CUSTOMER_HOSTS, PRODUCT_HOSTS, ORDER_HOSTS, COUPON_HOSTS):
        assert {profile: hosts[profile] for profile in EXPECTED_REST_HOSTS} == (
            EXPECTED_REST_HOSTS
        )


@pytest.mark.unit
def test_graphql_profiles_use_the_expected_endpoints():
    assert {
        profile: GRAPHQL_HOSTS[profile] for profile in EXPECTED_GRAPHQL_HOSTS
    } == EXPECTED_GRAPHQL_HOSTS


@pytest.mark.unit
@pytest.mark.parametrize("profile", ["test", "docker", "ci"])
def test_non_wamp_profiles_select_the_docker_dotenv(tmp_path, monkeypatch, profile):
    (tmp_path / ".env").write_text(
        "API_ENV=test\nDB_HOST=127.0.0.1\nWC_KEY=docker-key\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.wamp").write_text(
        "API_ENV=local\nDB_HOST=127.0.0.1\nWC_KEY=wamp-key\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_ENV", profile)
    for name in ("DB_HOST", "WC_KEY"):
        monkeypatch.delenv(name, raising=False)

    assert profile_dotenv_path(project_root=tmp_path) == tmp_path / ".env"
    assert load_profile_dotenv(project_root=tmp_path) == tmp_path / ".env"
    assert os.environ["WC_KEY"] == "docker-key"


@pytest.mark.unit
def test_local_profile_loads_only_the_wamp_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "API_ENV=test\nDB_HOST=docker-db\nWC_KEY=docker-key\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.wamp").write_text(
        "API_ENV=local\nDB_HOST=wamp-db\nWC_KEY=wamp-key\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_ENV", "local")
    for name in ("DB_HOST", "WC_KEY"):
        monkeypatch.delenv(name, raising=False)

    assert profile_dotenv_path(project_root=tmp_path) == tmp_path / ".env.wamp"
    assert load_profile_dotenv(project_root=tmp_path) == tmp_path / ".env.wamp"
    assert os.environ["DB_HOST"] == "wamp-db"
    assert os.environ["WC_KEY"] == "wamp-key"


@pytest.mark.unit
def test_local_profile_does_not_fall_back_to_docker_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "API_ENV=test\nDB_HOST=docker-db\nWC_KEY=docker-key\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_ENV", "local")
    for name in ("DB_HOST", "WC_KEY"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(FileNotFoundError, match="API_ENV=local requires"):
        load_profile_dotenv(project_root=tmp_path)
    assert "DB_HOST" not in os.environ
    assert "WC_KEY" not in os.environ


@pytest.mark.unit
def test_local_profile_overrides_inherited_docker_credentials(tmp_path, monkeypatch):
    (tmp_path / ".env.wamp").write_text(
        "API_ENV=local\nDB_HOST=wamp-db\nDB_PASSWORD=wamp-password\n"
        "DB_DATABASE=wamp-database\nWC_KEY=wamp-key\nWC_SECRET=wamp-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("API_ENV", "local")
    monkeypatch.setenv("DB_HOST", "docker-db")
    monkeypatch.setenv("DB_PASSWORD", "docker-db-password")
    monkeypatch.setenv("DB_USER", "docker-db-user")
    monkeypatch.setenv("DB_DATABASE", "docker-database")
    monkeypatch.setenv("WC_KEY", "docker-key")
    monkeypatch.setenv("WC_SECRET", "docker-secret")
    monkeypatch.setenv("WP_ADMIN_APP_PASSWORD", "docker-graphql-password")
    monkeypatch.setenv("UI_ADMIN_PASSWORD", "docker-ui-password")
    monkeypatch.setenv("GRAPHQL_URL", "http://docker/graphql")

    assert load_profile_dotenv(project_root=tmp_path) == tmp_path / ".env.wamp"
    assert os.environ["DB_HOST"] == "wamp-db"
    assert os.environ["DB_PASSWORD"] == "wamp-password"
    assert os.environ["DB_DATABASE"] == "wamp-database"
    assert "DB_USER" not in os.environ
    assert os.environ["WC_KEY"] == "wamp-key"
    assert os.environ["WC_SECRET"] == "wamp-secret"
    assert "WP_ADMIN_APP_PASSWORD" not in os.environ
    assert "UI_ADMIN_PASSWORD" not in os.environ
    assert "GRAPHQL_URL" not in os.environ


@pytest.mark.unit
def test_active_profile_selects_matching_endpoints_and_db_contract():
    profile = (os.getenv("API_ENV") or os.getenv("ENV") or "test").lower()
    assert get_config(reload=True).ENV.lower() == profile
    assert get_api_host("customers") == EXPECTED_REST_HOSTS[profile]
    assert get_graphql_host() == EXPECTED_GRAPHQL_HOSTS[profile]

    db_env_names = {
        "host": "DB_HOST",
        "user": "DB_USER",
        "password": "DB_PASSWORD",
        "database": "DB_DATABASE",
        "port": "DB_PORT",
    }
    db_config = get_db_config()
    db_credentials = (
        get_db_credentials()
        if all(os.getenv(name) for name in db_env_names.values())
        else None
    )
    for config_name, env_name in db_env_names.items():
        if os.getenv(env_name):
            assert db_config[config_name] == os.environ[env_name]
            if db_credentials is not None:
                credential_name = (
                    "database" if config_name == "database" else config_name
                )
                assert str(db_credentials[credential_name]) == os.environ[env_name]


@pytest.mark.unit
def test_docker_credential_writer_only_targets_docker_dotenv():
    repo_root = Path(__file__).resolve().parents[3]
    writer = (repo_root / "scripts" / "write_env_credentials.sh").read_text(
        encoding="utf-8"
    )

    assert "[[ ! -f .env ]]" in writer
    assert 'grep -q "^${key}=" .env' in writer
    assert 'sed -i "s|^${key}=.*|${key}=${value}|" .env' in writer
    assert 'echo "${key}=${value}" >> .env' in writer
    assert ".env.wamp" not in writer
