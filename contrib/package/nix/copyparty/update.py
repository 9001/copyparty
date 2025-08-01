#!/usr/bin/env python3

# Update the Nix package pin
#
# Usage: ./update.sh [PATH]
# When the [PATH] is not set, it will fetch the latest release from the repo.
# With [PATH] set, it will hash the given file and generate the URL,
# base on the version contained within the file

import base64
import json
import hashlib
import sys
import tarfile
from pathlib import Path

OUTPUT_FILE = Path("pin.json")
TARGET_ASSET = lambda version: f"copyparty-{version}.tar.gz"
HASH_TYPE = "sha256"
LATEST_RELEASE_URL = "https://api.github.com/repos/9001/copyparty/releases/latest"
DOWNLOAD_URL = lambda version: f"https://github.com/9001/copyparty/releases/download/v{version}/{TARGET_ASSET(version)}"


def get_formatted_hash(binary):
    hasher = hashlib.new("sha256")
    hasher.update(binary)
    asset_hash = hasher.digest()
    encoded_hash = base64.b64encode(asset_hash).decode("ascii")
    return f"{HASH_TYPE}-{encoded_hash}"


def version_from_tar_gz(path):
    with tarfile.open(path) as tarball:
        release_name = tarball.getmembers()[0].name
        prefix = "copyparty-"

        if release_name.startswith(prefix):
            return release_name.replace(prefix, "")
    raise ValueError("version not found in provided file")


def remote_release_pin():
    import requests

    response = requests.get(LATEST_RELEASE_URL).json()
    version = response["tag_name"].lstrip("v")
    asset_info = [a for a in response["assets"] if a["name"] == TARGET_ASSET(version)][0]
    download_url = asset_info["browser_download_url"]
    asset = requests.get(download_url)
    formatted_hash = get_formatted_hash(asset.content)

    result = {"url": download_url, "version": version, "hash": formatted_hash}
    return result


def local_release_pin(path):
    version = version_from_tar_gz(path)
    download_url = DOWNLOAD_URL(version)
    formatted_hash = get_formatted_hash(path.read_bytes())

    result = {"url": download_url, "version": version, "hash": formatted_hash}
    return result


def main():
    if len(sys.argv) > 1:
        asset_path = Path(sys.argv[1])
        result = local_release_pin(asset_path)
    else:
        result = remote_release_pin()

    print(result)
    json_result = json.dumps(result, indent=4)
    OUTPUT_FILE.write_text(json_result)


if __name__ == "__main__":
    main()
