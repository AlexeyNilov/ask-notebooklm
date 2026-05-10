from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import quote, urlencode

import httpx

QUERY_URL = (
    "https://notebooklm.google.com/_/LabsTailwindUi/data/google.internal.labs.tailwind."
    "orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed"
)
DEFAULT_BL = "boq_labs-tailwind-frontend_20260301.03_p0"
ALLOWED_COOKIE_DOMAINS = {".google.com", "notebooklm.google.com", ".googleusercontent.com"}
MINIMUM_REQUIRED_COOKIES = {"SID"}


class NotebookLMError(RuntimeError):
    pass


class NotebookLMValidationError(NotebookLMError):
    pass


class AuthRequiredError(NotebookLMError):
    pass


class NotebookLMTransientError(NotebookLMError):
    pass


class MalformedResponseError(NotebookLMError):
    pass


@dataclass(frozen=True)
class AskResult:
    answer: str
    conversation_id: str | None


class NotebookLMAskClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        csrf_token: str,
        session_id: str,
        cookies: dict[str, str],
    ) -> None:
        self.http_client = http_client
        self.csrf_token = csrf_token
        self.session_id = session_id
        self.cookies = cookies
        self._reqid_counter = 100000

    @classmethod
    async def from_storage_state(
        cls,
        http_client: httpx.AsyncClient,
        storage_state: dict[str, Any],
    ) -> NotebookLMAskClient:
        cookies = extract_auth_cookies(storage_state)
        csrf_token, session_id = await fetch_tokens(http_client, cookies)
        return cls(http_client, csrf_token, session_id, cookies)

    async def ask(self, notebook_id: str, question: str) -> AskResult:
        validate_ask_input(notebook_id, question)
        response_text = await self._post_question(notebook_id.strip(), question.strip())
        return parse_ask_response(response_text)

    async def _post_question(self, notebook_id: str, question: str) -> str:
        self._reqid_counter += 100000
        try:
            response = await self.http_client.post(
                build_query_url(self.session_id, self._reqid_counter),
                content=build_ask_body(notebook_id, question, self.csrf_token),
                headers=build_headers(self.cookies),
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as error:
            raise map_http_error(error) from error
        except httpx.TimeoutException as error:
            raise NotebookLMTransientError("NotebookLM ask request timed out.") from error
        except httpx.RequestError as error:
            raise NotebookLMTransientError(f"NotebookLM ask request failed: {error}") from error


def validate_ask_input(notebook_id: str, question: str) -> None:
    if not notebook_id or not notebook_id.strip():
        raise NotebookLMValidationError("Configured notebook ID is required.")
    if not question or not question.strip():
        raise NotebookLMValidationError("A non-empty question is required.")


def build_query_url(session_id: str, reqid: int) -> str:
    params = {
        "bl": DEFAULT_BL,
        "hl": "en",
        "_reqid": str(reqid),
        "rt": "c",
        "f.sid": session_id,
    }
    return f"{QUERY_URL}?{urlencode(params)}"


def build_ask_body(notebook_id: str, question: str, csrf_token: str) -> str:
    params = [
        [],
        question,
        None,
        [2, None, [1], [1]],
        str(uuid.uuid4()),
        None,
        None,
        notebook_id,
        1,
    ]
    params_json = json.dumps(params, separators=(",", ":"))
    f_req = quote(json.dumps([None, params_json], separators=(",", ":")))
    return f"f.req={f_req}&at={quote(csrf_token)}&"


def build_headers(cookies: dict[str, str]) -> dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Cookie": "; ".join(f"{name}={value}" for name, value in cookies.items()),
    }


