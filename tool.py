import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time, json, threading, logging, sched, os, shutil, pyperclip, pickle
from datetime import datetime
from sympy import sympify

# Cài đặt thư viện
required_libraries = ["selenium", "pyperclip", "sympy", "undetected-chromedriver"]
def install_libraries():
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"Đang cài đặt thư viện {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
install_libraries()

import undetected_chromedriver as uc
# Cấu hình logging
logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Thêm encoding utf-8
)

# Đường dẫn và biến toàn cục
CHROMEDRIVER_PATH = "chromedriver.exe"
PROFILES_DIR = os.path.join(os.path.dirname(__file__), "profiles")
script_steps = []
accounts = []

# Tệp cấu hình
SETTINGS_FILE = "settings.txt"
def load_settings():
    settings = {"threads": "1", "width": "1200", "height": "800", "auto_create_profiles": "True", "delete_profiles_after_run": "False"}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        settings[k] = v
        except Exception as e:
            logging.error(f"Lỗi khi tải settings: {e}")
    return settings

def save_settings(threads, width, height, auto_create_profiles, delete_profiles_after_run):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(f"threads={threads}\n")
            f.write(f"width={width}\n")
            f.write(f"height={height}\n")
            f.write(f"auto_create_profiles={auto_create_profiles}\n")
            f.write(f"delete_profiles_after_run={delete_profiles_after_run}\n")
    except Exception as e:
        logging.error(f"Lỗi khi lưu settings: {e}")

def create_profile_dir(profile_id):
    try:
        if not os.path.exists(PROFILES_DIR):
            os.makedirs(PROFILES_DIR)
            logging.info(f"Tạo thư mục profiles: {PROFILES_DIR}")
        profile_path = os.path.join(PROFILES_DIR, f"chrome_profile_{profile_id}")
        if os.path.exists(profile_path):
            logging.info(f"Tái sử dụng profile hiện có: {profile_path}")
        else:
            os.makedirs(profile_path)
            logging.info(f"Tạo profile mới: {profile_path}")
        return profile_path
    except Exception as e:
        logging.error(f"Lỗi khi tạo profile {profile_id}: {e}")
        raise

def clear_profiles():
    try:
        if os.path.exists(PROFILES_DIR):
            shutil.rmtree(PROFILES_DIR)
            logging.info("Đã xóa tất cả thư mục profile")
            messagebox.showinfo("Thành công", "Đã xóa tất cả profile Chrome")
        else:
            messagebox.showinfo("Thông báo", "Không có profile nào để xóa")
    except Exception as e:
        logging.error(f"Lỗi khi xóa profiles: {e}")
        messagebox.showerror("Lỗi", f"Không thể xóa profiles: {e}")

def list_profiles():
    try:
        if not os.path.exists(PROFILES_DIR):
            return []
        profiles = [f for f in os.listdir(PROFILES_DIR) if f.startswith("chrome_profile_")]
        return profiles
    except Exception as e:
        logging.error(f"Lỗi khi liệt kê profiles: {e}")
        return []

def show_profiles():
    profiles = list_profiles()
    if not profiles:
        messagebox.showinfo("Danh sách profile", "Chưa có profile nào trong thư mục 'profiles'.")
        return
    win = tk.Toplevel(root)
    win.title("Danh sách Chrome Profiles")
    win.geometry("300x200")
    tk.Label(win, text="Các profile hiện có:", font=("Arial", 10, "bold")).pack(pady=5)
    profile_listbox = tk.Listbox(win, width=30, height=10)
    profile_listbox.pack(pady=5)
    for profile in profiles:
        profile_listbox.insert(tk.END, profile)
    tk.Button(win, text="Đóng", command=win.destroy).pack(pady=5)

def save_cookies(driver, profile_path):
    try:
        cookies_file = os.path.join(profile_path, "cookies.pkl")
        cookies = driver.get_cookies()
        with open(cookies_file, "wb") as f:
            pickle.dump(cookies, f)
        logging.info(f"Đã lưu {len(cookies)} cookies vào: {cookies_file}")
    except Exception as e:
        logging.error(f"Lỗi khi lưu cookies vào {cookies_file}: {e}")

