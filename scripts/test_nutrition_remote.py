#!/usr/bin/env python3
import sys
import uuid
import time
import requests
from datetime import datetime, timezone


def ok(name: str, r: requests.Response, codes):
    ok = r.status_code in codes
    print(f"{name}: {r.status_code} ({'OK' if ok else 'FAIL'})")
    if not ok:
        try:
            print(r.json())
        except Exception:
            print(r.text)
    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_nutrition_remote.py <BASE_URL> [--with-gam]")
        sys.exit(2)

    base = sys.argv[1].rstrip('/')
    with_gam = any(arg == "--with-gam" for arg in sys.argv[2:])

    # Register or login
    email = f"nutri-{uuid.uuid4().hex[:8]}@example.com"
    password = "test123"
    reg = requests.post(f"{base}/auth/register", json={"first_name":"Test","last_name":"User","email":email,"password":password}, timeout=30)
    if not ok("Register", reg, [200, 201]):
        # Try login if already exists
        print("Register failed; trying login...")
    login = requests.post(f"{base}/auth/login", json={"email":email,"password":password}, timeout=30)
    if not ok("Login", login, [200]):
        sys.exit(1)
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create child with schema tolerance: prefer date_of_birth; try dob alias on 422
    child_payload = {"name":"Dash Child","date_of_birth":"2023-08-01","gender":"male","region":"US"}
    c = requests.post(f"{base}/children", headers=headers, json=child_payload, timeout=30)
    if not ok("Create Child (date_of_birth)", c, [201]):
        # Try dob alias
        child_payload = {"name":"Dash Child","dob":"2023-08-01","gender":"male","region":"US"}
        c = requests.post(f"{base}/children", headers=headers, json=child_payload, timeout=30)
        if not ok("Create Child (dob)", c, [201]):
            sys.exit(1)
    child_id = c.json()["id"]

    # Targets with timing
    t0 = time.perf_counter()
    t = requests.get(f"{base}/nutrition/targets/{child_id}", headers=headers, timeout=30)
    t1 = time.perf_counter()
    if not ok("Targets", t, [200]):
        sys.exit(1)
    targets = t.json()
    # Validate flat numeric dict
    assert isinstance(targets.get("targets"), dict)
    for k, v in targets["targets"].items():
        assert isinstance(v, (int, float))

    # Daily totals (today) before meals
    today = datetime.now(tz=timezone.utc).date().isoformat()
    dt0 = time.perf_counter()
    d1 = requests.get(f"{base}/nutrition/daily_totals/{child_id}", headers=headers, params={"date": today}, timeout=30)
    dt1 = time.perf_counter()
    if not ok("Daily Totals (nutrition)", d1, [200]):
        sys.exit(1)
    totals_before = d1.json()

    # Attempt to log a meal (may fail if GPT unavailable)
    meal_payload = {
        "child_id": child_id,
        "meal_type": "breakfast",
        "meal_time": datetime.now(tz=timezone.utc).isoformat(),
        "input_method": "text",
        "raw_input": "Oatmeal with banana and 120ml milk"
    }
    m = requests.post(f"{base}/meals/log", headers=headers, json=meal_payload, timeout=30)
    ok("Log Meal", m, [201])

    # Daily totals after meal
    dt2 = time.perf_counter()
    d2 = requests.get(f"{base}/nutrition/daily_totals/{child_id}", headers=headers, params={"date": today}, timeout=30)
    dt3 = time.perf_counter()
    if not ok("Daily Totals (nutrition, after)", d2, [200]):
        sys.exit(1)
    dt_alias0 = time.perf_counter()
    d2_alias = requests.get(f"{base}/meals/daily_totals/{child_id}", headers=headers, params={"date": today}, timeout=30)
    dt_alias1 = time.perf_counter()
    if not ok("Daily Totals (meals alias)", d2_alias, [200]):
        sys.exit(1)

    after_nutrition = d2.json()
    after_alias = d2_alias.json()
    alias_equals = after_nutrition == after_alias

    summary = {
        "targets_sample": targets,
        "totals_before": totals_before,
        "totals_after": after_nutrition,
        "alias_equals": alias_equals,
        "timings_ms": {
            "targets": int((t1 - t0) * 1000),
            "daily_totals": int((dt1 - dt0) * 1000),
            "daily_totals_alias": int((dt_alias1 - dt_alias0) * 1000),
        }
    }
    if with_gam:
        # first call (after meal) expected to persist and return non-zero results
        gs0 = time.perf_counter()
        g1 = requests.get(f"{base}/gamification/summary/{child_id}", headers=headers, params={"date": today}, timeout=30)
        gs1 = time.perf_counter()
        ok("Gamification Summary", g1, [200])
        gam1 = g1.json() if g1.status_code == 200 else {}

        # second call (cached fast-path)
        gs2 = time.perf_counter()
        g2 = requests.get(f"{base}/gamification/summary/{child_id}", headers=headers, params={"date": today}, timeout=30)
        gs3 = time.perf_counter()
        ok("Gamification Summary (cached)", g2, [200])
        gam2 = g2.json() if g2.status_code == 200 else {}

        summary["gamification_summary_first"] = gam1
        summary["gamification_summary_second"] = gam2
        summary["timings_ms"]["gam_summary"] = int((gs1 - gs0) * 1000)
        summary["timings_ms"]["gam_summary_cached"] = int((gs3 - gs2) * 1000)
        try:
            assert gam1.get("daily_score",{}).get("score",0) > 0
            assert gam1.get("streak",{}).get("current",0) >= 1
            assert gam1.get("points_today",0) >= 10
        except AssertionError:
            print("Gamification assertions failed; payload:")
            print(gam1)
    print("\nSummary:")
    import json
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


