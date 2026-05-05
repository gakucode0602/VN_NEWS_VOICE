#!/usr/bin/env bash
set -euo pipefail

GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-}"
RAG_HEALTH_URL="${RAG_HEALTH_URL:-}"
RABBITMQ_API_URL="${RABBITMQ_API_URL:-}"
RABBITMQ_USER="${RABBITMQ_USER:-}"
RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD:-}"

if [[ -z "$GATEWAY_BASE_URL" ]]; then
  echo "ERROR: GATEWAY_BASE_URL is required"
  exit 2
fi

# if [[ -z "$RAG_HEALTH_URL" ]]; then
#   RAG_HEALTH_URL="$GATEWAY_BASE_URL/api/v1/health"
# fi

FAILS=0

pass() { echo "PASS: $1 - $2"; }
fail() { echo "FAIL: $1 - $2"; FAILS=$((FAILS+1)); }

# Retry curl up to N times with a delay between attempts.
curl_with_retry() {
  local url="$1"
  local retries="${2:-5}"
  local delay="${3:-10}"
  local attempt=1
  while [[ "$attempt" -le "$retries" ]]; do
    if RESULT=$(curl -fsS "$url" 2>/dev/null); then
      echo "$RESULT"
      return 0
    fi
    echo "  [retry $attempt/$retries] $url not ready, waiting ${delay}s..."
    sleep "$delay"
    attempt=$((attempt+1))
  done
  return 1
}

# 1) Gateway health
if BODY=$(curl -fsS "$GATEWAY_BASE_URL/health"); then
  if echo "$BODY" | grep -qi "ok"; then
    pass "Gateway health" "HTTP OK"
  else
    fail "Gateway health" "Unexpected body"
  fi
else
  fail "Gateway health" "Request failed"
fi

# 2) Auth JWKS — retry up to 5x (Spring Boot may still be starting after redeploy)
if JWKS=$(curl_with_retry "$GATEWAY_BASE_URL/api/.well-known/jwks.json" 5 12); then
  if echo "$JWKS" | grep -q '"keys"'; then
    pass "Auth JWKS" "keys field detected"
  else
    fail "Auth JWKS" "keys field missing"
  fi
else
  fail "Auth JWKS" "Request failed"
fi

# # 3) RAG health
# if RAG=$(curl -fsS "$RAG_HEALTH_URL"); then
#   if echo "$RAG" | grep -qi '"status"'; then
#     pass "RAG health" "status field detected"
#   else
#     pass "RAG health" "HTTP OK"
#   fi
# else
#   fail "RAG health" "Request failed"
# fi

# 4) Optional RabbitMQ API
if [[ -n "$RABBITMQ_API_URL" ]]; then
  if [[ -z "$RABBITMQ_USER" || -z "$RABBITMQ_PASSWORD" ]]; then
    fail "RabbitMQ API" "RABBITMQ_USER/RABBITMQ_PASSWORD required"
  else
    if RABBIT=$(curl -fsS -u "$RABBITMQ_USER:$RABBITMQ_PASSWORD" "$RABBITMQ_API_URL/api/overview"); then
      if echo "$RABBIT" | grep -q '"rabbitmq_version"'; then
        pass "RabbitMQ API" "overview reachable"
      else
        fail "RabbitMQ API" "rabbitmq_version missing"
      fi
    else
      fail "RabbitMQ API" "Request failed"
    fi
  fi
else
  pass "RabbitMQ API" "Skipped (RABBITMQ_API_URL not set)"
fi

if [[ "$FAILS" -gt 0 ]]; then
  echo "Smoke tests failed: $FAILS check(s)."
  exit 1
fi

echo "All smoke tests passed."