def load_cookies(driver, profile_path):
    try:
        cookies_file = os.path.join(profile_path, "cookies.pkl")
        if os.path.exists(cookies_file):
            driver.get('https://accounts.google.com')
            with open(cookies_file, "rb") as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        logging.error(f"Lỗi khi thêm cookie: {e}")
                logging.info(f"Đã tải {len(cookies)} cookies từ: {cookies_file}")
                return True
        else:
            logging.warning(f"Không tìm thấy file cookies: {cookies_file}")
            return False
    except Exception as e:
        logging.error(f"Lỗi khi tải cookies từ {cookies_file}: {e}")
        return False

def show_guide():
    guide_text = (
        "HƯỚNG DẪN SỬ DỤNG\n\n"
        "1. Nhập tay các bước đăng nhập Google:\n"
        "- Bước 1: Chọn 'Mở URL', nhập 'https://accounts.google.com'.\n"
        "- Bước 2: Chọn 'Gửi ký tự (XPath|Text)', nhập '//*[@id=\"identifierId\"]|your_email@gmail.com'.\n"
        "- Bước 3: Chọn 'Click XPath', nhập '//*[@id=\"identifierNext\"]/div/button'.\n"
        "- Bước 4: Chọn 'Ngủ', nhập '2' (giây).\n"
        "- Bước 5: Chọn 'Gửi ký tự (XPath|Text)', nhập '//input[@name=\"Passwd\"]|your_password'.\n"
        "- Bước 6: Chọn 'Click XPath', nhập '//*[@id=\"passwordNext\"]/div/button'.\n"
        "- Bước 7: Chọn 'Ngủ', nhập '5' (giây).\n"
        "- Bước 8: Chọn 'Tùy chỉnh', nhập mã: save_cookies(driver, '{profile_path}')\n"
        "- Bước 9 (lần chạy sau): Chọn 'Tùy chỉnh', nhập mã: load_cookies(driver, '{profile_path}')\ndriver.get('https://accounts.google.com')\n\n"
        "2. Các hành động khác:\n"
        "- Mở URL: Nhập đường dẫn website.\n"
        "- Ngủ: Nhập số giây cần chờ.\n"
        "- Click XPath: Nhập XPath của nút cần click.\n"
        "- Gửi ký tự (XPath|Text): Nhập XPath và nội dung (ví dụ: email, mật khẩu).\n"
        "- Swipe (Hướng|Pixel đầu|Pixel cuối): Nhập hướng (lên/xuống/trái/phải), số pixel đầu và cuối.\n"
        "- Click Full XPath: Nhập XPath, dùng JavaScript để click.\n"
        "- Tùy chỉnh: Viết mã Python tùy chỉnh.\n"
        "- Tìm và Nhập (Text|Value): Tìm phần tử chứa văn bản và nhập giá trị.\n"
        "- Tìm và Nhập vào Phần Tử Gần Kề (Text|Value|Position|ElementType): Tìm phần tử chứa văn bản và nhập giá trị vào phần tử gần kề.\n\n"
        "3. Quản lý Chrome Profiles:\n"
        "- Bật 'Tạo profile tự động' để tạo thư mục profile.\n"
        "- Tắt 'Xóa profile sau khi chạy' để giữ cookies.\n"
        "- Nhấn 'Xem Profiles' để kiểm tra danh sách profile.\n"
        "- Nhấn 'Xóa Tất Cả Profiles' để xóa toàn bộ profile.\n\n"
        "4. Khắc phục lỗi:\n"
        "- Kiểm tra log.txt để xem chi tiết lỗi.\n"
        "- Nếu Google yêu cầu CAPTCHA, tắt 'Ẩn Chrome (headless)' và đăng nhập thủ công.\n"
        "- Đảm bảo chromedriver.exe tương thích với Chrome.\n"
        "- Kiểm tra quyền ghi/đọc thư mục profiles.\n"
    )
    messagebox.showinfo("Hướng dẫn sử dụng", guide_text)

