from pathlib import Path
from typing import Dict, Optional
import tqdm
import os
import re
import subprocess
import fire
import requests

ENDPOINT = "https://api.github.com"


def auth_header(token):
    return {"Authorization": f"token {token}"}


def get_upload_url(tag, repo, token) -> str:
    res = requests.get(
        ENDPOINT + f"/repos/{repo}/releases", headers=auth_header(token)
    ).json()
    for d in res:
        try:
            if d["tag_name"] == tag:
                return d["upload_url"]
        except:
            print(res)
            exit(1)
    raise ValueError(f"tag {tag} not found")


def make_upload_url(url: str, file: str):
    url = url.rstrip("{?name,label}")
    file = Path(file).name
    return url + f"?name={file}"


def make_releases_url(repo):
    return ENDPOINT + f"/repos/{repo}/releases"


def make_upload_header(token: str):
    header = auth_header(token)
    header["Content-Type"] = "application/octet-stream"
    return header


def make_download_header(header: Dict) -> Dict:
    header["Accept"] = "application/octet-stream"
    return header


def get_repo() -> str:
    remote_versbose = subprocess.check_output(["git", "remote", "-v"]).decode()
    url = None
    for line in remote_versbose.split("\n"):
        items = line.split()
        if not items:
            continue
        if items[0] == "origin":
            url = items[1]
    assert url
    repo = re.findall(r"github.com[:/](.*?/.*)", url)[0]
    repo = re.sub(".git$", "", repo)
    return repo


def get_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        token = input("Input github token: ")
    return token


def up(file, tag, token: str = "", repo=None):
    token = token or get_token()
    repo = repo or get_repo()
    print(f"repo: {repo}")
    url = get_upload_url(tag, repo, token)
    url = make_upload_url(url, file)
    header = make_upload_header(token)
    print(header)
    print(url)
    with open(file, "rb") as f:
        data = f.read()
    res = requests.post(url, headers=header, data=data)
    print(res.json())


def check_maybe_private_repo(url: str) -> bool:
    r = requests.get(url)
    return r.status_code == 404


def get(name: str, repo: Optional[str] = None, token: Optional[str] = None):
    repo = repo or get_repo()
    url = make_releases_url(repo)
    if not token and check_maybe_private_repo(url):
        token = get_token()
    header = auth_header(token) if token else {}
    r = requests.get(url, headers=header)
    r.raise_for_status()

    target = None
    for release in r.json():
        for asset in release["assets"]:
            if asset["name"] == name:
                target = asset
                break
        if target is not None:
            break

    assert target, f"Asset {name} not found."

    header = make_download_header(header)
    r = requests.get(target["url"], headers=header, stream=True)

    chunk_size = 8192
    with tqdm.tqdm(total=target["size"]) as p:
        with open(name, "wb") as f:
            for c in r.iter_content(chunk_size=chunk_size):
                if c:
                    f.write(c)
                    p.update(len(c))


def main():
    fire.Fire({"up": up, "get": get})


if __name__ == "__main__":
    main()
