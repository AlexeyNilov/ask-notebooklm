import json
from urllib.parse import parse_qs

import httpx
import pytest

from ask_notebooklm.notebooklm_client import (
    AuthRequiredError,
    MalformedResponseError,
    NotebookLMAskClient,
    NotebookLMTransientError,
    NotebookLMValidationError,
    extract_auth_cookies,
    extract_tokens,
)


def storage_state() -> dict:
    return {
        "cookies": [
            {"name": "SID", "value": "sid-cookie", "domain": ".google.com"},
            {"name": "HSID", "value": "hsid-cookie", "domain": ".google.com"},
        ],
        "origins": [],
    }


def streamed_answer(answer: str = "NotebookLM answer") -> str:
    inner = json.dumps(
        [[answer, None, ["server-conversation-id", 1], None, [None, None, None, [], 1]]]
    )
    outer = json.dumps([["wrb.fr", None, inner]])
    return ")]}'\n123\n" + outer


def test_extract_auth_cookies_keeps_google_cookie_values():
    cookies = extract_auth_cookies(storage_state())

    assert cookies == {"SID": "sid-cookie", "HSID": "hsid-cookie"}


def test_extract_auth_cookies_rejects_missing_sid():
    with pytest.raises(AuthRequiredError, match="SID"):
        extract_auth_cookies({"cookies": [], "origins": []})


def test_extract_tokens_reads_csrf_and_session_id_from_html():
    html = '{"SNlM0e":"csrf-token","FdrFJe":"session-id"}'

    assert extract_tokens(html) == ("csrf-token", "session-id")


@pytest.mark.anyio
async def test_from_storage_state_fetches_homepage_tokens_before_ask():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, text='{"SNlM0e":"csrf-token","FdrFJe":"session-id"}')
        return httpx.Response(200, text=streamed_answer())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = await NotebookLMAskClient.from_storage_state(http_client, storage_state())
        result = await client.ask("notebook-123", "What matters?")

    assert result.answer == "NotebookLM answer"
    assert requests[0].method == "GET"
    assert requests[0].headers["Cookie"] == "SID=sid-cookie; HSID=hsid-cookie"


@pytest.mark.anyio
async def test_ask_posts_question_to_read_only_notebook_and_returns_answer():
    captured_request: httpx.Request | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, text=streamed_answer())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})
        result = await client.ask("notebook-123", "What matters?")

    assert result.answer == "NotebookLM answer"
    assert result.conversation_id == "server-conversation-id"
    assert captured_request is not None
    assert "GenerateFreeFormStreamed" in str(captured_request.url)
    assert captured_request.url.params["f.sid"] == "session-id"
    body = parse_qs(captured_request.content.decode("utf-8"))
    assert body["at"] == ["csrf-token"]
    assert "What matters?" in body["f.req"][0]
    assert "notebook-123" in body["f.req"][0]


@pytest.mark.anyio
async def test_ask_rejects_empty_question_before_network_call():
    async with httpx.AsyncClient(transport=httpx.MockTransport(no_requests)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(NotebookLMValidationError, match="question"):
            await client.ask("notebook-123", " ")


@pytest.mark.anyio
async def test_ask_maps_auth_http_status_to_reauthentication_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(AuthRequiredError, match="login"):
            await client.ask("notebook-123", "What matters?")


@pytest.mark.anyio
async def test_ask_maps_rate_limit_to_transient_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(NotebookLMTransientError, match="rate"):
            await client.ask("notebook-123", "What matters?")


@pytest.mark.anyio
async def test_ask_maps_timeout_to_transient_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(NotebookLMTransientError, match="timed out"):
            await client.ask("notebook-123", "What matters?")


@pytest.mark.anyio
async def test_ask_rejects_malformed_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=")]}'\n[]")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(MalformedResponseError, match="answer"):
            await client.ask("notebook-123", "What matters?")


@pytest.mark.anyio
async def test_ask_rejects_response_with_malformed_inner_chunk():
    async def handler(request: httpx.Request) -> httpx.Response:
        chunk = json.dumps([["wrb.fr", None, "{"]])
        return httpx.Response(200, text=")]}'\n123\n" + chunk)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = NotebookLMAskClient(http_client, "csrf-token", "session-id", {"SID": "sid-cookie"})

        with pytest.raises(MalformedResponseError, match="answer"):
            await client.ask("notebook-123", "What matters?")


async def no_requests(request: httpx.Request) -> httpx.Response:
    raise AssertionError("network should not be called")
