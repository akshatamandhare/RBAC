from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class APIClient:
    base_url: str
    timeout: int = 30

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def login(self, username: str, password: str) -> dict[str, Any]:
        resp = requests.post(
            self._url("/auth/login"),
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        self._raise_for_error(resp)
        return resp.json()

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        resp = requests.post(
            self._url("/auth/refresh"),
            json={"refresh_token": refresh_token},
            timeout=self.timeout,
        )
        self._raise_for_error(resp)
        return resp.json()

    def profile(self, access_token: str) -> dict[str, Any]:
        resp = requests.get(
            self._url("/auth/profile"),
            headers=self._auth_header(access_token),
            timeout=self.timeout,
        )
        self._raise_for_error(resp)
        return resp.json()

    def chat(self, access_token: str, query: str, top_k: int = 5) -> dict[str, Any]:
        resp = requests.post(
            self._url("/chat/query"),
            headers=self._auth_header(access_token),
            json={"query": query, "top_k": top_k},
            timeout=self.timeout,
        )
        if resp.status_code == 401:
            raise PermissionError("Session expired or unauthorized")
        self._raise_for_error(resp)
        return resp.json()

    @staticmethod
    def _auth_header(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"API {response.status_code}: {detail}")
