# PhotoPro Architecture & Engineering Blueprint

## 1. Architecture Evaluation & Decision

### Comparison of Evaluated Architectures

| Metric | Option A: Python + PySide6 (Qt 6) | Option B: Tauri 2 + Rust + Python Sidecar |
| :--- | :--- | :--- |
| **Idle Memory Footprint** | **~85 MB – 140 MB** | ~180 MB – 260 MB (Webview + Rust + Python subprocess) |
| **Active Processing RAM** | **~150 MB – 320 MB** | ~350 MB – 550 MB |
| **Cold Startup Time** | **< 0.9 seconds** | ~1.4 – 2.0 seconds |
| **Image Processing Speed** | **Direct C/C++ memory bindings** (NumPy, OpenCV, ONNX Runtime) | IPC serialization overhead (sending image buffers between Rust and Python sidecar) |
| **Printing & DPI Accuracy** | **Native `QPrinter` with exact 300 DPI physical hardware mapping** | Browser Webview print spooler (often applies unrequested "fit to printable area" margins) |
| **Offline Reliability** | **100% self-contained binary** | Multiple processes requiring IPC synchronization |
| **Windows Packaging** | **Standard PyInstaller + Inno Setup** | Multi-toolchain (Cargo, Rustc, MSVC, PyInstaller sidecar, NSIS/WiX) |
| **Code Maintainability** | **Single unified Python 3 codebase** | Triple-stack complexity (HTML/JS + Rust + Python) |

### Final Architecture Decision: Option A (Python + PySide6)

Option A was selected as the superior architecture for PhotoPro because:
1. **Zero Serialization Overhead**: Image arrays (`np.ndarray`) reside in native memory and pass directly between OpenCV, ONNX Runtime, and PySide6 `QImage` without JSON/Base64 or IPC socket conversions.
2. **True 300 DPI Hardware Spooling**: Photo and printing shops require millimeter-exact cuts (35×45 mm). Qt's `QPrinter` interacts directly with the Windows GDI/Print Spooler at `HighResolution` (300 DPI) with zero margins, eliminating driver distortion.
3. **Low Resource Footprint**: Runs comfortably on 4GB RAM budget shop computers running Windows 10/11 without exhausting system resources.
4. **Single-Binary Installation**: Bundled via PyInstaller and wrapped with an Inno Setup installer into a single `PhotoPro Setup.exe`.

---

## 2. System Pipeline & Data Flow

```
+-------------------+
| Customer Photo    |  (JPEG, PNG, WEBP, BMP)
+---------+---------+
          |
          v
+-------------------+
| Face Detection    |  OpenCV Haar / YuNet / Eye Landmark Extraction
| & Auto Positioning|  Detects bounding box, eye centers, head roll tilt
+---------+---------+
          |
          v
+-------------------+
| Biometric Crop    |  ISO/IEC 19794-5 Compliance
| & 300 DPI Scaling |  Crown-to-chin 70-80% height, centered on eye axis
+---------+---------+
          |
          v
+-------------------+
| Portrait Enhance  |  - Skin probability mask (YCbCr locus)
| & Retouching      |  - Conservative blemish & pimple reduction
|                   |  - Adaptive facial exposure lift (highlight protected)
|                   |  - Color grading & contrast stretch (1st-99th percentile)
|                   |  - Unsharp mask detail enhancement
+---------+---------+
          |
          v
+-------------------+
| AI BG Removal     |  ONNX Runtime (u2netp / RMBG)
| & Studio Backdrop |  - Inward morphological choke (1px erosion)
|                   |  - Defringing: samples interior foreground to eliminate wall halo
|                   |  - Compositing onto White (#FFF), Blue (#1F6FB2), or Grey (#E5E7EB)
+---------+---------+
          |
          +---------------------------------------+
          |                                       |
          v                                       v
+-------------------+                   +-------------------+
| 300 DPI Sheet     |                   | Single Photo      |
| Generation        |                   | Export            |
| (4R or A4 Grid)   |                   | (JPG / PNG)       |
+---------+---------+                   +-------------------+
          |
    +-----+-----+
    |           |
    v           v
+-------+   +-------+
| Print |   | PDF   |
| (Q    |   | 300   |
| Print)|   | DPI   |
+-------+   +-------+
```

---

## 3. Physical Calibration Standards

- **Resolution**: 300 DPI (11.811 pixels per millimeter)
- **Paper Formats**:
  - **4R (6×4 in)**: 152.4 × 101.6 mm -> `1800 × 1200 px`
  - **A4**: 210.0 × 297.0 mm -> `2480 × 3508 px`
- **Passport Formats**:
  - **Standard Passport**: 35.0 × 45.0 mm -> `413 × 531 px`
  - **Smaller Photo**: 30.0 × 40.0 mm -> `354 × 472 px`
- **Cutting Guides**:
  - 1px light neutral line (`#D4D4D8`) around each tile
  - 3.0 mm corner tick marks for guillotine and rotary paper trimmers

---

## 4. Local Persistence & Resiliency

PhotoPro uses a local SQLite database (`photopro.db`):
- `settings`: Operator preferences, default paper/photo sizes, retouch strength.
- `print_history`: Audit trail of all print and export jobs.
- `background_presets`: Studio backdrop colors.

**Corruption Auto-Recovery**:
If `photopro.db` is ever corrupted (e.g. abrupt power failure in the shop), `DatabaseManager` automatically renames the corrupt file to `.corrupt_<timestamp>` and re-initializes a clean, fully-functioning schema without crashing.
