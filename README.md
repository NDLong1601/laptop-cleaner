<div align="center">

<img src="assets/icon.png" alt="Laptop Cleaner & Optimizer Logo" width="130" height="130" />

# Laptop Cleaner & Optimizer

### Giải Pháp Dọn Dẹp, Tối Ưu Hóa & Tăng Tốc Toàn Diện Cho Windows 11 / 10

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6%20%26%20Fluent%20Widgets-00BCF9?logo=qt&logoColor=white)](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
[![Style](https://img.shields.io/badge/Design-Windows%2011%20Mica-5c2d91)](https://learn.microsoft.com/en-us/windows/apps/design/style/mica)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/Build-PyInstaller%20One--File%20EXE-orange)](https://pyinstaller.org/)

<p align="center">
  <b>Laptop Cleaner & Optimizer</b> là phần mềm tiện ích desktop hiện đại được xây dựng nhằm giúp người dùng theo dõi tài nguyên, dọn sạch tệp rác, phân tích chuyên sâu thư mục AppData, tìm kiếm tệp trùng lặp, tối ưu bộ nhớ RAM và quản lý hệ điều hành với giao diện Fluent Design chuẩn mực của Windows 11.
</p>

[Tính Năng](#-tính-năng-nổi-bật) •
[Giao Diện](#-trải-nghiệm-giao-diện--hiệu-ứng) •
[Cài Đặt](#-cài-đặt--chạy-từ-mã-nguồn) •
[Build .EXE](#-đóng-gói-thành-file-exe) •
[Cấu Trúc](#-cấu-trúc-dự-án) •
[Cơ Chế An Toàn](#-cơ-chế-an-toàn-dữ-liệu) •
[Đóng Góp](#-tác-giả--bản-quyền)

---

</div>

## 📖 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng Nổi Bật](#-tính-năng-nổi-bật)
- [Trải Nghiệm Giao Diện & Hiệu Ứng](#-trải-nghiệm-giao-diện--hiệu-ứng)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
- [Cài Đặt & Chạy Từ Mã Nguồn](#-cài-đặt--chạy-từ-mã-nguồn)
- [Đóng Gói Thành File .EXE Độc Lập](#-đóng-gói-thành-file-exe-độc-lập)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [Cơ Chế An Toàn Dữ Liệu](#-cơ-chế-an-toàn-dữ-liệu)
- [Công Nghệ & Thư Viện Sử Dụng](#-công-nghệ--thư-viện-sử-dụng)
- [Tác Giả & Bản Quyền](#-tác-giả--bản-quyền)

---

## 🌟 Giới Thiệu

Theo thời gian sử dụng, hệ điều hành Windows tích tụ hàng chục Gigabyte tệp tạm (`%TEMP%`, Windows Update cache, crash logs, thumbnail cache, trình duyệt cache), cùng các tiến trình chạy ngầm làm đầy bộ nhớ RAM và làm chậm máy tính. 

**Laptop Cleaner & Optimizer** được thiết kế như một trung tâm điều khiển (Command Center) tất cả trong một:
1. **Trực quan & Hiện đại:** Áp dụng hệ thống thiết kế Fluent UI của Windows 11 với hiệu ứng nền trong suốt Mica, biểu đồ sóng thời gian thực và chuyển động mượt mà.
2. **Can thiệp cấp thấp an toàn:** Sử dụng Windows Native API (`EmptyWorkingSet`, `winreg`, `psutil`) để giải phóng RAM và truy vấn cấu hình máy tính chuẩn xác mà không cần phần mềm thứ ba can thiệp nguy hiểm.
3. **Minh bạch & Kiểm soát:** Mọi tệp tin trước khi xóa đều được phân loại mức độ rủi ro (An toàn, Cân nhắc, Hệ thống) và hỗ trợ xóa thông qua Thùng rác (Recycle Bin) để có thể phục hồi khi cần.

---

## 🚀 Tính Năng Nổi Bật

Phần mềm tích hợp đầy đủ **12 phân hệ chuyên sâu**:

| Phân Hệ | Biểu Tượng | Mô Tả Chi Tiết |
|---|:---:|---|
| **Tổng Quan (Dashboard)** | 🏠 | Hiển thị điểm số sức khỏe hệ thống (0–100), biểu đồ CPU / RAM / Ổ đĩa thời gian thực, nút **Tối Ưu Nhanh 1-Click** giải phóng tức thì tài nguyên. |
| **Dọn Rác Hệ Thống** | 🗑️ | Quét và dọn sạch các khu vực rác phổ biến: `%TEMP%`, `C:\Windows\Temp`, Windows Update Cache, Thumbnail Cache, Recycle Bin, Browser Cache (Chrome, Edge, Firefox), crash dump và file log cũ. |
| **Phân Tích AppData & Thư Mục** | 📁 | Quét toàn diện thư mục bất kỳ hoặc `AppData` (`Roaming`, `Local`, `LocalLow`). Tự động đánh giá tác động: **An toàn**, **Cần cân nhắc** hoặc **Ảnh hưởng cấu hình** trước khi xóa. |
| **Tìm Tệp Trùng Lặp** | 🔁 | Dùng thuật toán băm kép (kích thước + MD5 hash) để tìm kiếm chính xác các tệp trùng lặp nội dung. Tự động đánh dấu bản sao và giữ lại bản gốc. |
| **Thợ Săn Tệp Dung Lượng Khủng** | 📦 | Quét và phân loại các tệp chiếm nhiều dung lượng trên ổ đĩa (>100MB, >500MB, >1GB) theo định dạng: Video, File nén (ZIP/RAR), File ảnh đĩa (ISO), Bộ cài đặt (EXE/MSI). |
| **Dấu Vết Riêng Tư** | 🔒 | Xóa lịch sử tệp mở gần đây (Recent Files), hộp thoại Windows Run, danh sách tác vụ nhanh JumpLists, lịch sử gõ phím và bộ đệm nháp tạm. |
| **Quản Lý & Gỡ Ứng Dụng** | 📋 | Liệt kê toàn bộ phần mềm đã cài đặt từ Windows Registry (kèm nhà phát hành, phiên bản, dung lượng, ngày cài). Hỗ trợ kích hoạt trình gỡ cài đặt tiêu chuẩn hoặc chế độ gỡ âm thầm (Silent Uninstall). |
| **Tiến Trình Chạy Ngầm** | ⚡ | Giám sát danh sách processes đang hoạt động, xếp hạng theo CPU% và RAM sử dụng. Cho phép người dùng kết thúc tiến trình gây đơ lag máy. |
| **Tối Ưu Hóa RAM** | 🧠 | Tận dụng Windows API để purge bộ nhớ đệm Working Set của tất cả tiến trình. Hiển thị thông số RAM trước/sau và biểu đồ sóng mini dạng Bezier thời gian thực. |
| **Khởi Động Cùng Windows** | 🚀 | Quản lý danh sách phần mềm tự khởi động khi mở máy (`HKEY_CURRENT_USER` & `HKEY_LOCAL_MACHINE` Run keys). Cho phép bật/tắt để tăng tốc độ boot máy. |
| **Pin & Hiệu Năng Laptop** | 🔋 | Theo dõi phần trăm pin, trạng thái cắm sạc, mức tiêu hao năng lượng. Chuyển đổi nhanh các gói năng lượng Windows (Balanced, High Performance, Power Saver). |
| **Lên Lịch Tự Động** | 📅 | Thiết lập lịch trình tự động quét và dọn rác định kỳ (Hàng ngày / Hàng tuần / Hàng tháng) hoặc khi khởi động máy. |

---

## 🎨 Trải Nghiệm Giao Diện & Hiệu Ứng

Ứng dụng được trau chuốt tỉ mỉ với bộ engine hoạt ảnh (`src/ui/animations.py`):

- **Hiệu Ứng Mica & Theme:** Hỗ trợ Windows 11 Mica translucent effect; chuyển đổi mượt mà giữa chế độ Sáng (Light) và Tối (Dark).
- **Staggered Card Entrance:** Hiệu ứng xuất hiện so le phân tầng khi khởi động từng thẻ chức năng trên Dashboard.
- **Micro-Interactions (Spring Bounce):** Hiệu ứng co dãn tự nhiên khi bấm các nút hành động chính (`PrimaryPushButton`).
- **Rolling Numeric Counter:** Các chỉ số dung lượng (Bytes/MB/GB) và phần trăm RAM tự động nhảy số chuyển động mượt mà khi cập nhật.
- **Mini Bezier Wave Sparkline:** Đồ họa sóng mượt biểu diễn biến động RAM theo thời gian thực thay thế thanh tiến trình tĩnh nhàm chán.
- **Breathing Pulse Indicator:** Đèn cảnh báo nhấp nháy nhịp thở khi hệ thống rơi vào trạng thái tài nguyên quá tải hoặc dung lượng đĩa cạn kiệt.

---

## 💻 Yêu Cầu Hệ Thống

- **Hệ điều hành:** Windows 10 (bản 1809 trở lên) hoặc Windows 11 (khuyên dùng).
- **Kiến trúc:** 64-bit (x64 / AMD64).
- **Môi trường (nếu chạy từ Source):** Python 3.10, 3.11, 3.12 hoặc 3.13.
- **Quyền hạn:** Nên chạy dưới quyền **Administrator** để phần mềm có thể dọn dẹp các thư mục hệ thống như `C:\Windows\Temp` và tối ưu RAM triệt để.

---

## 🛠️ Cài Đặt & Chạy Từ Mã Nguồn

### 1. Clone Kho Mã Nguồn
```bash
git clone https://github.com/NDLong1601/laptop-cleaner.git
cd laptop-cleaner
```

### 2. Cài Đặt Các Gói Phụ Thuộc
Khuyến khích tạo môi trường ảo hoặc cài đặt trực tiếp bằng `pip`:
```bash
pip install -r requirements.txt
```

*Nội dung `requirements.txt`:*
```text
PyQt6>=6.6.0
PyQt6-Fluent-Widgets>=1.7.0
psutil>=5.9.0
pywin32>=306
pyinstaller>=6.0.0
send2trash>=1.8.2
```

### 3. Khởi Động Ứng Dụng
Sử dụng script sẵn có:
```cmd
run.bat
```
Hoặc qua lệnh Python:
```bash
python src/main.py
```

---

## 📦 Đóng Gói Thành File .EXE Độc Lập

Dự án đã được cấu hình sẵn file đặc tả PyInstaller `laptop_cleaner.spec` tối ưu hóa cao:
- Đóng gói dạng **One-File EXE** duy nhất (~41 MB), người dùng không cần cài đặt Python.
- Tự động nhúng icon độ phân giải cao (`assets/icon.ico` đầy đủ 7 kích cỡ từ 16px đến 256px).
- Tích hợp Windows UAC Manifest (`uac_admin=True`) để tự động yêu cầu quyền Admin.
- Tự động ẩn cửa sổ dòng lệnh đen (Console Window), biến ứng dụng thành phần mềm GUI chuyên nghiệp.
- Nhúng metadata phiên bản (`version_info.txt`) hiển thị chi tiết trong thuộc tính File Properties.

### Cách 1: Chạy Script Tự Động (Khuyên Dùng)
Chỉ cần nhấp đúp vào file `build.bat` hoặc chạy:
```cmd
build.bat
```

Script sẽ tự động:
1. Dọn dẹp bản build và cache cũ.
2. Kiểm tra môi trường PyInstaller.
3. Thực hiện build với cờ `--clean --noconfirm`.
4. Báo cáo kích thước file hoàn tất và mở thư mục `dist/`.

### Cách 2: Chạy Thủ Công Bằng Lệnh
```bash
pyinstaller laptop_cleaner.spec --clean --noconfirm
```
File thực thi cuối cùng sẽ nằm tại:
```
dist/LaptopCleaner.exe
```

---

## 📂 Cấu Trúc Dự Án

```
laptop-cleaner/
├── assets/                          # Tài nguyên đồ họa
│   ├── icon.ico                     # Icon đa kích thước (16x16 -> 256x256)
│   └── icon.png                     # Logo độ phân giải cao
├── src/                             # Mã nguồn chính
│   ├── main.py                      # Điểm khởi chạy (Entry point, UAC, High-DPI)
│   ├── config.json                  # Tệp cấu hình lưu trữ người dùng
│   ├── core/                        # Tầng xử lý logic nghiệp vụ (Backend)
│   │   ├── admin.py                 # Kiểm tra & nâng cấp đặc quyền UAC Administrator
│   │   ├── cleaner.py               # Thuật toán quét và dọn dẹp file rác
│   │   ├── ram_optimizer.py         # Tối ưu hóa bộ nhớ RAM qua Windows API
│   │   ├── folder_analyzer.py       # Phân tích thư mục, AppData và đánh giá rủi ro
│   │   ├── duplicate_finder.py      # Tìm kiếm tệp trùng lặp qua hash MD5
│   │   ├── large_files_hunter.py    # Phân loại và tìm kiếm file dung lượng lớn
│   │   ├── privacy_cleaner.py       # Xóa dấu vết hoạt động và lịch sử gần đây
│   │   ├── app_manager.py           # Quản lý & truy vấn phần mềm từ Registry
│   │   ├── process_manager.py       # Quản lý danh sách tác vụ đang chạy
│   │   ├── startup_manager.py       # Quản lý phần mềm khởi động cùng hệ thống
│   │   ├── battery_power_manager.py # Quản lý pin và chuyển đổi Power Scheme
│   │   └── scheduler_manager.py     # Lập lịch trình dọn dẹp tự động
│   └── ui/                          # Tầng giao diện người dùng (PyQt6 Fluent)
│       ├── app.py                   # Cửa sổ chính FluentWindow và thanh điều hướng
│       ├── animations.py            # Central Engine hoạt ảnh & chuyển động
│       ├── dashboard_tab.py         # Giao diện Tổng Quan (Thẻ điểm, tài nguyên)
│       ├── cleaner_tab.py           # Giao diện Dọn Rác Hệ Thống
│       ├── folder_analyzer_tab.py   # Giao diện Phân Tích AppData / Thư Mục
│       ├── duplicate_tab.py         # Giao diện Tìm Tệp Trùng Lặp
│       ├── large_files_tab.py       # Giao diện Tệp Dung Lượng Khủng
│       ├── privacy_tab.py           # Giao diện Dấu Vết Riêng Tư
│       ├── uninstaller_tab.py       # Giao diện Gỡ Ứng Dụng
│       ├── processes_tab.py         # Giao diện Tiến Trình Chạy Ngầm
│       ├── ram_tab.py               # Giao diện Tối Ưu RAM & Đồ thị sóng
│       ├── startup_tab.py           # Giao diện Khởi Động Cùng Windows
│       ├── battery_tab.py           # Giao diện Pin & Hiệu Năng
│       └── scheduler_tab.py         # Giao diện Lên Lịch Tự Động
├── .gitignore                       # Cấu hình bỏ qua cache, venv, build artifacts
├── build.bat                        # Script tự động đóng gói file EXE
├── run.bat                          # Script khởi động nhanh từ source
├── laptop_cleaner.spec              # Cấu hình PyInstaller chuyên sâu
├── requirements.txt                 # Danh sách thư viện Python cần thiết
├── version_info.txt                 # Metadata Windows Version Resource cho file EXE
└── README.md                        # Tài liệu hướng dẫn dự án
```

---

## 🛡️ Cơ Chế An Toàn Dữ Liệu

Dọn dẹp hệ thống là tác vụ nhạy cảm, vì vậy phần mềm áp dụng các nguyên tắc bảo vệ nghiêm ngặt:
1. **Sử dụng Thùng Rác (Recycle Bin):** Các thao tác xóa tệp người dùng (Tệp trùng lặp, tệp lớn, thư mục tùy chọn) được ưu tiên chuyển qua `send2trash` thay vì xóa vĩnh viễn, giúp người dùng dễ dàng khôi phục nếu lỡ tay chọn nhầm.
2. **Whitelist Hệ Thống Nghiêm Ngặt:** Bộ lọc loại trừ tự động ngăn chặn người dùng xóa các tệp tin hạt nhân của Windows, trình điều khiển (drivers), file cấu hình hệ thống quan trọng.
3. **Phân Loại Tác Động Màu Sắc:**
   - 🟢 **An toàn:** Cache, tệp log tạm, tệp tạm có thể xóa ngay mà không ảnh hưởng ứng dụng.
   - 🟡 **Cân nhắc:** Thư mục dữ liệu người dùng, cấu hình offline cần xác nhận trước khi dọn.
   - 🔴 **Ảnh hưởng môi trường:** Thư mục chứa cấu hình biến môi trường, khóa đăng ký quan trọng.
4. **Xử Lý Lỗi Ngoại Lệ (Graceful Exception Handling):** Bỏ qua mượt mà các tệp đang bị khóa bởi tiến trình khác (`PermissionError`, `FileInUse`) mà không làm treo hay gián đoạn toàn bộ quá trình quét.

---

## 🧰 Công Nghệ & Thư Viện Sử Dụng

- **Ngôn ngữ:** [Python 3](https://www.python.org/)
- **Giao diện:** [PyQt6](https://pypi.org/project/PyQt6/) kết hợp [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- **Truy vấn hệ thống & Tiến trình:** [psutil](https://pypi.org/project/psutil/)
- **Windows API & Registry:** [pywin32](https://pypi.org/project/pywin32/)
- **Thao tác rác an toàn:** [send2trash](https://pypi.org/project/Send2Trash/)
- **Đóng gói phân phối:** [PyInstaller](https://pyinstaller.org/)

---

## 👤 Tác Giả & Bản Quyền

- **Tác giả:** [NDLong1601](https://github.com/NDLong1601)
- **Kho lưu trữ:** [https://github.com/NDLong1601/laptop-cleaner](https://github.com/NDLong1601/laptop-cleaner)
- **Giấy phép:** Phân phối dưới giấy phép **MIT License**. Bạn được tự do sử dụng, chỉnh sửa và phân phối lại theo các điều khoản của giấy phép.

<div align="center">
  <sub>Được phát triển với niềm đam mê nâng cao trải nghiệm người dùng Windows. ⭐ Đừng quên tặng 1 Star nếu dự án hữu ích với bạn!</sub>
</div>
