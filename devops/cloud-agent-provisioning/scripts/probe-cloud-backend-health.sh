#!/usr/bin/env bash
# probe-cloud-backend-health.sh
#
# Reachability probe for maritime.sh BEFORE launching a deploy loop that
# would otherwise burn attempts on a known-broken upstream.
#
# Usage:
#   bash probe-cloud-backend-health.sh           # quiet
#   bash probe-cloud-backend-health.sh verbose   # full timing per call

set -e
VERBOSE=${1:-}

echo "== maritime.sh dashboard / API reachability =="
curl -s -o /dev/null -w "  HTTP %{http_code}  time=%{time_total}s\n" --max-time 8 https://maritime.sh
curl -s -o /dev/null -w "  HTTP %{http_code}  time=%{time_total}s  path=/docs/cli\n" --max-time 8 https://maritime.sh/docs/cli

echo ""
echo "== maritime.sh upstream VM provisioner (Hetzner, 162.55.88.160:9500) =="
# 162.55.0.0/16 is Hetzner Online (Germany). /vms is POST-only; GET will fail
# cleanly with "405" or similar \u2014 the question is just whether the host is up.
curl -s -o /dev/null -w "  HTTP %{http_code}  time=%{time_total}s  endpoint=/vms\n" --max-time 8 \
  http://162.55.88.160:9500/vms || echo "  (host unreachable from this network \u2014 operator upstream issue)"

echo ""
echo "== sustained probe: 6 GETs to maritime.sh, watch for variance =="
fail=0
for i in 1 2 3 4 5 6; do
  out=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --max-time 10 https://maritime.sh)
  code=$(echo "$out" | awk '{print $1}')
  t=$(echo "$out" | awk '{print $2}')
  if [ "$code" != "200" ]; then
    fail=$((fail + 1))
    echo "  call $i: code=$code  t=$t  FAIL"
  else
    [ "$VERBOSE" = "verbose" ] && echo "  call $i: code=$code  t=$t"
  fi
done
echo "  failed: $fail / 6"
[ "$fail" -gt 2 ] && {
  echo ""
  echo "BACKEND_LOOKS_UNHEALTHY: more than 2 of 6 calls failed."
  echo "Before launching a deploy loop, wait or escalate."
  exit 2
}
exit 0
