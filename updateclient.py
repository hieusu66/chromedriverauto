import os
import requests

# URL đến file text.txt trên server
TEXT_FILE_URL = "https://bloghieu.id.vn/chromedriverauto/ver.txt"

# Tên file lưu version hiện tại trên máy
LOCAL_VERSION_FILE = "version.txt"

def get_remote_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip().splitlines()
    except Exception as e:
        print(f"[Lỗi] Không thể tải file text.txt: {e}")
        return []

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    return "ver--0.0"

def save_local_version(version):
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(version)

def download_file(url, save_dir):
    local_filename = os.path.join(save_dir, url.split("/")[-1])
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"[✓] Tải thành công: {local_filename}")
    except Exception as e:
        print(f"[Lỗi] Không thể tải {url}: {e}")

def main():
    lines = get_remote_text(TEXT_FILE_URL)
    if not lines or not lines[0].startswith("ver--"):
        print("[Lỗi] Không tìm thấy thông tin phiên bản hợp lệ trong text.txt")
        return

    remote_version = lines[0]
    file_links = lines[1:]

    local_version = get_local_version()

    print(f"Phiên bản hiện tại: {local_version}")
    print(f"Phiên bản trên server: {remote_version}")

    if remote_version != local_version:
        print("[!] Phát hiện phiên bản mới, bắt đầu tải các file...")
        for url in file_links:
            download_file(url, os.getcwd())
        save_local_version(remote_version)
        print("[✓] Cập nhật hoàn tất.")
    else:
        print("[✓] Đã là phiên bản mới nhất, không cần tải lại.")

if __name__ == "__main__":
    main()
