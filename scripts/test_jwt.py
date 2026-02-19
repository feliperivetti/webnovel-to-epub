import base64
import json

import jwt  # PyJWT


def _make_none_token(payload: dict) -> str:
    """Manually craft a JWT with alg='none' (PyJWT blocks this by design)."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "none", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{body}."


def test_jwt_error():
    secret = "secret"

    # 1) Valid HS256 token – should decode fine
    token_hs256 = jwt.encode({"sub": "user"}, secret, algorithm="HS256")
    decoded = jwt.decode(token_hs256, secret, algorithms=["HS256"])
    assert decoded["sub"] == "user"

    # 2) Manually crafted alg='none' token – must be rejected
    token_none = _make_none_token({"sub": "user"})
    try:
        jwt.decode(token_none, secret, algorithms=["HS256"])
        assert False, "Should have raised InvalidTokenError for alg='none'"
    except jwt.InvalidTokenError:
        pass  # Expected


if __name__ == "__main__":
    test_jwt_error()
    print("All JWT tests passed!")
