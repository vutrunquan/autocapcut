# 🎬 AutoCapCut Pro - Tự Động Khớp Media & Âm Thanh Cho CapCut PC

Công cụ tự động hóa biên tập video CapCut chuyên nghiệp:
- Tự động đồng bộ hóa **ảnh và video** với **giọng đọc (Voice)** chuẩn xác từng mili-giây theo file phụ đề SRT và kịch bản phân cảnh.
- Giao diện được thiết kế trực quan, đầy đủ các tính năng nâng cao: Keyframe chuyển động, chuyển cảnh Transitions, Nhạc nền BGM, Xóa watermark Gemini, và Sắp xếp media đa chế độ.

---

## 🌟 Toàn Bộ Các Tính Năng Như Trong Ảnh

### 1. Nạp File Âm Thanh Linh Hoạt (Audio File)
- Hỗ trợ chọn **một hoặc nhiều file audio giọng đọc** (`.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`).
- Khi chọn nhiều file, hệ thống sẽ tự động ghép nối liên tục theo thứ tự trên timeline.

### 2. File Phụ Đề SRT (SRT File)
- Nhận diện phụ đề chuẩn xác với timestamp chi tiết để căn thời gian đọc của từng câu.

### 3. Khung Nhập Kịch Bản (Scenes)
- Hỗ trợ **nhập/paste trực tiếp kịch bản** vào khung văn bản lớn hoặc nhấn **Browse** để nạp file `.txt`, `.csv`.
- Hỗ trợ nút **Copy** tiện lợi để sao chép nhanh toàn bộ kịch bản vào clipboard.
- Mỗi dòng là một cảnh ứng với một ảnh/video. Tool tự động căn thời gian media theo đúng thời gian đọc nội dung của dòng đó.

### 4. Thư Mục Media (Ảnh & Video)
- Hỗ trợ cả **hình ảnh** (`.jpg`, `.png`, `.webp`, `.bmp`) và **video clip** (`.mp4`, `.mov`, `.mkv`, `.webm`).
- Menu **Sắp xếp media** đa dạng:
  - `Sắp xếp media theo ABC` (Số tự nhiên chuẩn: `1`, `2`, `10`, `001`, `002`...)
  - `Sắp xếp media theo thời gian Cũ đến Mới`
  - `Sắp xếp media theo thời gian Mới đến Cũ`

### 5. Nhạc Nền (BGM)
- Hỗ trợ chọn một hoặc nhiều file nhạc nền.
- Tự động đưa vào track âm thanh riêng với âm lượng 15% để giọng đọc luôn rõ ràng, tự động lặp lại cho khớp độ dài video.
- Có nút **Xóa** nhanh đường dẫn nhạc nền.

### 6. Xóa Watermark Gemini Khỏi Ảnh (Reverse Alpha Blending - Lossless)
- Tích hợp công nghệ xóa watermark chuẩn xác từ repository **[GargantuaX/gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover.git)**.
- Thay vì dùng thuật toán inpainting mờ đục hoặc chắp vá, hệ thống sử dụng **thuật toán toán học Reverse Alpha Blending** đảo ngược chính xác kênh Alpha của logo ngôi sao 4 cánh Google Gemini/Imagen, phục hồi lại 100% chi tiết gốc không làm mờ, không biến dạng ảnh.
- Hỗ trợ xử lý song song đa luồng (multi-threaded concurrent processing) cực nhanh trên toàn bộ danh sách ảnh của dự án.

### 7. Hiệu Ứng Chuyển Cảnh (Transitions)
Menu lựa chọn 8 kiểu chuyển cảnh mượt mà:
- `Không transition`
- `Black Fade` (Flash Black)
- `Slow Fade` (Dissolve / Hòa tan mượt)
- `Fade Swipe` (Trượt ngang)
- `Fade Wipe` (Gạt cảnh)
- `Fade Shift` (Đẩy cảnh)
- `Basic Black` (Chuyển đen cơ bản)
- `Blink Fade` (Nhấp nháy chuyển cảnh)

### 8. Auto Keyframe Chuyển Động (Pan & Zoom)
Tùy biến chi tiết thông số từng chuyển động:
- **Zoom in**: Phóng to từ 100% lên `[ 110 ] %`
- **Zoom out**: Thu nhỏ từ `[ 110 ] %` về 100%
- **Pan up**: Lia khung hình lên trên với `X [ 0 ]`, `Y [ 100 ]`, `Scale [ 110 ] %`
- **Pan down**: Lia khung hình xuống dưới với `X [ 0 ]`, `Y [ 100 ]`, `Scale [ 110 ] %`
- **Pan left**: Lia khung hình sang trái với `X [ 190 ]`, `Y [ 0 ]`, `Scale [ 110 ] %`
- **Pan right**: Lia khung hình sang phải với `X [ 190 ]`, `Y [ 0 ]`, `Scale [ 110 ] %`
- Có nút **✓ Chọn Tất Cả** và **✕ Bỏ Chọn** nhanh.

---

