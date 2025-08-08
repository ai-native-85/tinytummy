#!/usr/bin/env python3
"""
E2E test for /children creation (no 307 redirects).

Usage:
  python3 scripts/test_children_remote.py <base_url>
"""

import sys
import uuid
import requests


def must_status(name: str, resp: requests.Response, codes: list[int]):
    ok = resp.status_code in codes
    print(f"{name}: {resp.status_code} ({'OK' if ok else 'FAIL'})")
    if not ok:
        try:
            print("Response:", resp.json())
        except Exception:
            print("Response:", resp.text)
        raise SystemExit(1)
    return resp


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_children_remote.py <base_url>")
        sys.exit(2)

    base = sys.argv[1].rstrip('/')

    # Create user and login
    email = f"child-{uuid.uuid4().hex[:8]}@example.com"
    password = "test123"
    reg = {"first_name":"Test","last_name":"User","email":email,"password":password}
    r = requests.post(f"{base}/auth/register", json=reg, timeout=30)
    must_status("Register", r, [200, 201])
    r = requests.post(f"{base}/auth/login", json={"email": email, "password": password}, timeout=30)
    r = must_status("Login", r, [200])
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Simulate Lovable frontend payload using "dob" alias
    payload = {
        "name": "Baby A",
        "dob": "2023-08-02",
        "gender": "Male",
        "allergies": ["peanuts"],
        "dietary_restrictions": ["vegetarian"],
        "region": "US"
    }

    # Test without trailing slash
    r = requests.post(f"{base}/children", json=payload, headers=headers, allow_redirects=False, timeout=30)
    must_status("Children create (no slash)", r, [201])

    # Test with trailing slash
    r = requests.post(f"{base}/children/", json=payload, headers=headers, allow_redirects=False, timeout=30)
    must_status("Children create (slash)", r, [201])

    print("\n/children creation OK without redirects")


if __name__ == "__main__":
    main()