def run_script_instance(account=None, headless=False, profile_path=None):
    try:
        options = Options()
        if headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if profile_path:
            options.add_argument(f"--user-data-dir={profile_path}")
        service = Service(CHROMEDRIVER_PATH)
        service.creationflags = subprocess.CREATE_NO_WINDOW
        driver = uc.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            w = int(chrome_width.get())
            h = int(chrome_height.get())
            driver.set_window_size(w, h)
        except Exception as e:
            logging.error(f"Lỗi khi đặt kích thước cửa sổ: {e}")

        for action, value in script_steps:
            try:
                if action == "Mở URL":
                    driver.get(value)
                    logging.info(f"Đã mở URL: {value}")
                elif action == "Ngủ":
                    time.sleep(float(value))
                    logging.info(f"Ngủ {value} giây")
                elif action == "Click XPath":
                    element = driver.find_element(By.XPATH, value)
                    element.click()
                    logging.info(f"Đã click XPath: {value}")
                elif action in ["Gửi ký tự (XPath|Text)", "Send Keys (XPath|Text)"]:
                    xpath, text = value.split("|", 1)
                    if account:
                        for k, v in account.items():
                            text = text.replace(f"{{{k}}}", str(v or ""))
                    driver.find_element(By.XPATH, xpath).send_keys(text)
                    logging.info(f"Đã gửi ký tự '{text}' vào XPath: {xpath}")
                elif action == "Swipe (Hướng|Pixel đầu|Pixel cuối)":
                    direction, start_pixel, end_pixel = value.split("|")
                    start_pixel = int(start_pixel)
                    end_pixel = int(end_pixel)
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    if direction.lower() == "lên":
                        start_x, start_y = 400, start_pixel
                        end_x, end_y = 400, end_pixel
                    elif direction.lower() == "xuống":
                        start_x, start_y = 400, start_pixel
                        end_x, end_y = 400, end_pixel
                    elif direction.lower() == "trái":
                        start_x, start_y = start_pixel, 400
                        end_x, end_y = end_pixel, 400
                    elif direction.lower() == "phải":
                        start_x, start_y = start_pixel, 400
                        end_x, end_y = end_pixel, 400
                    else:
                        raise Exception("Hướng swipe không hợp lệ")
                    actions.move_by_offset(start_x, start_y)
                    actions.click_and_hold()
                    actions.move_by_offset(end_x - start_x, end_y - start_y)
                    actions.release()
                    actions.perform()
                    logging.info(f"Đã thực hiện swipe {direction}: {start_pixel} -> {end_pixel}")
                elif action == "Click Full XPath":
                    element = driver.find_element(By.XPATH, value)
                    driver.execute_script("arguments[0].click();", element)
                    logging.info(f"Đã click Full XPath: {value}")
                elif action == "Tùy chỉnh":
                    value = value.replace("{profile_path}", profile_path if profile_path else "")
                    if account:
                        for k, v in account.items():
                            value = value.replace(f"{{{k}}}", str(v or ""))
                    local_vars = {"driver": driver, "account": account, "By": By, "sympify": sympify, "logging": logging, "save_cookies": save_cookies, "load_cookies": load_cookies, "time": time}
                    exec(value, {}, local_vars)
                    logging.info(f"Đã thực thi mã tùy chỉnh: {value[:50]}...")
                elif action == "Tìm và Nhập (Text|Value)":
                    search_text, input_value = value.split("|", 1)
                    if account:
                        for k, v in account.items():
                            input_value = input_value.replace(f"{{{k}}}", str(v or ""))
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{search_text}')]")
                    if not elements:
                        logging.error(f"Không tìm thấy phần tử chứa văn bản: {search_text}")
                        continue
                    for element in elements:
                        try:
                            if element.is_enabled() and element.is_displayed():
                                element.clear()
                                element.send_keys(input_value)
                                logging.info(f"Đã nhập '{input_value}' vào phần tử chứa '{search_text}'")
                                break
                        except Exception as e:
                            logging.error(f"Không thể nhập vào phần tử: {e}")
                            continue
                    else:
                        logging.error(f"Không có phần tử nào phù hợp để nhập: {search_text}")
                elif action == "Tìm và Nhập vào Phần Tử Gần Kề (Text|Value|Position|ElementType)":
                    search_text, input_value, position, element_type = value.split("|", 3)
                    if account:
                        for k, v in account.items():
                            input_value = input_value.replace(f"{{{k}}}", str(v or ""))
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{search_text}')]")
                    if not elements:
                        logging.error(f"Không tìm thấy phần tử chứa văn bản: {search_text}")
                        continue
                    for element in elements:
                        try:
                            if element_type.lower() == "input":
                                xpath = f"preceding::input[1]" if position.lower() == "before" else f"following::input[1]"
                            elif element_type.lower() == "textarea":
                                xpath = f"preceding::textarea[1]" if position.lower() == "before" else f"following::textarea[1]"
                            elif element_type.lower() == "contenteditable":
                                xpath = f"preceding::*[@contenteditable='true'][1]" if position.lower() == "before" else f"following::*[@contenteditable='true'][1]"
                            else:
                                logging.error(f"Loại phần tử không hợp lệ: {element_type}")
                                continue
                            target_element = element.find_element(By.XPATH, xpath)
                            if target_element.is_enabled() and target_element.is_displayed():
                                if element_type.lower() in ["input", "textarea"]:
                                    target_element.clear()
                                    target_element.send_keys(input_value)
                                elif element_type.lower() == "contenteditable":
                                    driver.execute_script("arguments[0].innerText = arguments[1];", target_element, input_value)
                                logging.info(f"Đã nhập '{input_value}' vào {element_type} {position} phần tử chứa '{search_text}'")
                                break
                        except Exception as e:
                            logging.error(f"Không tìm thấy hoặc không thể nhập vào {element_type} {position}: {e}")
                            continue
                    else:
                        logging.error(f"Không tìm thấy {element_type} {position} phù hợp cho: {search_text}")
            except Exception as e:
                logging.error(f"Lỗi khi thực thi hành động '{action}' với giá trị '{value}': {e}")
        logging.info("Hoàn thành 1 phiên chạy")
        if auto_quit_var.get():
            driver.quit()
    except Exception as e:
        logging.error(f"Lỗi khi chạy script instance: {e}")

