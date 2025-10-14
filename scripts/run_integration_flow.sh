#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="server.log"
COOKIE_JAR=$(mktemp)
EMAIL="user@example.com"
ORIGINAL_USERNAME="testuser"
UPDATED_USERNAME="updateduser"
BASE_URL="http://127.0.0.1:8000"

cleanup() {
  if kill -0 ${SERVER_PID} 2>/dev/null; then
    kill ${SERVER_PID} 2>/dev/null || true
    wait ${SERVER_PID} 2>/dev/null || true
  fi
  rm -f "${COOKIE_JAR}"
}

# Start Django development server in background
python manage.py runserver 0.0.0.0:8000 > "${LOG_FILE}" 2>&1 &
SERVER_PID=$!
trap cleanup EXIT

# Wait for server to be ready
SERVER_READY=false
for _ in {1..30}; do
    if curl -sSf "${BASE_URL}/" > /dev/null; then
        SERVER_READY=true
        break
    fi
    if ! kill -0 ${SERVER_PID} 2>/dev/null; then
        break
    fi
    sleep 1
done

if [[ "${SERVER_READY}" != true ]]; then
    echo "Django server did not become ready in time" >&2
    exit 1
fi

# Step 1: Request verification code
SEND_CODE_RESPONSE=$(curl -sS -X POST "${BASE_URL}/auth/sendcode/" \
  -H "Content-Type: application/json" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "{\"email\":\"${EMAIL}\"}")
echo "Send code response: ${SEND_CODE_RESPONSE}"

RESPONSE="${SEND_CODE_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
if resp.get('status') != 'success':
    raise SystemExit('Send code failed: ' + json.dumps(resp))
PY

sleep 2

# Extract the latest verification code from the server log
CODE=$(grep -oP 'Your verification code is: \K[0-9]+' "${LOG_FILE}" | tail -n 1)
if [[ -z "${CODE}" ]]; then
    echo "Failed to retrieve verification code from server log" >&2
    exit 1
fi

echo "Retrieved verification code: ${CODE}"

# Step 2: Register/Login using the verification code
REGISTER_RESPONSE=$(curl -sS -X POST "${BASE_URL}/auth/verify/" \
  -H "Content-Type: application/json" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "{\"username\":\"${ORIGINAL_USERNAME}\",\"email\":\"${EMAIL}\",\"code\":\"${CODE}\"}")
echo "Register response: ${REGISTER_RESPONSE}"

TOKEN=$(RESPONSE="${REGISTER_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
if resp.get('status') != 'success':
    raise SystemExit('Registration/Login failed: ' + json.dumps(resp))
print(resp['token'])
PY
)

echo "Received token: ${TOKEN}"

AUTH_HEADER="AUTH: Bearer ${TOKEN}"

# Step 3: Change username to the updated value
CHANGE_RESPONSE=$(curl -sS -X POST "${BASE_URL}/auth/changename/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "{\"email\":\"${EMAIL}\",\"new_username\":\"${UPDATED_USERNAME}\"}")
echo "Change name response: ${CHANGE_RESPONSE}"

RESPONSE="${CHANGE_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
if resp.get('status') != 'success':
    raise SystemExit('Change name failed: ' + json.dumps(resp))
PY

# Step 4: Change username back to the original value
RESTORE_RESPONSE=$(curl -sS -X POST "${BASE_URL}/auth/changename/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "{\"email\":\"${EMAIL}\",\"new_username\":\"${ORIGINAL_USERNAME}\"}")
echo "Restore name response: ${RESTORE_RESPONSE}"

RESPONSE="${RESTORE_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
if resp.get('status') != 'success':
    raise SystemExit('Restore name failed: ' + json.dumps(resp))
PY

# Step 5: Logout
LOGOUT_RESPONSE=$(curl -sS -X POST "${BASE_URL}/auth/logout/" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HEADER}" \
  -c "${COOKIE_JAR}" \
  -b "${COOKIE_JAR}" \
  -d "{\"email\":\"${EMAIL}\"}")
echo "Logout response: ${LOGOUT_RESPONSE}"

RESPONSE="${LOGOUT_RESPONSE}" python - <<'PY'
import json
import os
resp = json.loads(os.environ['RESPONSE'])
if resp.get('status') != 'success':
    raise SystemExit('Logout failed: ' + json.dumps(resp))
PY
