# PhotoPro - Professional Passport Photo Desktop Studio

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-LGPLv3%20%2F%20Commercial-blue.svg)](THIRD_PARTY_LICENSES.md)
[![DPI](https://img.shields.io/badge/Resolution-300%20DPI%20Calibrated-orange.svg)]()
[![Offline](https://img.shields.io/badge/Offline-100%25%20Independent-success.svg)]()

**PhotoPro** is a professional, offline-first Windows desktop application engineered specifically for photo studios, printing shops, and copy centers. It transforms customer portraits into ISO/IEC-compliant passport and ID photos with automated AI face positioning, studio background replacement, conservative blemish retouching, and exact 300 DPI sheet layout generation for 4R and A4 photo paper.

---

## Key Features

- 🎯 **Automated Face Detection & Biometric Positioning**:
  - Automatically identifies subject facial landmarks, eye alignment, and roll tilt.
  - Automatically aligns and crops the portrait to satisfy international passport standards (crown-to-chin 70–80% portrait height).
- ✂️ **Studio-Grade Background Removal**:
  - Local ONNX neural network execution (`u2netp.onnx`) without any external cloud APIs.
  - Advanced inward morphological choke (1px erosion) and bilateral edge anti-aliasing to eliminate halos.
  - Instant one-click backdrops: **Studio White**, **Passport Blue** (`#1F6FB2`), **Light Grey** (`#E5E7EB`), **Original**, or **Custom Color**.
- 🌟 **Intelligent Portrait Retouching**:
  - Conservative blemish and pimple reduction that preserves natural skin pores and identity (never plastic or artificial).
  - Adaptive exposure compensation for underexposed faces with highlight protection.
  - 1st-to-99th percentile contrast stretching and natural skin tone balancing.
  - Precision unsharp mask sharpening for crisp eyes, hair, and clothing.
- 🖨️ **Exact 300 DPI Sheet Layout**:
  - Supports **4R (6×4 in / 152.4×101.6 mm)** and **A4 (210×297 mm)** photo paper.
  - Mathematical grid calculation with centered margins and spacing.
  - Built-in 1px cutting guidelines and 3mm corner tick marks for rotary trimmers and scissors.
- 📦 **Batch Photo Queue**:
  - Process multiple customer photos in sequence with asynchronous background threads and real-time progress bars.
- 💾 **Local SQLite Persistence**:
  - Stores shop settings, hardware acceleration preferences, and complete print history with auto-recovery on file corruption.
- 📄 **Direct Printing & Vector PDF Export**:
  - Native Windows `QPrinter` spooling ensuring 1:1 physical millimeter dimensions.
  - Export to 300 DPI JPEG (with JFIF metadata), lossless PNG, or print-ready PDF.

---

## Quick Start (Development)

### 1. Prerequisites
- Windows 10/11 (64-bit) or Linux / macOS
- Python 3.10+

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run PhotoPro Desktop
```bash
python run_desktop.py
```

---

## Building the Windows Installer (`PhotoPro Setup.exe`)

PhotoPro comes with automated scripts to package a standalone Windows distribution:

### Option A: One-Click Build Script
On a Windows machine with Inno Setup 6 installed:
```cmd
build_windows.bat
```

### Option B: Manual Build
1. Compile standalone executable with PyInstaller:
   ```cmd
   pyinstaller --clean photopro.spec
   ```
2. Open `installer\photopro.iss` in **Inno Setup Compiler** and click **Build**.
3. Your installer will be ready in `dist_installer\PhotoPro Setup.exe`.

---

## Running Tests

PhotoPro includes automated unit tests covering geometry calculations, database auto-repair, capacity limits, and pipeline logic:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## Physical Specifications

| Format | Dimensions (mm) | 300 DPI Resolution (px) | Max Capacity (4R) | Max Capacity (A4) |
| :--- | :--- | :--- | :--- | :--- |
| **Passport Photo** | 35.0 × 45.0 mm | 413 × 531 px | 8 photos | 30 photos |
| **Smaller Photo** | 30.0 × 40.0 mm | 354 × 472 px | 10 photos | 42 photos |
| **4R Paper** | 152.4 × 101.6 mm | 1800 × 1200 px | — | — |
| **A4 Paper** | 210.0 × 297.0 mm | 2480 × 3508 px | — | — |

---

## License & Software Attribution

All third-party libraries (PySide6, OpenCV, NumPy, Pillow, ONNX Runtime, U-2-Net, Inno Setup) and their respective licenses are documented in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