def run_multithread():
    try:
        n = int(threads_entry.get())
        head = headless_var.get()
        if not script_steps:
            messagebox.showwarning("Cảnh báo", "Vui lòng thêm bước trước khi chạy.")
            return
        progress_var.set(0)
        progressbar['maximum'] = n
        progress_label.config(text="Đang chạy...")
        threads = []
        tot = n

        profile_paths = []
        if auto_create_profiles_var.get():
            for i in range(n):
                profile_path = create_profile_dir(i + 1)
                profile_paths.append(profile_path)
        else:
            profile_paths = [None] * n

        def wrapper(acc, hd, profile_path):
            try:
                run_script_instance(acc, hd, profile_path)
                progress_var.set(progress_var.get() + 1)
                progressbar.update()
                progress_label.config(text=f"Đã xong {progress_var.get()}/{tot}")
                if delete_profiles_after_run_var.get() and profile_path:
                    try:
                        shutil.rmtree(profile_path)
                        logging.info(f"Đã xóa profile: {profile_path}")
                    except Exception as e:
                        logging.error(f"Lỗi khi xóa profile {profile_path}: {e}")
            except Exception as e:
                logging.error(f"Lỗi trong luồng {profile_path}: {e}")
                progress_var.set(progress_var.get() + 1)
                progressbar.update()
                progress_label.config(text=f"Đã xong {progress_var.get()}/{tot}")

        for i in range(n):
            acc = accounts[i % len(accounts)] if accounts else None
            profile_path = profile_paths[i % len(profile_paths)] if profile_paths else None
            t = threading.Thread(target=wrapper, args=(acc, head, profile_path), daemon=True)
            t.start()
            threads.append(t)

        def chk():
            if all(not t.is_alive() for t in threads):
                progress_label.config(text="Hoàn tất tất cả")
                messagebox.showinfo("Xong", "Tất cả script đã chạy xong.")
            else:
                root.after(500, chk)
        root.after(500, chk)
    except Exception as e:
        logging.error(f"Lỗi khi chạy multithread: {e}")
        messagebox.showerror("Lỗi", str(e))

def add_step():
    action = action_combo.get()
    value = value_entry.get().strip()
    if action == "Tùy chỉnh":
        open_custom_code_popup()
        return
    if not action:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn thao tác.")
        return
    script_steps.append((action, value))
    script_listbox.insert(tk.END, f"{action} | {value}")
    value_entry.delete(0, tk.END)