async def fetch_tokens(http_client: httpx.AsyncClient, cookies: dict[str, str]) -> tuple[str, str]:
    try:
        response = await http_client.get(
            "https://notebooklm.google.com/",
            headers={"Cookie": build_cookie_header(cookies)},
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise map_http_error(error) from error
    except httpx.RequestError as error:
        raise NotebookLMTransientError(f"NotebookLM token request failed: {error}") from error
    return extract_tokens(response.text)


def build_cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def map_http_error(error: httpx.HTTPStatusError) -> NotebookLMError:
    status = error.response.status_code
    if status in (401, 403):
        return AuthRequiredError("NotebookLM authentication failed. Run the login tool.")
    if status == 429:
        return NotebookLMTransientError("NotebookLM API rate limit reached.")
    if status >= 500:
        return NotebookLMTransientError(f"NotebookLM server error: HTTP {status}.")
    return NotebookLMError(f"NotebookLM ask request failed: HTTP {status}.")


def extract_auth_cookies(storage_state: dict[str, Any]) -> dict[str, str]:
    cookies = {
        cookie["name"]: cookie["value"]
        for cookie in storage_state.get("cookies", [])
        if is_allowed_cookie(cookie)
    }
    missing = MINIMUM_REQUIRED_COOKIES - set(cookies)
    if missing:
        raise AuthRequiredError(f"Missing required NotebookLM auth cookies: {sorted(missing)}.")
    return cookies


def is_allowed_cookie(cookie: object) -> bool:
    if not isinstance(cookie, dict):
        return False
    return (
        cookie.get("domain") in ALLOWED_COOKIE_DOMAINS
        and bool(cookie.get("name"))
        and bool(cookie.get("value"))
    )


def extract_tokens(html: str) -> tuple[str, str]:
    csrf_token = extract_global_value(html, "SNlM0e")
    session_id = extract_global_value(html, "FdrFJe")
    if not csrf_token or not session_id:
        raise AuthRequiredError(
            "NotebookLM authentication tokens were not found. Run the login tool."
        )
    return csrf_token, session_id


def extract_global_value(html: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', html)
    return match.group(1) if match else None


def parse_ask_response(response_text: str) -> AskResult:
    answer = ""
    conversation_id = None
    for chunk in iter_response_chunks(strip_xssi_prefix(response_text)):
        chunk_answer, chunk_conversation_id = parse_answer_chunk(chunk)
        if chunk_answer and len(chunk_answer) > len(answer):
            answer = chunk_answer
            conversation_id = chunk_conversation_id
    if not answer:
        raise MalformedResponseError("NotebookLM response did not contain an answer.")
    return AskResult(answer=answer, conversation_id=conversation_id)


def strip_xssi_prefix(response_text: str) -> str:
    return response_text[4:] if response_text.startswith(")]}'") else response_text


def iter_response_chunks(response_text: str) -> list[str]:
    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    chunks: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].isdigit() and index + 1 < len(lines):
            chunks.append(lines[index + 1])
            index += 2
        else:
            chunks.append(lines[index])
            index += 1
    return chunks


def parse_answer_chunk(json_text: str) -> tuple[str | None, str | None]:
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return None, None
    for item in data if isinstance(data, list) else []:
        result = parse_response_item(item)
        if result[0]:
            return result
    return None, None


def parse_response_item(item: object) -> tuple[str | None, str | None]:
    if not is_response_item(item):
        return None, None
    response_item = cast(list[Any], item)
    try:
        inner = json.loads(response_item[2])
    except json.JSONDecodeError:
        return None, None
    first = inner[0] if isinstance(inner, list) and inner else None
    if not isinstance(first, list) or not isinstance(first[0], str):
        return None, None
    conversation_id = extract_conversation_id(first)
    return first[0], conversation_id


def is_response_item(item: object) -> bool:
    return (
        isinstance(item, list)
        and len(item) > 2
        and item[0] == "wrb.fr"
        and isinstance(item[2], str)
    )


def extract_conversation_id(first: list[Any]) -> str | None:
    if len(first) <= 2 or not isinstance(first[2], list) or not first[2]:
        return None
    return first[2][0] if isinstance(first[2][0], str) else None
