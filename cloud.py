"""One-time Wonderfree cloud authentication for local key retrieval."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import secrets
import string
from typing import Any

from aiohttp import ClientError, ClientSession
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .const import REGION_CHINA, REGION_EUROPE, REGION_NORTH_AMERICA

_APP_ID = "277"
_APP_VERSION = "3.6.5"
_LOGIN_PATH = "/v2/enduser/enduserapi/emailPwdLogin"
_DEVICE_LIST_PATH = "/v2/binding/enduserapi/userDeviceList"
_REQUEST_TIMEOUT = 20
_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class WonderfreeCloudRegion:
    """Wonderfree OEM cloud settings for one account region."""

    base_url: str
    user_domain: str
    user_domain_secret: str


REGIONS = {
    REGION_EUROPE: WonderfreeCloudRegion(
        base_url="https://iot-api.acceleronix.io",
        user_domain="E.SP.4294967410",
        user_domain_secret="3aRNUwWahjyANa7WfBK2wCCkxCexB6nXxKJwXxfePvzf",
    ),
    REGION_NORTH_AMERICA: WonderfreeCloudRegion(
        base_url="https://iot-api.landecia.com",
        user_domain="U.SP.8589934603",
        user_domain_secret="pUTp5goB1bLinprRQMmK3EPiiuPiGrJtKUNptWRXVmP",
    ),
    REGION_CHINA: WonderfreeCloudRegion(
        base_url="https://iot-api.quectelcn.com",
        user_domain="C.DM.5903.1",
        user_domain_secret="EufftRJSuWuVY7c6txzGifV9bJcfXHAFa7hXY5doXSn7",
    ),
}


class WonderfreeCloudError(Exception):
    """Base Wonderfree cloud error."""


class WonderfreeCloudConnectionError(WonderfreeCloudError):
    """Wonderfree cloud could not be reached."""


class WonderfreeCloudAuthenticationError(WonderfreeCloudError):
    """Wonderfree rejected the account credentials or region."""


class WonderfreeCloudDeviceNotFoundError(WonderfreeCloudError):
    """The discovered device is not bound to the account."""


class WonderfreeCloudResponseError(WonderfreeCloudError):
    """Wonderfree returned an unexpected response."""


def _encrypt_password(password: str, random_value: str) -> str:
    """Reproduce the password encryption used by the Wonderfree app."""
    md5_hex = hashlib.md5(
        random_value.encode(), usedforsecurity=False
    ).hexdigest().upper()
    key = md5_hex[8:24].encode()
    iv = key[8:] + key[:8]
    padder = padding.PKCS7(128).padder()
    padded = padder.update(password.encode()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode()


def _build_login_payload(
    email: str,
    password: str,
    region: WonderfreeCloudRegion,
    random_value: str,
) -> dict[str, str]:
    """Build the signed Wonderfree email login form."""
    encrypted_password = _encrypt_password(password, random_value)
    signature = hashlib.sha256(
        (
            email
            + encrypted_password
            + random_value
            + region.user_domain_secret
        ).encode()
    ).hexdigest()
    return {
        "pwd": encrypted_password,
        "email": email,
        "random": random_value,
        "userDomain": region.user_domain,
        "signature": signature,
    }


def _extract_device_page(response: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Return a normalized device list and total page count."""
    data = response.get("data")
    if not isinstance(data, dict):
        raise WonderfreeCloudResponseError("Device response has no data object")
    devices = data.get("list")
    if not isinstance(devices, list):
        raise WonderfreeCloudResponseError("Device response has no list")
    pages = data.get("pages", 1)
    if not isinstance(pages, int) or pages < 1:
        pages = 1
    return [device for device in devices if isinstance(device, dict)], pages


class WonderfreeCloudClient:
    """Fetch a local auth key using a short-lived Wonderfree cloud session."""

    def __init__(self, session: ClientSession, region: str) -> None:
        try:
            self._region = REGIONS[region]
        except KeyError as err:
            raise ValueError(f"Unsupported Wonderfree region: {region}") from err
        self._session = session

    @staticmethod
    def _headers(access_token: str | None = None) -> dict[str, str]:
        headers = {
            "appVersion": _APP_VERSION,
            "appSystemType": "android",
            "appId": _APP_ID,
            "X-Q-Language": "en",
        }
        if access_token:
            headers["Authorization"] = access_token
        return headers

    async def _request_json(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                self._region.base_url + path,
                timeout=_REQUEST_TIMEOUT,
                **kwargs,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise WonderfreeCloudConnectionError from err
        if not isinstance(payload, dict):
            raise WonderfreeCloudResponseError("Wonderfree response is not an object")
        return payload

    async def _login(self, email: str, password: str) -> str:
        alphabet = string.ascii_letters + string.digits
        random_value = "".join(secrets.choice(alphabet) for _ in range(16))
        payload = await self._request_json(
            "POST",
            _LOGIN_PATH,
            headers=self._headers(),
            data=_build_login_payload(email, password, self._region, random_value),
        )
        if payload.get("code") != 200:
            raise WonderfreeCloudAuthenticationError
        data = payload.get("data")
        access_token = data.get("accessToken") if isinstance(data, dict) else None
        token = access_token.get("token") if isinstance(access_token, dict) else None
        if not isinstance(token, str) or not token:
            raise WonderfreeCloudResponseError("Login response has no access token")
        return token

    async def async_get_auth_key(
        self, email: str, password: str, device_key: str
    ) -> str:
        """Log in, find a bound device, and return its local authentication key."""
        access_token = await self._login(email, password)
        page = 1
        pages = 1
        while page <= pages:
            payload = await self._request_json(
                "GET",
                _DEVICE_LIST_PATH,
                headers=self._headers(access_token),
                params={
                    "page": str(page),
                    "pageSize": str(_PAGE_SIZE),
                    "isAssociation": "false",
                },
            )
            if payload.get("code") != 200:
                raise WonderfreeCloudResponseError("Device list request was rejected")
            devices, pages = _extract_device_page(payload)
            for device in devices:
                if device.get("deviceKey") != device_key:
                    continue
                auth_key = device.get("authKey")
                if not isinstance(auth_key, str) or not auth_key:
                    raise WonderfreeCloudResponseError("Bound device has no auth key")
                return auth_key
            page += 1
        raise WonderfreeCloudDeviceNotFoundError