def refresh_script_list():
    try:
        if not os.path.exists("script"):
            os.makedirs("script")
        files = [f for f in os.listdir("script") if f.endswith((".json", ".txt"))]
        script_option_listbox.delete(0, tk.END)
        for f in files:
            script_option_listbox.insert(tk.END, f)
    except Exception as e:
        logging.error(f"Lỗi khi tải danh sách script: {e}")

def on_script_option_select(event=None):
    try:
        sel = script_option_listbox.curselection()
        if not sel:
            return
        fname = script_option_listbox.get(sel[0])
        fp = os.path.join("script", fname)
        global script_steps
        script_steps = []
        if fname.endswith(".json"):
            with open(fp, "r", encoding="utf-8") as f:
                script_steps = json.load(f)
        elif fname.endswith(".txt"):
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("|", 1)
                    script_steps.append((parts[0], parts[1] if len(parts) > 1 else ""))
        script_listbox.delete(0, tk.END)
        for a, v in script_steps:
            script_listbox.insert(tk.END, f"{a} | {v}")
        messagebox.showinfo("Đã tải", f"Đã tải script: {fname}")
    except Exception as e:
        logging.error(f"Lỗi khi tải script {fname}: {e}")
        messagebox.showerror("Lỗi", f"Không thể tải script: {e}")

