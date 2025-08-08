#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-"https://tinytummy-production.up.railway.app"}

echo "Healthz:"
curl -s "$BASE_URL/healthz"; echo

EMAIL="smoke-$(date +%s)@example.com"
PASS="test123"

echo "Register or ignore if exists"
curl -s -X POST "$BASE_URL/auth/register" -H 'Content-Type: application/json' --data '{"first_name":"Test","last_name":"User","email":"'$EMAIL'","password":"'$PASS'"}' >/dev/null || true

echo "Login"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" -H 'Content-Type: application/json' --data '{"email":"'$EMAIL'","password":"'$PASS'"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
echo "Token prefix: ${TOKEN:0:12}..."

echo "Create child"
CHILD=$(curl -s -X POST "$BASE_URL/children" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' --data '{"name":"Smoke Child","date_of_birth":"2023-08-01","gender":"male","region":"US"}')
CHILD_ID=$(python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" <<< "$CHILD")
echo "Child ID: $CHILD_ID"

TODAY=$(date -u +%F)

echo "Targets timing"
time -p curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/nutrition/targets/$CHILD_ID" >/dev/null

echo "Daily totals (nutrition) timing"
time -p curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/nutrition/daily_totals/$CHILD_ID?date=$TODAY" >/dev/null

echo "Daily totals (meals alias) timing"
time -p curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/meals/daily_totals/$CHILD_ID?date=$TODAY" >/dev/null

NUTR=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/nutrition/daily_totals/$CHILD_ID?date=$TODAY")
MEAL=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/meals/daily_totals/$CHILD_ID?date=$TODAY")

echo "Equal:"
[ "$NUTR" = "$MEAL" ] && echo true || echo false

echo "nutrition:"; echo "$NUTR"
echo "meals alias:"; echo "$MEAL"


