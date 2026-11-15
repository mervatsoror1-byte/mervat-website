#!/usr/bin/env python3
"""Upload the WordPress theme, setup plugin and API files to Hostinger, then activate them.

Only files that changed since the last upload are sent (hashes kept in wp/.deploy-state.json).
Needs the Hostinger API token saved for developers.hostinger.com (the network proxy adds it).
Usage: python3 tools/deploy_wp.py [domain]      (default: new.mervatsror.com)
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WP = ROOT / "wp"
API = "https://developers.hostinger.com/api/hosting/v1"
USER = "u627037283"
DOMAIN = sys.argv[1] if len(sys.argv) > 1 else "new.mervatsror.com"
STATE = WP / f".deploy-state-{DOMAIN}.json"
AUTH = ["-H", "Authorization: Bearer proxy-injected"]

# local folder -> path under the website's document root
TARGETS = [(WP / "mervat", "wp-content/themes/mervat"), (WP / "mervat-setup", "wp-content/plugins/mervat-setup"), (WP / "root", "")]


def curl(*args, data=None):
    r = subprocess.run(["curl", "-sS", "-m", "120", *args], capture_output=True, text=data is None)
    return r.stdout


def api(method, path, body=None):
    args = ["-X", method, *AUTH, API + path]
    if body is not None:
        args = ["-X", method, *AUTH, "-H", "Content-Type: application/json", "-d", json.dumps(body), API + path]
    out = subprocess.run(["curl", "-sS", "-m", "120", *args], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"raw": out}


def upload(creds, local, remote):
    size = local.stat().st_size
    url = f"{creds['url'].rstrip('/')}/{remote}?override=true"
    h = ["-H", f"X-Auth: {creds['auth_key']}", "-H", f"X-Auth-Rest: {creds['rest_auth_key']}", "-H", "Tus-Resumable: 1.0.0"]
    r1 = subprocess.run(["curl", "-sS", "-m", "60", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST", url, *h,
                         "-H", f"Upload-Length: {size}", "-H", "Upload-Offset: 0"], capture_output=True, text=True).stdout
    if r1 != "201":
        return f"create {r1}"
    if size == 0:
        return None
    r2 = subprocess.run(["curl", "-sS", "-m", "300", "-D", "-", "-o", "/dev/null", "-X", "PATCH", url, *h,
                         "-H", "Content-Type: application/offset+octet-stream", "-H", "Upload-Offset: 0", "--data-binary", f"@{local}"],
                        capture_output=True, text=True).stdout.lower()
    if f"upload-offset: {size}" not in r2:
        return "patch incomplete"
    return None


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    todo = []
    for base, prefix in TARGETS:
        for f in sorted(base.rglob("*")):
            if not f.is_file():
                continue
            remote = (prefix + "/" if prefix else "") + f.relative_to(base).as_posix()
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            if state.get(remote) != digest:
                todo.append((f, remote, digest))
    print(f"{len(todo)} files to upload to {DOMAIN}")
    if todo:
        creds = api("POST", "/files/upload-urls", {"username": USER, "domain": DOMAIN})
        if "url" not in creds:
            sys.exit(f"no upload url: {creds}")
        failed = []
        for i, (f, remote, digest) in enumerate(todo, 1):
            err = upload(creds, f, remote)
            if err:
                failed.append((remote, err))
            else:
                state[remote] = digest
            if i % 20 == 0:
                print(f"  {i}/{len(todo)}")
        STATE.write_text(json.dumps(state, indent=0, sort_keys=True))
        if failed:
            print("failed:", failed[:10])
            sys.exit(1)
    # Files are already in place; just make sure the theme and plugin are switched on.
    sw = next((i["id"] for i in api("GET", "/wordpress/installations") if i.get("domain") == DOMAIN), None)
    if sw:
        print("theme:", api("POST", f"/accounts/{USER}/wordpress/{sw}/themes/activate", {"theme": "mervat"}))
        print("plugin:", api("POST", f"/accounts/{USER}/wordpress/{sw}/plugins/activate", {"plugin": "mervat-setup"}))
    api("DELETE", f"/accounts/{USER}/websites/{DOMAIN}/cache/clear")
    print("done")


if __name__ == "__main__":
    main()
