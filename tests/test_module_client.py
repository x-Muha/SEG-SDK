from __future__ import annotations

import os
import sys
import textwrap
import subprocess

import httpx2
import pytest
from httpx2 import URL

import seg
from seg import DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES


def reset_state() -> None:
    seg._reset_client()
    seg.api_key = None
    seg.base_url = None
    seg.timeout = DEFAULT_TIMEOUT
    seg.max_retries = DEFAULT_MAX_RETRIES
    seg.default_headers = None
    seg.default_query = None
    seg.http_client = None


@pytest.fixture(autouse=True)
def reset_state_fixture() -> None:
    reset_state()


def test_base_url_option() -> None:
    assert seg.base_url is None
    assert seg.chat._client.base_url == URL("https://sovereigneg.com/v1/")

    seg.base_url = "http://foo.com"

    assert seg.base_url == URL("http://foo.com")
    assert seg.chat._client.base_url == URL("http://foo.com")


def test_base_url_env_var() -> None:
    env = {**os.environ, "SEG_BASE_URL": "http://env.example/v1", "SEG_API_KEY": "fake-key"}
    env.pop("SEG_BASE_URL_UNUSED", None)
    code = textwrap.dedent(
        """
        import seg
        print(str(seg.chat._client.base_url))
        """
    )
    out = subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()
    assert out == "http://env.example/v1/"


def test_timeout_option() -> None:
    assert seg.timeout == seg.DEFAULT_TIMEOUT
    assert seg.chat._client.timeout == seg.DEFAULT_TIMEOUT

    seg.timeout = 3

    assert seg.timeout == 3
    assert seg.chat._client.timeout == 3


def test_max_retries_option() -> None:
    assert seg.max_retries == seg.DEFAULT_MAX_RETRIES
    assert seg.chat._client.max_retries == seg.DEFAULT_MAX_RETRIES

    seg.max_retries = 1

    assert seg.max_retries == 1
    assert seg.chat._client.max_retries == 1


def test_default_headers_option() -> None:
    assert seg.default_headers is None

    seg.default_headers = {"Foo": "Bar"}

    assert seg.default_headers["Foo"] == "Bar"
    assert seg.chat._client.default_headers["Foo"] == "Bar"


def test_default_query_option() -> None:
    assert seg.default_query is None
    assert seg.chat._client._custom_query == {}

    seg.default_query = {"Foo": {"nested": 1}}

    assert seg.default_query["Foo"] == {"nested": 1}
    assert seg.chat._client._custom_query["Foo"] == {"nested": 1}


def test_http_client_option() -> None:
    assert seg.http_client is None

    original_http_client = seg.chat._client._client
    assert original_http_client is not None

    new_client = httpx2.Client()
    seg.http_client = new_client

    assert seg.chat._client._client is new_client


def test_api_key_is_read_lazily() -> None:
    seg.api_key = "module-level-key"
    assert seg.chat._client.api_key == "module-level-key"
    assert seg.chat._client.auth_headers == {"Authorization": "Bearer module-level-key"}

    seg.api_key = "rotated-key"
    assert seg.chat._client.auth_headers == {"Authorization": "Bearer rotated-key"}


def test_all_resources_are_exposed() -> None:
    seg.api_key = "k"
    for name in ("chat", "embeddings", "images", "moderations", "models", "decisions"):
        assert getattr(seg, name)._client is seg.chat._client


def test_missing_key_errors_on_first_request() -> None:
    assert seg.api_key is None
    with pytest.raises(TypeError, match="Could not resolve authentication method"):
        seg.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
