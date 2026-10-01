"""
Automated GitHub Release Publisher for AutoCapCut Studio.
Reads GitHub OAuth token from Git Credential Manager or GITHUB_TOKEN env var,
creates or updates the GitHub Release, and uploads the distribution zip file.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_OWNER = "vutrunquan"
REPO_NAME = "autocapcut"
BASE_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = BASE_DIR / "releases" / "AutoCapCut_Studio_Windows.zip"
VERSION_FILE = BASE_DIR / "version.json"


def get_github_token() -> str:
    """Retrieve GitHub token from environment variable or Git Credential Manager."""
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        return env_token.strip()

    try:
        p = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, _ = p.communicate("protocol=https\nhost=github.com\n")
        creds = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        token = creds.get("password")
        if token:
            return token.strip()
    except Exception as e:
        print(f"Warning: Could not retrieve token from Git Credential Manager: {e}")

    return ""


def main():
    print("\n" + "=" * 65)
    print("    AUTOCAPCUT STUDIO - TỰ ĐỘNG PHÁT HÀNH BẢN CẬP NHẬT GITHUB")
    print("=" * 65 + "\n")

    if not VERSION_FILE.exists():
        print(f"[X] Không tìm thấy file {VERSION_FILE}")
        sys.exit(1)

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        v_data = json.load(f)

    version = v_data.get("version", "1.0.1")
    tag_name = f"v{version}"
    title = v_data.get("title", f"AutoCapCut Studio {tag_name}")
    changelog = v_data.get("changelog", [])
    body_text = f"## {title}\n\n" + "\n".join(f"- {c}" for c in changelog)

    token = get_github_token()
    if not token:
        print("[X] Không tìm thấy GitHub token!")
        print("Vui lòng thiết lập biến môi trường GITHUB_TOKEN hoặc đăng nhập git với GitHub.")
        sys.exit(1)

    print(f"1. Xác thực GitHub Token... OK ({REPO_OWNER}/{REPO_NAME})")
    print(f"2. Phiên bản phát hành: {tag_name}")

    if not ZIP_PATH.exists():
        print(f"[X] File zip chưa được đóng gói: {ZIP_PATH}")
        print("Vui lòng chạy 'python tools/build_dist.py' trước!")
        sys.exit(1)

    zip_size_mb = os.path.getsize(ZIP_PATH) / (1024 * 1024)
    print(f"3. File đóng gói: {ZIP_PATH.name} ({zip_size_mb:.1f} MB)")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AutoCapCut-Publisher"
    }

    # Step A: Check if release exists or create it
    rel_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    release_info = None

    try:
        tag_check_url = f"{rel_api_url}/tags/{tag_name}"
        req = urllib.request.Request(tag_check_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            release_info = json.loads(resp.read().decode("utf-8"))
            print(f"4. Bản phát hành {tag_name} đã tồn tại trên GitHub (ID: {release_info['id']}).")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"4. Đang tạo Release mới cho {tag_name} trên GitHub...")
            payload = json.dumps({
                "tag_name": tag_name,
                "name": title,
                "body": body_text,
                "draft": False,
                "prerelease": False
            }).encode("utf-8")
            req = urllib.request.Request(rel_api_url, data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    release_info = json.loads(resp.read().decode("utf-8"))
                    print(f"   Tạo Release thành công (ID: {release_info['id']})!")
            except Exception as create_err:
                print(f"[X] Lỗi tạo release: {create_err}")
                sys.exit(1)
        else:
            print(f"[X] Lỗi kiểm tra release: {e}")
            sys.exit(1)

    release_id = release_info["id"]

    # Step B: Check existing assets and remove old zip if already present
    for asset in release_info.get("assets", []):
        if asset.get("name") == ZIP_PATH.name:
            asset_id = asset["id"]
            print(f"5. Đang xoá file cũ trên Release (Asset ID: {asset_id})...")
            del_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/assets/{asset_id}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(del_req):
                    print("   Xoá file cũ thành công.")
            except Exception as del_err:
                print(f"   Cảnh báo: Không thể xoá asset cũ: {del_err}")

    # Step C: Upload ZIP asset
    upload_url = f"https://uploads.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/{release_id}/assets?name={ZIP_PATH.name}"
    print(f"6. Đang tải lên {ZIP_PATH.name} ({zip_size_mb:.1f} MB) lên GitHub Releases...")
    print("   Vui lòng đợi vài giây trong khi tải file lên...")

    upload_headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/zip",
        "Content-Length": str(os.path.getsize(ZIP_PATH)),
        "User-Agent": "AutoCapCut-Publisher"
    }

    with open(ZIP_PATH, "rb") as f_zip:
        upload_req = urllib.request.Request(upload_url, data=f_zip, headers=upload_headers, method="POST")
        try:
            with urllib.request.urlopen(upload_req) as resp:
                asset_res = json.loads(resp.read().decode("utf-8"))
                download_url = asset_res.get("browser_download_url")
                print("\n" + "=" * 65)
                print("🎉 TẢI LÊN GITHUB RELEASES THÀNH CÔNG!")
                print(f"👉 Direct Download URL:\n   {download_url}")
                print(f"👉 Release Page:\n   {release_info.get('html_url')}")
                print("=" * 65 + "\n")
        except urllib.error.HTTPError as up_err:
            err_body = up_err.read().decode("utf-8", errors="ignore")
            print(f"[X] Lỗi upload asset: {up_err} - {err_body}")
            sys.exit(1)


if __name__ == "__main__":
    main()
