#!/usr/bin/env bash
# HORIZON one-time Let's Encrypt certificate issuance.
#
# Runs ON THE SERVER, after:
#   1. DNS for hantavirus.software (apex + www) resolves to this host
#   2. The stack has been deployed once (so nginx is running on port 80)
#   3. .env.production is in place with LETSENCRYPT_EMAIL set
#
# Strategy:
#   Use certbot's webroot plugin via the running nginx. The nginx config
#   already serves /.well-known/acme-challenge/ from /var/www/certbot, and
#   the certbot service mounts the same path.
#
# After issuance:
#   - Certs live at /etc/letsencrypt/live/hantavirus.software/{fullchain.pem,privkey.pem}
#   - The web service mounts /etc/letsencrypt:ro and picks them up on reload
#   - The certbot sidecar in docker-compose.prod.yml handles auto-renewal

set -euo pipefail

cd /home/ubuntu/horizon

# Load LETSENCRYPT_EMAIL from .env.production
# shellcheck disable=SC1091
LETSENCRYPT_EMAIL=$(grep -E '^LETSENCRYPT_EMAIL=' .env.production | cut -d= -f2-)
if [[ -z "${LETSENCRYPT_EMAIL}" ]]; then
    echo "ERROR: LETSENCRYPT_EMAIL not set in .env.production"
    exit 1
fi

DOMAIN=hantavirus.software
ALIAS_DOMAIN=horizon.79thunit.co.uk

echo "==> Issuing Let's Encrypt certificate for:"
echo "    - ${DOMAIN}"
echo "    - www.${DOMAIN}"
echo "    - ${ALIAS_DOMAIN}  (79th Unit branded alias, 301 -> apex)"
echo "==> Email: ${LETSENCRYPT_EMAIL}"
echo
echo "Pre-flight: all three hostnames must resolve to this server BEFORE running."
echo "Verify:"
echo "  dig +short ${DOMAIN}        # expect hantavirus.software"
echo "  dig +short www.${DOMAIN}    # expect hantavirus.software"
echo "  dig +short ${ALIAS_DOMAIN}  # expect hantavirus.software"
echo

# Run certbot via a one-shot container that shares the webroot + letsencrypt volumes.
# A single multi-SAN cert covers all three hostnames; the certbot sidecar renews it.
docker run --rm \
    -v horizon_letsencrypt:/etc/letsencrypt \
    -v horizon_certbot-webroot:/var/www/certbot \
    certbot/certbot:latest \
    certonly --webroot --webroot-path /var/www/certbot \
    --email "${LETSENCRYPT_EMAIL}" \
    --agree-tos \
    --no-eff-email \
    --domain "${DOMAIN}" \
    --domain "www.${DOMAIN}" \
    --domain "${ALIAS_DOMAIN}" \
    --rsa-key-size 4096 \
    --non-interactive

echo
echo "==> Certificate issued. Reloading nginx..."
docker compose -f docker-compose.prod.yml exec web nginx -s reload

echo
echo "Done. Verify:"
echo "  curl -sI https://${DOMAIN}/ | head -1     # expect HTTP/2 200"
echo "  openssl s_client -connect ${DOMAIN}:443 -servername ${DOMAIN} </dev/null 2>/dev/null \\"
echo "    | openssl x509 -noout -dates -subject -issuer"
