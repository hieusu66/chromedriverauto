import os
import sys
import subprocess

# 👇 Tự cài thư viện nếu chưa có
def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Đang cài đặt {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for pkg in ["requests", "bs4"]:
    install_if_missing(pkg)

# 👇 Phần chính sau khi cài xong thư viện
import platform
import re
import requests
from bs4 import BeautifulSoup
import zipfile

def get_chrome_version():
    system = platform.system()
    try:
        if system == "Windows":
            output = subprocess.check_output(
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                shell=True, text=True
            )
            version = re.search(r"(\d+\.\d+\.\d+\.\d+)", output).group(1)
        elif system == "Darwin":
            output = subprocess.check_output(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                text=True
            )
            version = re.search(r"(\d+\.\d+\.\d+\.\d+)", output).group(1)
        elif system == "Linux":
            output = subprocess.check_output(["google-chrome", "--version"], text=True)
            version = re.search(r"(\d+\.\d+\.\d+\.\d+)", output).group(1)
        else:
            return None
        return version
    except Exception as e:
        print("❌ Không thể lấy phiên bản Chrome:", e)
        return None

def find_latest_matching_driver(major_version_prefix):
    base_url = "https://mirrors.huaweicloud.com/chromedriver/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    versions = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.startswith(major_version_prefix):
            clean_version = href.strip("/")
            versions.append(clean_version)

    if versions:
        versions.sort(key=lambda s: list(map(int, s.split('.'))))
        return versions[-1]
    else:
        return None

def download_and_extract_chromedriver(version):
    base_url = f"https://mirrors.huaweicloud.com/chromedriver/{version}/"
    system = platform.system()

    if system == "Windows":
        zip_name = "chromedriver-win64.zip"
        folder_name = "chromedriver-win64"
        driver_filename = "chromedriver.exe"
    elif system == "Linux":
        zip_name = "chromedriver-linux64.zip"
        folder_name = "chromedriver-linux64"
        driver_filename = "chromedriver"
    elif system == "Darwin":
        zip_name = "chromedriver-mac-x64.zip"
        folder_name = "chromedriver-mac-x64"
        driver_filename = "chromedriver"
    else:
        print("❌ Hệ điều hành không hỗ trợ.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(script_dir, zip_name)
    extract_folder = os.path.join(script_dir, folder_name)
    driver_output_path = os.path.join(script_dir, driver_filename)

    # 📥 Tải zip
    download_url = base_url + zip_name
    print(f"⬇️ Đang tải: {download_url}")
    r = requests.get(download_url)
    if r.status_code == 200:
        with open(zip_path, "wb") as f:
            f.write(r.content)
        print(f"✅ Đã tải: {zip_path}")
    else:
        print("❌ Lỗi khi tải:", r.status_code)
        return

    # 📦 Giải nén zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(script_dir)

    extracted_path = os.path.join(extract_folder, driver_filename)
    if os.path.exists(extracted_path):
        os.replace(extracted_path, driver_output_path)
        print(f"🗂️ Đã giải nén {driver_filename} tới: {driver_output_path}")
    else:
        print("❌ Không tìm thấy file đã giải nén:", extracted_path)
        return

    # 🧹 Dọn dẹp
    os.remove(zip_path)
    if os.path.exists(extract_folder):
        import shutil
        shutil.rmtree(extract_folder)
        print(f"🧹 Đã xoá thư mục: {extract_folder}")

    # 🔧 Set quyền nếu không phải Windows
    if system != "Windows":
        os.chmod(driver_output_path, 0o755)
        print("🔧 Set quyền thực thi.")

# ----------------------------
# THỰC THI
chrome_ver = get_chrome_version()
print("🔍 Chrome version:", chrome_ver)

if chrome_ver:
    major_prefix = chrome_ver.split(".")[0] + "."
    matched_driver = find_latest_matching_driver(major_prefix)
    if matched_driver:
        print("✅ Bản chromedriver phù hợp:", matched_driver)
        download_and_extract_chromedriver(matched_driver)
    else:
        print("❌ Không tìm thấy bản phù hợp.")
else:
    print("❌ Không xác định được phiên bản Chrome.")
