#!/usr/bin/env bash
# Share your locally-running ToDate demo with teammates via a public HTTPS URL —
# no cloud account needed. The app keeps running on THIS machine; the tunnel is
# just a public door to it (same idea as Claude Code Remote Control).
#
# Usage:
#   1) In one terminal, start the server in demo mode:
#        cd backend
#        DEMO_MODE=true ENVIRONMENT=development \
#          uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
#   2) In another terminal:
#        bash scripts/share-demo.sh 8000
#   3) Share the https URL it prints. Teammates open it on any phone/browser.
set -e
PORT="${1:-8000}"

if command -v cloudflared >/dev/null 2>&1; then
  echo "→ Starting Cloudflare quick tunnel to http://localhost:$PORT"
  echo "  (public https URL appears below; Ctrl-C to stop sharing)"
  # --protocol http2 on purpose: the default (QUIC/UDP) gets degraded on many
  # networks, producing a tunnel that registers a hostname but never fully binds
  # to Cloudflare's edge — the URL then resolves but silently routes nowhere
  # (symptom: `cloudflared_tunnel_ha_connections 1` and 0 total_requests).
  # HTTP/2 runs over TCP and is far more reliable here.
  exec cloudflared tunnel --url "http://localhost:$PORT" --protocol http2
fi

echo "cloudflared not installed. Options:"
echo "  • brew install cloudflared    then re-run this script"
echo "  • npx localtunnel --port $PORT"
echo "  • ngrok http $PORT            (needs a free ngrok account)"
exit 1
