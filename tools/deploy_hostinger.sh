#!/usr/bin/env bash
# Build the site, zip it and deploy it to Hostinger (mervatsror.com) through the Hostinger API.
# Needs the Hostinger API token saved as a network secret for developers.hostinger.com (the proxy adds it).
set -euo pipefail
# Since 2026-11-22 mervatsror.com runs WordPress. Deploying the static archive would overwrite it.
if [ "${ALLOW_STATIC_DEPLOY:-}" != "yes-overwrite-wordpress" ]; then
  echo "Refusing: mervatsror.com is now the WordPress site. Use: python3 tools/build_site.py && python3 tools/build_wp_theme.py && python3 tools/deploy_wp.py" >&2
  exit 1
fi
cd "$(dirname "$0")/.."
API=https://developers.hostinger.com/api/hosting/v1; USERN=u627037283; DOMAIN=mervatsror.com
AUTH=(-H "Authorization: Bearer proxy-injected")
python3 tools/build_site.py >/dev/null
mkdir -p dist; rm -f dist/mervat-site-upload.zip
(cd site && zip -qr ../dist/mervat-site-upload.zip . -x "_artifact_index.html")
F=dist/mervat-site-upload.zip; S=$(stat -c%s "$F")
R=$(curl -sS -m 30 -X POST "${AUTH[@]}" -H "Content-Type: application/json" -d "{\"username\":\"$USERN\",\"domain\":\"$DOMAIN\"}" "$API/files/upload-urls")
j(){ echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
U=$(j url); K=$(j auth_key); KR=$(j rest_auth_key); N=mervat-site-upload.zip
H=(-H "X-Auth: $K" -H "X-Auth-Rest: $KR" -H "Tus-Resumable: 1.0.0")
curl -sS -m 60 -o /dev/null -X POST "$U/$N?override=true" "${H[@]}" -H "Upload-Length: $S" -H "Upload-Offset: 0"
OFF=$(curl -sS -m 300 -D - -o /dev/null -X PATCH "$U/$N?override=true" "${H[@]}" -H "Content-Type: application/offset+octet-stream" -H "Upload-Offset: 0" --data-binary "@$F" | grep -i '^upload-offset' | tr -dc 0-9)
[ "$OFF" = "$S" ] || { echo "upload incomplete ($OFF/$S)"; exit 1; }
curl -sS -m 120 -X POST "${AUTH[@]}" -H "Content-Type: application/json" -d "{\"archive_path\":\"$N\"}" "$API/accounts/$USERN/websites/$DOMAIN/deploy"; echo
sleep 15
curl -sS -m 30 -X DELETE "${AUTH[@]}" "$API/accounts/$USERN/websites/$DOMAIN/cache/clear" >/dev/null || true
echo "deployed $S bytes to $DOMAIN"
