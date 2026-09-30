# 💰 HƯỚNG DẪN THƯƠNG MẠI HOÁ AUTOCAPCUT STUDIO

Tài liệu này hướng dẫn chi tiết cách thức vận hành hệ thống bản quyền, dùng thử 3 ngày và cấp quyền vĩnh viễn gói 150.000đ cho khách hàng.

---

## 🌟 1. Cơ Chế Hoạt Động Của Hệ Thống

1. **Dùng thử miễn phí 3 ngày (72 giờ)**:
   - Tự động kích hoạt ngay khi khách hàng mở phần mềm lần đầu tiên trên máy tính của họ.
   - Khách có thể trải nghiệm toàn bộ tính năng cao cấp (chèn nhạc, hiệu ứng, transition, sync phụ đề, camera pacing AI...).
   - Có đồng hồ đếm ngược hiển thị trên huy hiệu bản quyền (ví dụ: `⏳ Dùng thử: Còn 2 ngày 18h`).

2. **Khóa phần mềm khi hết 3 ngày**:
   - Khi hết 3 ngày, nút "Bắt đầu tạo dự án CapCut" sẽ tự động bị **KHÓA**.
   - Cả giao diện Desktop GUI, Web App, Command Line (CLI) và Core Engine đều chặn quá trình render draft.
   - Phần mềm hiển thị hộp thoại yêu cầu kích hoạt bản quyền trọn đời 150.000 VNĐ.

3. **Mã máy độc nhất (Machine ID - HWID)**:
   - Mỗi máy tính (Windows hoặc macOS Intel / chip M) sẽ có 1 mã máy riêng biệt (ví dụ: `AC-6370-F993-CD03`).
   - Mã được đọc từ Registry hệ thống Windows (`MachineGuid`) hoặc IORegistry macOS (`IOPlatformUUID`). Khách không thể sao chép bản quyền sang máy khác.

4. **Chữ ký mã hóa HMAC-SHA256 (Hoạt động Offline 100%)**:
   - Bạn **không cần thuê máy chủ (server) hay domain** tốn kém hàng tháng.
   - Bản quyền được xác thực bằng mật mã học offline: Chỉ bạn (nắm giữ công cụ `admin_keygen.py`) mới tạo được License Key hợp lệ cho mã máy đó.

5. **Chống gian lận (Anti-tamper & Anti-clock rollback)**:
   - Chống tua lùi ngày giờ hệ thống.
   - Có dấu vết hệ thống phụ chống việc xóa file để gian lận ngày dùng thử.

---

## 🚀 2. Quy Trình Bán Hàng & Cấp Key (3 Bước Đơn Giản)

### BƯỚC 1: Khách hàng gửi Mã Máy (Machine ID) & Chuyển khoản 150k
- Khách mở phần mềm, bấm vào huy hiệu bản quyền góc trên (hoặc khi hết hạn màn hình tự động bật lên).
- Khách bấm nút **"Sao chép"** mã máy (ví dụ: `AC-6370-F993-CD03`).
- Khách quét mã **VietQR** có sẵn trên giao diện để chuyển 150.000đ (tiền và nội dung chuyển khoản đã được điền tự động).
- Khách gửi mã máy qua Zalo/Facebook cho bạn.

---

### BƯỚC 2: Bạn tạo Mã Kích Hoạt (License Key) cho khách

Bạn có 2 cách cực kỳ nhanh chóng:

#### Cách 1: Dùng giao diện đồ họa (Khuyên dùng)
1. Nhấp đúp chuột vào file:
   - Trên Windows: `admin_keygen.bat`
   - Trên macOS: `admin_keygen.command`
2. Dán mã máy khách vừa gửi vào ô **Mã Thiết Bị (Machine ID)**.
3. Bấm **"Tạo Key & Sao Chép"**.
4. Key đã được tự động lưu vào Clipboard máy bạn (ví dụ: `ACCP-6370-1750-031D-DC29`).

#### Cách 2: Dùng dòng lệnh (Terminal / CMD)
Chạy lệnh:
```bash
python admin_keygen.py AC-6370-F993-CD03
```
Màn hình sẽ hiển thị Key và tự động copy vào Clipboard cho bạn.

---

### BƯỚC 3: Khách nhập Key để mở khóa Vĩnh Viễn
1. Bạn gửi mã Key (dạng `ACCP-XXXX-XXXX-XXXX-XXXX`) lại cho khách.
2. Khách dán mã Key vào ô **"Nhập mã kích hoạt (License Key)"** trên app.
3. Bấm **"Kích hoạt ngay"**.
4. Ứng dụng ngay lập tức hiển thị huy hiệu: **"✨ Bản quyền vĩnh viễn"**, mở khóa toàn bộ tính năng và dùng trọn đời trên máy tính đó!

---

## ⚙️ 3. Cài Đặt Thông Tin Ngân Hàng & VietQR Của Bạn

Để khách hàng khi bấm vào app sẽ nhìn thấy đúng số tài khoản ngân hàng và mã QR chuyển khoản của bạn:

1. Chạy file `admin_keygen.bat` (hoặc `admin_keygen.command`).
2. Chọn tab **"Cài Đặt Thanh Toán (150k)"**.
3. Điền các thông tin:
   - **Tên ngân hàng**: VD: `MBBank`, `Vietcombank`, `Techcombank`, `ACB`, `TPBank`, `VPBank`, v.v.
   - **Số tài khoản**: Số tài khoản nhận tiền của bạn.
   - **Tên chủ tài khoản**: Họ và tên bạn viết hoa không dấu (VD: `VU TRUNG QUAN`).
   - **Giá gói**: `150000` (150.000 VNĐ).
   - **Zalo hỗ trợ**: Số điện thoại Zalo của bạn để khách liên hệ.
4. Bấm **"Lưu Cài Đặt Thanh Toán"**.

> Hoặc bạn có thể mở trực tiếp file `license_config.json` ở thư mục gốc dự án để sửa thông tin bất cứ lúc nào.

---

## 📦 4. Lưu Ý Quan Trọng Khi Đóng Gói Gửi Cho Khách Hàng

Khi nén file zip hoặc gửi thư mục cho khách:
- **KHÔNG GỬI** các file của Admin:
  - ❌ `admin_keygen.py`
  - ❌ `admin_keygen.bat`
  - ❌ `admin_keygen.command`
  *(Chỉ giữ những file này trên máy tính của riêng bạn để tạo key).*
- **GỬI CHO KHÁCH**:
  - ✅ Thư mục `autocapcut/`
  - ✅ File `gui.py` & `Chay_AutoCapCut_GUI.bat` (hoặc `.command` cho Mac)
  - ✅ File `web_app.py` & `Chay_AutoCapCut_Web.bat`
  - ✅ File `cli.py`
  - ✅ File `license_config.json` (chứa thông tin STK của bạn để khách thấy QR chuyển tiền)
  - ✅ File `requirements.txt`

---

## 🛡️ 5. Tổng Kết Các Lệnh CLI Bản Quyền Cho Kỹ Thuật Viên

- Xem mã máy và trạng thái bản quyền hiện tại:
  ```bash
  python cli.py --hwid
  ```
- Kích hoạt bản quyền qua dòng lệnh:
  ```bash
  python cli.py --activate ACCP-XXXX-XXXX-XXXX-XXXX
  ```
- Tạo key bản quyền từ mã máy:
  ```bash
  python admin_keygen.py <HWID>
  ```
