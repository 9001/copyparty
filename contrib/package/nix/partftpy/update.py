#!/usr/bin/env python3

# Update the Nix package pin
#
# Usage: ./update.sh

import base64
import json
import hashlib
import sys
from pathlib import Path

OUTPUT_FILE = Path("pin.json")
TARGET_ASSET = lambda version: f"partftpy-{version}.tar.gz"
HASH_TYPE = "sha256"
LATEST_RELEASE_URL = "https://api.github.com/repos/9001/partftpy/releases/latest"


def get_formatted_hash(binary):
    hasher = hashlib.new("sha256")
    hasher.update(binary)
    asset_hash = hasher.digest()
    encoded_hash = base64.b64encode(asset_hash).decode("ascii")
    return f"{HASH_TYPE}-{encoded_hash}"


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


def main():
    result = remote_release_pin()

    print(result)
    json_result = json.dumps(result, indent=4)
    OUTPUT_FILE.write_text(json_result)


if __name__ == "__main__":
    main()
