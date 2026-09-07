#!/usr/bin/env python3
"""
PhotoPro Windows Desktop Application Entry Point
Initializes PySide6 application, sets high-DPI scaling policies,
loads models, and presents the main photo studio window.
"""
import sys
import os
import logging

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PhotoPro")

def main():
    # Ensure current working directory is application root
    app_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_root)
    sys.path.insert(0, app_root)

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
    except ImportError:
        logger.error(
            "PySide6 is not installed. To run PhotoPro Desktop, install requirements:\n"
            "pip install -r requirements.txt"
        )
        sys.exit(1)

    # Windows High-DPI Scaling configuration
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PhotoPro")
    app.setApplicationDisplayName("PhotoPro - Professional Passport Photo Studio")
    app.setOrganizationName("PhotoPro")

    # Locate model path
    model_path = os.path.join(app_root, "u2netp.onnx")
    if not os.path.exists(model_path):
        logger.warning(f"u2netp.onnx not found at {model_path}. Using fallback segmentation.")

    from app.ui.main_window import MainWindow
    window = MainWindow(model_path=model_path)
    window.show()

    logger.info("PhotoPro Desktop UI started successfully.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
