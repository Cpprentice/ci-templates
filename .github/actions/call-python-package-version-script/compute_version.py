import subprocess
import sys
import re
from datetime import datetime, timezone
import tomllib
from packaging.version import Version


def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def normalize(tag):
    return tag[1:] if tag and tag.startswith("v") else tag


def main():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    v_py = data["project"]["version"]

    try:
        tags_on_head = run(["git", "tag", "--points-at", "HEAD"]).splitlines()
    except subprocess.CalledProcessError:
        tags_on_head = []

    try:
        latest_tag = run(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        latest_tag = None

    if latest_tag and not re.match(r"^v\d+\.\d+\.\d+((a|b|rc)\d+)?$", latest_tag):
        print(f"ERROR: Invalid tag format: {latest_tag}")
        sys.exit(1)

    v_tag = normalize(latest_tag)

    expected_tag = f"v{v_py}"

    if expected_tag in tags_on_head:
        version = v_py
    else:
        if v_tag is None:
            is_dev = True
        else:
            v_py = Version(v_py)
            v_tag = Version(v_tag)

            if v_py > v_tag:
                is_dev = True
            elif v_py == v_tag:
                print(f"ERROR: Version {v_py} already tagged but not on this commit.")
                sys.exit(1)
            else:
                print(f"ERROR: Version {v_py} < latest tag {v_tag}.")
                sys.exit(1)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        version = f"{v_py}.dev{ts}"

    print(version)

    # --- Export to GitHub ---
    with open(sys.argv[1], "a") as f:
        f.write(f"version={version}\n")


if __name__ == '__main__':
    main()
