# Handoff: upload the prototype to Hostinger

Goal: put the current static prototype online on the client's own domain fast, so Paymob can review a live site before linking the payment gateway. This is temporary; the WordPress build will replace it later on the same hosting and domain.

## What to upload
- Ready archive: `dist/mervat-site-upload.zip` (built from `site/`, excludes `_artifact_index.html`).
- To rebuild after changes: `python3 tools/build_site.py`, then zip the contents of `site/` (not the folder itself) without `_artifact_index.html`.
- Static files only, no build step: `index.html` sits at the archive root.

## Target
- Domain: `drmervatsoror.com` (planned free domain with the hosting plan). Check in the Hostinger account which domain/hosting actually exists before deploying. If only `mervatsror.com` (owned, auto-renew on) is attached to hosting, ask the user which domain to use.
- Use the Hostinger connector's static-site deploy tool (e.g. `hosting_deployStaticWebsite`) with the domain and the archive path. It overwrites the site's current files: confirm with the user first if the domain already shows a site.

## After upload
1. Make sure SSL is active (https padlock).
2. Open the live URL and check: home, a product page, checkout, privacy/refund/terms, contact.
3. Paymob also wants an official email on the contact page. Once the user creates one on Hostinger (e.g. info@<domain>), add it to the contact page and footer, rebuild, and redeploy.

## Rules
- Do not buy anything or change billing in the user's Hostinger account; purchases are the user's decision.
- Never ask for passwords, card data or verification codes.
- Talk to the user in Arabic (Egyptian is fine), short and simple.
