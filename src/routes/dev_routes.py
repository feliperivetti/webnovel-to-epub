"""Local token issuer for exercising JWT authentication through Swagger."""

import time
from ipaddress import ip_address
from urllib.parse import urlsplit

import jwt
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from src.config import get_settings


router = APIRouter(prefix="/dev", tags=["Local development"])
settings = get_settings()
TOKEN_LIFETIME_SECONDS = 3600


def _is_loopback(host: str) -> bool:
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


class LocalTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = TOKEN_LIFETIME_SECONDS


@router.post("/token", response_model=LocalTokenResponse)
async def issue_local_token(request: Request, response: Response):
    """Generate a one-hour test JWT, then paste access_token into Authorize.

    Requires DEBUG=true, API_JWT_SECRET and a loopback connection. This helper
    issues a fixed local identity with action=generate-epub.
    """
    host = request.url.hostname or ""
    if (
        not settings.DEBUG
        or not request.client
        or not _is_loopback(request.client.host)
        or not (host == "localhost" or _is_loopback(host))
    ):
        raise HTTPException(status_code=404, detail="Not found")

    # The API otherwise permits cross-origin requests. A remote web page must
    # not be able to use that policy to obtain a token from a local server.
    origin = request.headers.get("origin")
    if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
        raise HTTPException(status_code=403, detail="Same-origin requests only")
    referer = request.headers.get("referer")
    if referer:
        source = urlsplit(referer)
        if (source.scheme, source.netloc) != (request.url.scheme, request.url.netloc):
            raise HTTPException(status_code=403, detail="Same-origin requests only")

    if not settings.API_JWT_SECRET:
        raise HTTPException(status_code=409, detail="Configure API_JWT_SECRET in .env first")

    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "local-test",
            "tier": "premium",
            "action": "generate-epub",
            "iat": now,
            "exp": now + TOKEN_LIFETIME_SECONDS,
        },
        settings.API_JWT_SECRET,
        algorithm="HS256",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return LocalTokenResponse(access_token=token)
