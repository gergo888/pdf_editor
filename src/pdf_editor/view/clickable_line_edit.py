from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, Qt


class ClickableLineEdit(QLineEdit):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
