# Hướng Dẫn Sử Dụng AutoCapCut Studio Trên macOS 🍏

AutoCapCut Studio hỗ trợ **100% nguyên bản** trên hệ điều hành **macOS**, tương thích hoàn toàn với cả:
- **Apple Silicon**: Chip **M1, M2, M3, M4** (Kiến trúc ARM64 nguyên bản, siêu mượt và mát máy).
- **Intel**: Các dòng máy Mac sử dụng chip Intel Core i5, i7, i9 (Kiến trúc x86_64).

---

## 1. Yêu Cầu Cần Có
1. **Python 3.9+**:
   - Nếu chưa có, bạn tải tại [python.org/downloads/macos](https://www.python.org/downloads/macos/)
   - Hoặc cài qua Homebrew:
     ```bash
     brew install python python-tk
     ```
2. **CapCut Desktop cho macOS**:
   - Tải chính thức từ Mac App Store hoặc trang chủ CapCut.

---

## 2. Cài Đặt Tự Động (Chỉ Cần Làm 1 Lần)

Mở **Terminal** trên Mac của bạn và chạy lệnh sau trong thư mục dự án:

```bash
chmod +x setup_macos.sh
./setup_macos.sh
```

Script sẽ tự động:
- Phát hiện kiến trúc chip của máy Mac (Intel hoặc Apple Silicon M).
- Tạo môi trường ảo Python `venv` độc lập để không ảnh hưởng đến hệ điều hành.
- Cài đặt đầy đủ các thư viện phụ thuộc (`customtkinter`, `fastapi`, `pillow`,...).
- Cấp quyền nhấp đúp chạy nhanh cho các file `.command`.

---

## 3. Cách Mở Ứng Dụng Trên Mac

Sau khi cài đặt xong, bạn có thể khởi động cực kỳ đơn giản bằng **2 cách**:

### Cách 1: Nhấp đúp chuột trong Finder (Tiện lợi nhất)
- **Mở giao diện ứng dụng Desktop (GUI)**:
  - Nhấp đúp chuột vào file: `Chay_AutoCapCut_GUI.command`
- **Mở giao diện Web trong trình duyệt**:
  - Nhấp đúp chuột vào file: `Chay_AutoCapCut_Web.command` *(Tự động mở Safari/Chrome tại `http://localhost:8000`)*

> **Lưu ý nhỏ cho lần đầu mở file `.command` trên Mac:**
> Nếu macOS hiển thị thông báo bảo mật *"App can't be opened because it is from an unidentified developer"*, bạn chỉ cần:
> 1. Chuột phải (hoặc giữ phím `Control` + click) vào file `.command`
> 2. Chọn **Open** (Mở) -> Chọn tiếp **Open** là xong! Từ lần thứ 2 trở đi bạn có thể nhấp đúp bình thường.

---

### Cách 2: Mở bằng dòng lệnh Terminal
```bash
# Mở Desktop GUI
./venv/bin/python gui.py

# Hoặc mở Web Interface
./venv/bin/python web_app.py

# Hoặc sử dụng giao diện dòng lệnh CLI
./venv/bin/python cli.py --help
```

---

## 4. Đường Dẫn Lưu Dự Án CapCut Trên macOS

Phần mềm đã được lập trình sẵn để tự động phát hiện chính xác thư mục Drafts của CapCut trên macOS:
- Bản cài trực tiếp:
  `~/Movies/CapCut/User Data/Projects/com.lveditor.draft`
- Bản tải từ Mac App Store:
  `~/Library/Containers/com.lemon.lvoverseas/Data/Movies/CapCut/User Data/Projects/com.lveditor.draft`
- Bản Cắt Áo (Jianying Pro):
  `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

Ngay khi bạn nhấn **"Bắt đầu tạo dự án CapCut"**, dự án mới sẽ được chèn thẳng vào đầu danh sách của CapCut Mac. Khi bạn mở CapCut lên, project sẽ hiển thị ngay lập tức!

---

## 5. Xử Lý Sự Cố Thường Gặp Trên Mac

### Lỗi Tkinter (`No module named '_tkinter'`)
- Thường gặp nếu bạn dùng Python cài từ Homebrew mà chưa cài `python-tk`.
- **Cách khắc phục**:
  Chạy lệnh:
  ```bash
  brew install python-tk
  ```

### Cấp quyền truy cập tệp (Permission Denied)
- Nếu CapCut hoặc Terminal không đọc được thư mục Media trên Desktop hoặc Downloads:
- Vào **System Settings (Cài đặt hệ thống)** -> **Privacy & Security (Bảo mật & Quyền riêng tư)** -> **Files and Folders (Tệp và thư mục)** -> Cho phép Terminal/Python truy cập `Desktop` và `Downloads`.