## ✨ Các Tính Năng Pro Mới Bổ Sung (Dễ Sử Dụng)

### 🎯 1. Bộ Thiết Lập Sẵn 1-Click (Pro Presets)
Chỉ cần chọn 1 preset trong dropdown, hệ thống sẽ tự động cấu hình toàn bộ thông số:
- **🔥 TikTok / Reels / Shorts Siêu Cuốn**: Tỉ lệ dọc 9:16, nhịp nhanh, SFX 60%, chữ vàng TikTok nổi bật, mờ nền canvas blur, ducking.
- **🎬 YouTube Kể Chuyện Điện Ảnh**: Tỉ lệ ngang 16:9, hạt phim Soft Grain, chữ trắng truyền thống, slow fade, SFX 35%.
- **💼 Tin Tức & Phân Tích Tài Chính**: Tỉ lệ 16:9, chữ xanh lá tài chính, chuyển cảnh Fade Wipe, ducking êm dịu.
- **⚡ Tối Giản Siêu Tốc**: Tối giản không SFX, không filter, tập trung vào hình ảnh và giọng đọc.
- **⚙️ Tùy Chỉnh Thủ Công**: Tự do điều chỉnh theo ý muốn.

### 📐 2. Tỉ Lệ Khung Hình & Độ Phân Giải (Aspect Ratio)
- `16:9` (1920x1080 - YouTube, Facebook ngang)
- `9:16` (1080x1920 - TikTok, Reels, YouTube Shorts dọc)
- `1:1` (1080x1080 - Vuông Instagram, Facebook Post)

### ✂️ 3. Công Cụ Kịch Bản Nhanh (Script Tools)
- **✂️ Tách Câu**: Nếu dán một đoạn văn dài, 1 click sẽ tự động ngắt theo dấu chấm, hỏi, cảm thành từng dòng (1 dòng = 1 cảnh).
- **🧹 Dọn Dòng**: Tự động loại bỏ các dòng trắng thừa.
- **📋 Dán / Copy / ✕ Xóa sạch**: Thao tác 1 click.

### 🔊 4. Âm Thanh Chuyển Cảnh (SFX Whoosh / Swoosh)
- Tự động đặt các âm thanh SFX điện ảnh (Whoosh, Swoosh, Pop) đúng vào điểm giao giữa các cảnh với âm lượng tùy chỉnh (mặc định 50%).

### 🎨 5. Tự Động Làm Mờ Nền (Canvas Blur - Chống Viền Đen)
- Khi ảnh hoặc video có tỉ lệ không khớp với khung hình (ví dụ ảnh dọc đặt vào video 16:9 hoặc ảnh ngang đặt vào video 9:16), CapCut sẽ tự động làm mờ hậu cảnh, loại bỏ hoàn toàn dải viền đen xấu xí.

### 🎚️ 6. Audio Ducking & Fade In/Out
- **Audio Ducking**: Tự động hạ âm lượng nhạc nền khi có tiếng giọng đọc và nâng nhẹ khi hết câu.
- **Audio Fade In/Out**: Nhạc nền mở và tắt êm ái, không bị ngắt cụt.
- **Tùy chỉnh âm lượng BGM**: Nhập % trực tiếp (10%, 15%, 20%, 30%...).

### 🎞️ 7. Bộ Lọc Màu Điện Ảnh (Cinematic Filters)
- `Soft Grain`: Hạt phim điện ảnh vintage.
- `Vintage 1980`: Tông màu retro 1980s.
- `VHS Retro`: Hiệu ứng băng từ cổ điển.
- `Peach Fuzz`: Tông màu ấm điện ảnh.
- `Lover Blue`: Tông màu lạnh điện ảnh.
- `BW Retro`: Trắng đen hoài niệm.

### 💬 8. Bảng Màu Phụ Đề Nổi Bật (Subtitle Styles)
- **Vàng Nổi Bật (TikTok / Viral)**: Chữ vàng viền đen dày, cực kỳ thu hút người xem.
- **Trắng Truyền Thống (Classic White)**: Thanh lịch, chuẩn YouTube.
- **Xanh Công Nghệ (Cyan Modern)**: Phong cách Tech, AI, hiện đại.
- **Xanh Lá Tài Chính (Finance Green)**: Phong cách tiền tệ, crypto, đầu tư.

### 🔔 9. Kêu Gọi Đăng Ký Kênh (CTA Subscribe & Chuông)
- Tự động chèn thanh banner nhắc người xem Đăng ký kênh (Subscribe) cùng tiếng chuông "Ding" ngân vang ở những giây cuối của video.

---

## 🖥️ Cách Khởi Chạy

### 1. Giao diện Desktop App
Nhấp đúp chuột vào shortcut **`AutoCapCut Pro`** trên màn hình Desktop hoặc chạy file:
```bat
Chay_AutoCapCut_GUI.bat
```

### 2. Giao diện Web Trình Duyệt (Web UI)
Chạy file:
```bat
Chay_AutoCapCut_Web.bat
```
Truy cập tại: `http://localhost:8000`
