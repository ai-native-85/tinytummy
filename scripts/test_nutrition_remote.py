#!/usr/bin/env python3
import sys
import uuid
import requests


def must_status(name: str, r: requests.Response, codes):
    ok = r.status_code in codes
    print(f"{name}: {r.status_code} ({'OK' if ok else 'FAIL'})")
    if not ok:
        try:
            print(r.json())
        except Exception:
            print(r.text)
        sys.exit(1)
    return r


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_nutrition_remote.py <base_url>")
        sys.exit(2)

    base = sys.argv[1].rstrip('/')

    # Register/login
    email = f"nutri-{uuid.uuid4().hex[:8]}@example.com"
    password = "test123"
    reg = requests.post(f"{base}/auth/register", json={"first_name":"Test","last_name":"User","email":email,"password":password}, timeout=30)
    must_status("Register", reg, [200, 201])
    login = requests.post(f"{base}/auth/login", json={"email":email,"password":password}, timeout=30)
    login = must_status("Login", login, [200])
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create child
    c = requests.post(f"{base}/children", headers=headers, json={"name":"Dash Child","date_of_birth":"2023-08-01","gender":"male"}, timeout=30)
    c = must_status("Create Child", c, [201])
    child_id = c.json()["id"]

    # Targets
    t = requests.get(f"{base}/nutrition/targets/{child_id}", headers=headers, timeout=30)
    t = must_status("Targets", t, [200])
    print("Targets JSON:", t.json())

    # Daily totals (today)
    from datetime import datetime
    today = datetime.utcnow().date().isoformat()
    d = requests.get(f"{base}/nutrition/daily_totals/{child_id}", headers=headers, params={"date": today}, timeout=30)
    d = must_status("Daily Totals", d, [200])
    print("Daily Totals JSON:", d.json())

    print("\nNutrition endpoints OK")


if __name__ == "__main__":
    main()


