from jose import jwt, JWTError

def test_jwt_error():
    secret = "secret"
    # Create a token with HS256 (valid)
    token_hs256 = jwt.encode({"sub": "user"}, secret, algorithm="HS256")
    
    # Create a token with NONE (invalid per our config)
    token_none = jwt.encode({"sub": "user"}, "", algorithm="none") # Note: jose might not let us encode 'none' easily without explicit allow
    
    print("Testing HS256 decode with HS256 allowed:")
    try:
        jwt.decode(token_hs256, secret, algorithms=["HS256"])
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting 'none' alg token with HS256 allowed:")
    try:
        # We simulate a token with alg='none' coming in
        # To bypass jose encode protection, we'll manually craft it or just valid RS256 if we had keys
        # For 'none': header={"alg": "none", "typ": "JWT"}
        # But jose supports 'none'.
        # Let's try to decode token_none expecting HS256
        jwt.decode(token_none, secret, algorithms=["HS256"])
        print("Success")
    except JWTError as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    test_jwt_error()