def save_script():
    try:
        if not os.path.exists("script"):
            os.makedirs("script")
        win = tk.Toplevel(root)
        win.title("Lưu script")
        win.geometry("350x250")
        tk.Label(win, text="Tên script (để trống = timestamp):").pack(pady=5)
        ne = tk.Entry(win, width=30)
        ne.pack(pady=5)
        tk.Label(win, text="Hoặc dán nội dung TXT (Action|Value mỗi dòng):").pack(pady=5)
        txt = tk.Text(win, height=5, width=30)
        txt.pack(pady=5)
        def on_save():
            try:
                name = ne.get().strip() or datetime.now().strftime("%H_%M_%S-%d-%m-%Y")
                fp = os.path.join("script", name + ".json")
                steps = script_steps.copy()
                txt_content = txt.get("1.0", tk.END).strip()
                if txt_content:
                    steps = []
                    for line in txt_content.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split("|", 1)
                        steps.append([parts[0], parts[1] if len(parts) > 1 else ""])
                else:
                    steps = [[a, v] for a, v in steps]
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(steps, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Đã lưu", f"Đã lưu script vào: {fp}")
                win.destroy()
                refresh_script_list()
            except Exception as e:
                logging.error(f"Lỗi khi lưu script: {e}")
                messagebox.showerror("Lỗi", f"Không thể lưu script: {e}")
        tk.Button(win, text="Lưu", command=on_save).pack(pady=10)
    except Exception as e:
        logging.error(f"Lỗi khi mở cửa sổ lưu script: {e}")

def load_accounts_from_text():
    try:
        fp = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not fp:
            return
        global accounts
        accounts = []
        with open(fp, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if not lines:
            messagebox.showerror("Lỗi", "File rỗng")
            return
        headers = lines[0].split("|")
        for ln in lines[1:]:
            vals = ln.split("|")
            acc = {h: vals[i] if i < len(vals) else "" for i, h in enumerate(headers)}
            accounts.append(acc)
        messagebox.showinfo("Thành công", f"Đã tải {len(accounts)} tài khoản.\nCác trường: {', '.join(headers)}")
        update_account_option_menu()
    except Exception as e:
        logging.error(f"Lỗi khi tải tài khoản: {e}")
        messagebox.showerror("Lỗi", f"Không thể tải tài khoản: {e}")

def schedule_run():
    try:
        h = int(hour_entry.get())
        m = int(minute_entry.get())
        now = datetime.now()
        if not (0 <= h < 24 and 0 <= m < 60):
            messagebox.showerror("Lỗi", "Giờ hoặc phút không hợp lệ.")
            return
        runt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if runt <= now:
            runt = runt.replace(day=now.day + 1)
        delay = (runt - now).total_seconds()
        sch = sched.scheduler(time.time, time.sleep)
        sch.enter(delay, 1, run_multithread)
        threading.Thread(target=sch.run, daemon=True).start()
        messagebox.showinfo("Đã hẹn", f"Script sẽ chạy lúc {h:02d}:{m:02d}")
    except Exception as e:
        logging.error(f"Lỗi khi hẹn giờ: {e}")
        messagebox.showerror("Lỗi", f"Giờ không hợp lệ hoặc lỗi: {e}")

def update_account_option_menu():
    global account_option_menu
    try:
        account_option_menu.destroy()
    except:
        pass
    if accounts:
        fs = list(accounts[0].keys())
        selected_field_var.set(fs[0] if fs else "")
        account_option_menu = tk.OptionMenu(input_frame, selected_field_var, *fs)
    else:
        selected_field_var.set("")
        account_option_menu = tk.OptionMenu(input_frame, selected_field_var, "Không có tài khoản")
    account_option_menu.grid(row=0, column=3, padx=5)

def add_account_field_to_script():
    if not accounts:
        messagebox.showwarning("Cảnh báo", "Chưa tải tài khoản.")
        return
    fld = selected_field_var.get()
    xpath = simpledialog.askstring("Nhập XPath", f"Nhập XPath cho trường '{fld}':")
    if not xpath:
        return
    script_steps.append(("Gửi ký tự (XPath|Text)", f"{xpath}|{{{fld}}}"))
    script_listbox.insert(tk.END, f"Gửi ký tự (XPath|Text) | {xpath}|{{{fld}}}")

def edit_step(event=None):
    try:
        sel = script_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        old_action, old_value = script_steps[idx]
        win = tk.Toplevel(root)
        win.title("Chỉnh sửa bước")
        win.geometry("450x300")
        tk.Label(win, text="Hành động:", font=('Arial', 10)).pack(pady=5)
        action_entry = ttk.Combobox(win, values=action_combo['values'], width=30)
        action_entry.set(old_action)
        action_entry.pack(pady=5)
        tk.Label(win, text="Giá trị:", font=('Arial', 10)).pack(pady=5)
        value_entry = tk.Text(win, width=50, height=8)
        value_entry.insert("1.0", old_value)
        value_entry.pack(pady=5)
        def save_edit():
            try:
                new_action = action_entry.get()
                new_value = value_entry.get("1.0", tk.END).strip()
                if not new_action:
                    messagebox.showwarning("Lỗi", "Hành động không được để trống.")
                    return
                script_steps[idx] = (new_action, new_value)
                script_listbox.delete(idx)
                script_listbox.insert(idx, f"{new_action} | {new_value}")
                win.destroy()
            except Exception as e:
                logging.error(f"Lỗi khi chỉnh sửa bước: {e}")
                messagebox.showerror("Lỗi", f"Không thể chỉnh sửa bước: {e}")
        tk.Button(win, text="Lưu", command=save_edit, bg="lightgreen").pack(pady=10)
    except Exception as e:
        logging.error(f"Lỗi khi mở cửa sổ chỉnh sửa bước: {e}")

def open_custom_code_popup():
    try:
        win = tk.Toplevel(root)
        win.title("Thêm mã Python tùy chỉnh")
        win.geometry("600x450")
        tk.Label(win, text="Nhập đoạn mã Python cần thực thi:", font=("Arial", 10, "bold")).pack(pady=5)
        code_text = tk.Text(win, width=70, height=18, font=("Consolas", 10))
        code_text.pack(pady=5)
        def save_code_action():
            try:
                user_code = code_text.get("1.0", tk.END).strip()
                if user_code:
                    script_steps.append(("Tùy chỉnh", user_code))
                    first_line = user_code.splitlines()[0]
                    display_line = first_line if first_line else "[...]"
                    script_listbox.insert(tk.END, f"Tùy chỉnh | {display_line}")
                    win.destroy()
                else:
                    messagebox.showwarning("Cảnh báo", "Bạn chưa nhập mã Python.")
            except Exception as e:
                logging.error(f"Lỗi khi lưu mã tùy chỉnh: {e}")
                messagebox.showerror("Lỗi", f"Không thể lưu mã tùy chỉnh: {e}")
        tk.Button(win, text="Lưu hành động", command=save_code_action, bg="lightgreen", width=20).pack(pady=10)
    except Exception as e:
        logging.error(f"Lỗi khi mở cửa sổ mã tùy chỉnh: {e}")
def mo_chrome_py():
    def run_script():
        subprocess.run([sys.executable, "chromeinstall.py"])
    threading.Thread(target=run_script).start()
def update_client():
    def run_script():
        subprocess.run([sys.executable, "updateclient.py"])
    threading.Thread(target=run_script).start()
# GUI
root = tk.Tk()
root.title("🔧 Auto Chrome Script GUI (Tiếng Việt)")
root.geometry("760x780+0+0")
root.minsize(650, 750)

container = tk.Frame(root)
container.pack(fill=tk.BOTH, expand=True)
canvas = tk.Canvas(container)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
scrollable = tk.Frame(canvas)
scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

main_frame = tk.Frame(scrollable)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=3)
main_frame.rowconfigure(1, weight=1)

left = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
left.columnconfigure(0, weight=1)
left.rowconfigure(1, weight=1)
tk.Label(left, text="📜 Script đã lưu:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
script_option_listbox = tk.Listbox(left, width=20, height=10)
script_option_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
scrollbar_left = ttk.Scrollbar(left, orient="vertical", command=script_option_listbox.yview)
scrollbar_left.grid(row=1, column=1, sticky="ns")
script_option_listbox.config(yscrollcommand=scrollbar_left.set)
tk.Button(left, text="🔄 Tải lại danh sách", command=refresh_script_list).grid(row=2, column=0, pady=5)
tk.Button(left, text="📂 Xem Profiles", command=show_profiles).grid(row=3, column=0, pady=5)
tk.Button(left, text="🗑️ Xóa Tất Cả Profiles", command=clear_profiles).grid(row=4, column=0, pady=5)
tk.Button(left, text="Cài Chromedriver", command=mo_chrome_py).grid(row=5, column=0, pady=5)
tk.Button(left, text="Cập nhật app", command=update_client).grid(row=6, column=0, pady=5)
script_option_listbox.bind("<<ListboxSelect>>", on_script_option_select)

right = tk.Frame(main_frame, bd=2, relief=tk.GROOVE)
right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
right.columnconfigure(0, weight=1)
right.rowconfigure(1, weight=1)
tk.Label(right, text="📝 Các bước Script:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
script_listbox = tk.Listbox(right, width=50, height=15)
script_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
scrollbar_right = ttk.Scrollbar(right, orient="vertical", command=script_listbox.yview)
scrollbar_right.grid(row=1, column=1, sticky="ns")
script_listbox.config(yscrollcommand=scrollbar_right.set)
script_listbox.bind("<Double-Button-1>", edit_step)

input_frame = tk.Frame(main_frame)
input_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
input_frame.columnconfigure(1, weight=1)
tk.Label(input_frame, text="Hành động:").grid(row=0, column=0, sticky="w")
action_combo = ttk.Combobox(
    input_frame,
    values=[
        "Mở URL",
        "Ngủ",
        "Click XPath",
        "Gửi ký tự (XPath|Text)",
        "Swipe (Hướng|Pixel đầu|Pixel cuối)",
        "Click Full XPath",
        "Tùy chỉnh",
        "Tìm và Nhập (Text|Value)",
        "Tìm và Nhập vào Phần Tử Gần Kề (Text|Value|Position|ElementType)"
    ],
    width=30
)
action_combo.grid(row=0, column=1, sticky="ew", padx=5)
tk.Label(input_frame, text="Giá trị:").grid(row=1, column=0, sticky="w")
value_entry = tk.Entry(input_frame)
value_entry.grid(row=1, column=1, sticky="ew", padx=5)
selected_field_var = tk.StringVar()
update_account_option_menu()
tk.Button(input_frame, text="Thêm trường tài khoản vào Script", command=add_account_field_to_script).grid(row=0, column=4, padx=5)
tk.Button(input_frame, text="📄 Tải tài khoản", command=load_accounts_from_text).grid(row=0, column=5, padx=5)

def delete_step():
    try:
        sel = script_listbox.curselection()
        if not sel:
            messagebox.showwarning("Cảnh báo", "Chọn bước cần xóa.")
            return
        idx = sel[0]
        script_listbox.delete(idx)
        del script_steps[idx]
    except Exception as e:
        logging.error(f"Lỗi khi xóa bước: {e}")

tk.Button(input_frame, text="➕ Thêm bước", command=add_step).grid(row=1, column=2, columnspan=2, pady=5)
tk.Button(input_frame, text="🗑️ Xóa bước", command=delete_step).grid(row=1, column=3, columnspan=3, pady=5)

settings = load_settings()
option_frame = tk.Frame(scrollable)
option_frame.pack(fill="x", padx=10, pady=5)
row1 = tk.Frame(option_frame)
row1.pack(fill="x", pady=2)
tk.Label(row1, text="Số luồng:").pack(side="left")
threads_entry = tk.Entry(row1, width=3)
threads_entry.insert(0, settings.get("threads", "1"))
threads_entry.pack(side="left", padx=(2, 10))
headless_var = tk.BooleanVar()
tk.Checkbutton(row1, text="Ẩn Chrome (headless)", variable=headless_var).pack(side="left", padx=5)
auto_quit_var = tk.BooleanVar(value=True)
tk.Checkbutton(row1, text="Tự đóng Chrome khi xong", variable=auto_quit_var).pack(side="left", padx=5)
auto_create_profiles_var = tk.BooleanVar(value=settings.get("auto_create_profiles", "True") == "True")
tk.Checkbutton(row1, text="Tạo profile tự động", variable=auto_create_profiles_var).pack(side="left", padx=5)
delete_profiles_after_run_var = tk.BooleanVar(value=settings.get("delete_profiles_after_run", "False") == "True")
tk.Checkbutton(row1, text="Xóa profile sau khi chạy", variable=delete_profiles_after_run_var).pack(side="left", padx=5)
row2 = tk.Frame(option_frame)
row2.pack(fill="x", pady=2)
tk.Label(row2, text="Hẹn giờ chạy (Giờ:Phút):").pack(side="left")
hour_entry = tk.Entry(row2, width=3)
hour_entry.insert(0, "15")
hour_entry.pack(side="left", padx=(2, 0))
tk.Label(row2, text=":").pack(side="left")
minute_entry = tk.Entry(row2, width=3)
minute_entry.insert(0, "30")
minute_entry.pack(side="left", padx=(2, 10))
tk.Button(row2, text="🕑 Hẹn giờ", command=schedule_run, bg="orange").pack(side="left")
row3 = tk.Frame(option_frame)
row3.pack(fill="x", pady=2)
tk.Label(row3, text="Kích thước Chrome W x H:").pack(side="left")
chrome_width = tk.Entry(row3, width=5)
chrome_width.insert(0, settings.get("width", "1200"))
chrome_width.pack(side="left", padx=(2, 0))
tk.Label(row3, text="x").pack(side="left")
chrome_height = tk.Entry(row3, width=5)
chrome_height.insert(0, settings.get("height", "800"))
chrome_height.pack(side="left", padx=(2, 10))
row4 = tk.Frame(option_frame)
row4.pack(fill="x", pady=2)
tk.Button(row4, text="▶️ Chạy ngay", command=run_multithread, bg="green", fg="white").pack(side="left", padx=(0, 10))
tk.Button(row4, text="💾 Lưu script", command=save_script).pack(side="left")
tk.Button(option_frame, text="❓ Xem hướng dẫn", command=show_guide, bg="lightblue").pack(fill="x", padx=10, pady=5)
progress_frame = tk.Frame(scrollable)
progress_frame.pack(fill="x", padx=9, pady=9)
progress_label = tk.Label(progress_frame, text="Chưa chạy...")
progress_label.pack(anchor="w")
progress_var = tk.IntVar()
progressbar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
progressbar.pack(fill="x", pady=5)

def on_settings_change(*args):
    try:
        save_settings(
            threads_entry.get(),
            chrome_width.get(),
            chrome_height.get(),
            str(auto_create_profiles_var.get()),
            str(delete_profiles_after_run_var.get())
        )
    except Exception as e:
        logging.error(f"Lỗi khi lưu cài đặt: {e}")

threads_entry.bind('<FocusOut>', on_settings_change)
chrome_width.bind('<FocusOut>', on_settings_change)
chrome_height.bind('<FocusOut>', on_settings_change)
auto_create_profiles_var.trace('w', on_settings_change)
delete_profiles_after_run_var.trace('w', on_settings_change)

refresh_script_list()
root.mainloop()