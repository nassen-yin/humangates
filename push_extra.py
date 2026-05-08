#!/usr/bin/env python3
"""Push remaining files: .gitignore and .env.example"""
import os, json, base64, urllib.request

TOKEN = open("/tmp/gh_push_token").read().strip()
api_base = "https://api.github.com"
owner = "nassen-yin"
repo = "humangates"
headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
repo_dir = os.path.expanduser("~/human-gates")

for rel_path in [".gitignore", ".env.example"]:
    fpath = os.path.join(repo_dir, rel_path)
    if not os.path.exists(fpath):
        print(f"  Not found: {rel_path}")
        continue
    with open(fpath, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    data = json.dumps({
        "message": "Add .gitignore and .env.example",
        "content": content_b64,
        "branch": "main",
    }).encode()
    try:
        req = urllib.request.Request(
            f"{api_base}/repos/{owner}/{repo}/contents/{rel_path}",
            data=data,
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        resp = urllib.request.urlopen(req)
        print(f"  OK: {rel_path}")
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  FAIL {rel_path}: {e.code} {err[:100]}")

print("\nDone: https://github.com/nassen-yin/humangates")
