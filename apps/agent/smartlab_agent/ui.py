"""Small optional PySide6 shell; the client is intentionally headless-capable."""
import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from .config import AgentConfig
from .monitor import Monitor


class AgentWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SmartLab Agent")
        self.setMinimumSize(420, 260)
        config, identity = AgentConfig.load(), Monitor().system_identity()
        body, layout = QWidget(), QVBoxLayout()
        layout.addWidget(QLabel(f"<h2>{identity['name']}</h2>"))
        layout.addWidget(QLabel(f"Device ID: {config.device_id}"))
        layout.addWidget(QLabel(f"Server: {config.server_url}"))
        layout.addWidget(QLabel("The monitoring service runs independently of this window."))
        body.setLayout(layout)
        self.setCentralWidget(body)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AgentWindow()
    window.show()
    sys.exit(app.exec())

