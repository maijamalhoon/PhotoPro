"""
PhotoPro Windows Desktop UI Theme Stylesheet (QSS)
Clean, professional, high-contrast light theme with precision spacing and native controls.
"""

WINDOWS_STYLE = """
/* Global Window & Typography */
QMainWindow, QDialog {
    background-color: #F4F3F0;
    font-family: "Segoe UI", -apple-system, sans-serif;
    font-size: 13px;
    color: #18181B;
}

QWidget {
    outline: none;
}

/* Sidebar Navigation */
QFrame#sidebarFrame {
    background-color: #FFFFFF;
    border-right: 1px solid #E4E4E7;
    min-width: 180px;
    max-width: 220px;
}

QPushButton.navBtn {
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #52525B;
    background-color: transparent;
}
QPushButton.navBtn:hover {
    background-color: #F4F4F5;
    color: #18181B;
}
QPushButton.navBtn:checked, QPushButton.navBtn.active {
    background-color: #EFF6FF;
    color: #2563EB;
    font-weight: 600;
}

/* Panels & Cards */
QFrame.panelCard {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 8px;
    padding: 14px;
}

/* Section Headings */
QLabel.sectionHeader {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #71717A;
    margin-bottom: 6px;
}

/* Push Buttons */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 6px 14px;
    color: #18181B;
    font-weight: 500;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #F9F9FB;
    border-color: #D4D4D8;
}
QPushButton:pressed {
    background-color: #E4E4E7;
}

/* Primary Action Buttons */
QPushButton.primaryBtn {
    background-color: #2563EB;
    border: 1px solid #1D4ED8;
    color: #FFFFFF;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
}
QPushButton.primaryBtn:hover {
    background-color: #1D4ED8;
}
QPushButton.primaryBtn:pressed {
    background-color: #1E40AF;
}
QPushButton.primaryBtn:disabled {
    background-color: #93C5FD;
    border-color: #BFDBFE;
    color: #EFF6FF;
}

/* Option Chips (e.g. Paper sizes, Color buttons) */
QPushButton.chipBtn {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
    color: #27272A;
}
QPushButton.chipBtn:hover {
    background-color: #F4F4F5;
    border-color: #D4D4D8;
}
QPushButton.chipBtn:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #E4E4E7;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: #2563EB;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #2563EB;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: #EFF6FF;
    border-color: #1D4ED8;
}

/* Line Edits & Spin Boxes */
QLineEdit, QSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #E4E4E7;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
    color: #18181B;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: #2563EB;
}

/* Status Bar */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E4E4E7;
    font-size: 12px;
    color: #52525B;
    padding: 4px 8px;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #D4D4D8;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #A1A1AA;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
