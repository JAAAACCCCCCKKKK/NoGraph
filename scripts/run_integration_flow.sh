#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

LOG_FILE="${ROOT_DIR}/integration_server.log"
COOKIE_JAR=$(mktemp)
EMAIL="user@example.com"
ORIGINAL_USERNAME="testuser"
UPDATED_USERNAME="updateduser"
BASE_URL="http://127.0.0.1:8000"

cleanup() {
  local status=${1:-$?}
  if [[ -n "${TAIL_PID:-}" ]] && kill -0 "${TAIL_PID}" 2>/dev/null; then
    kill "${TAIL_PID}" 2>/dev/null || true
    wait "${TAIL_PID}" 2>/dev/null || true
  fi
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -f "${COOKIE_JAR}"
  return "${status}"
}
trap 'status=$?; cleanup "$status"; exit "$status"' EXIT

python manage.py runserver 0.0.0.0:8000 >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!

tail -n 30 -f "${LOG_FILE}" &
TAIL_PID=$!

printf 'Waiting for Django server to be ready'
for _ in {1..60}; do
  if curl -sSf "${BASE_URL}/" > /dev/null 2>&1; then
    printf '\nDjango server is ready.\n'
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    printf '\n'
    echo "Django server exited unexpectedly." >&2
    exit 1
  fi
  printf '.'
  sleep 1

done

if ! curl -sSf "${BASE_URL}/" >/dev/null 2>&1; then
  echo "Django server did not become ready in time" >&2
  exit 1
fi

json_payload() {
  python - "$@" <<'PY'
import json
import sys

args = sys.argv[1:]
if len(args) % 2:
    raise SystemExit("json_payload requires an even number of key/value arguments")

data = {args[i]: args[i + 1] for i in range(0, len(args), 2)}
print(json.dumps(data))
PY
}

assert_success() {
  RESPONSE=$1 python - <<'PY'
import json
import os
resp = json.loads(os.environ["RESPONSE"])
if resp.get("status") != "success":
    raise SystemExit("API call failed: " + json.dumps(resp))
PY
}

# Step 1: Request verification code
SEND_CODE_PAYLOAD=$(json_payload email "${EMAIL}")
SEND_CODE_RESPONSE=$(curl --fail-with-body -sS -X POST "${BASE_URL}/auth/sendcode/" \
  -H "Content-Type: application/json" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "${SEND_CODE_PAYLOAD}")
echo "Send code response: ${SEND_CODE_RESPONSE}"
assert_success "${SEND_CODE_RESPONSE}"

sleep 2

CODE=$(grep -oE 'Your verification code is: [0-9]+' "${LOG_FILE}" | awk '{print $NF}' | tail -n 1)
if [[ -z "${CODE}" ]]; then
  echo "Failed to retrieve verification code from server log" >&2
  exit 1
fi

echo "Retrieved verification code: ${CODE}"

# Step 2: Register/Login using the verification code
REGISTER_PAYLOAD=$(json_payload username "${ORIGINAL_USERNAME}" email "${EMAIL}" code "${CODE}")
REGISTER_RESPONSE=$(curl --fail-with-body -sS -X POST "${BASE_URL}/auth/verify/" \
  -H "Content-Type: application/json" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "${REGISTER_PAYLOAD}")
echo "Register response: ${REGISTER_RESPONSE}"
assert_success "${REGISTER_RESPONSE}"

TOKEN=$(RESPONSE="${REGISTER_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
print(resp['token'])
PY
)

echo "Received token: ${TOKEN}"
AUTH_HEADER="AUTH: Bearer ${TOKEN}"

# Step 3: Change username to the updated value
CHANGE_PAYLOAD=$(json_payload email "${EMAIL}" new_username "${UPDATED_USERNAME}")
CHANGE_RESPONSE=$(curl --fail-with-body -sS -X POST "${BASE_URL}/auth/changename/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "${CHANGE_PAYLOAD}")
echo "Change name response: ${CHANGE_RESPONSE}"
assert_success "${CHANGE_RESPONSE}"

# Step 4: Change username back to the original value
RESTORE_PAYLOAD=$(json_payload email "${EMAIL}" new_username "${ORIGINAL_USERNAME}")
RESTORE_RESPONSE=$(curl --fail-with-body -sS -X POST "${BASE_URL}/auth/changename/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "${RESTORE_PAYLOAD}")
echo "Restore name response: ${RESTORE_RESPONSE}"
assert_success "${RESTORE_RESPONSE}"

# Step 5: Logout
LOGOUT_PAYLOAD=$(json_payload email "${EMAIL}")
LOGOUT_RESPONSE=$(curl --fail-with-body -sS -X POST "${BASE_URL}/auth/logout/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "${LOGOUT_PAYLOAD}")
echo "Logout response: ${LOGOUT_RESPONSE}"
assert_success "${LOGOUT_RESPONSE}"

echo "Integration flow completed successfully."
