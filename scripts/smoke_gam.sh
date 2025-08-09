#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-"https://tinytummy-production.up.railway.app"}

echo "Using BASE_URL=$BASE_URL"

EMAIL="smoke_$(date -u +%s)@example.com"
PASSWORD='Test1234!'
FIRST='Smoke'
LAST='User'
TODAY=$(date -u +%F)

curl -sS -X POST "$BASE_URL/auth/register" -H 'Content-Type: application/json' -d '{"first_name":"'"$FIRST"'","last_name":"'"$LAST"'","email":"'"$EMAIL"'","password":"'"$PASSWORD"'"}' >/dev/null || true

TOKEN=$(curl -sS -X POST "$BASE_URL/auth/login" -H 'Content-Type: application/json' -d '{"email":"'"$EMAIL"'","password":"'"$PASSWORD"'"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

CHILD_ID=$(curl -sS -X POST "$BASE_URL/children" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"name":"Smoke Kid","date_of_birth":"2024-06-01","gender":"male","region":"US"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

curl -sS -X POST "$BASE_URL/meals/log" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"child_id":"'"$CHILD_ID"'","meal_type":"breakfast","input_method":"text","meal_time":"'"${TODAY}T09:00:00Z"'","raw_input":"Oatmeal + banana + milk"}' >/dev/null

SUM=$(curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/gamification/summary/$CHILD_ID?date=$TODAY")
TR=$(curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/meals/trends/$CHILD_ID?days=7")

# Move the meal to yesterday
YDAY=$(date -u -v-1d +%F 2>/dev/null || date -u -d 'yesterday' +%F)
MID=$(curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/meals/$CHILD_ID" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d[0]["id"])')
curl -sS -X PATCH "$BASE_URL/meals/$MID" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"meal_time":"'"${YDAY}T09:00:00Z"'"}' >/dev/null

# Delete the meal
curl -sS -X DELETE "$BASE_URL/meals/$MID" -H "Authorization: Bearer $TOKEN" >/dev/null

printf '{"summary":%s,"trends":%s,"ok":true}\n' "$SUM" "$TR"

