from PySide6.QtCore import Qt, QMimeData, QPoint, Signal, QRectF, QRect
from PySide6.QtGui import QPixmap, QDrag, QPainter, QPen
from PySide6.QtWidgets import QLabel, QWidget


class WidgetObject(QLabel):

    clicked = Signal(object)

    def __init__(self, sequence_index: int, box_x: float, box_y: float, box_width: float, box_height: float):
        super().__init__()
        self._sequence_index: int = sequence_index
        self._box_x: int = int(round(box_x))
        self._box_y: int = int(round(box_y))
        self._box_width: int = int(round(box_width))
        self._box_height: int = int(round(box_height))

        self.drag: bool = False
        self._dragged: bool = False
        self.setGeometry(self._box_x, self._box_y, self._box_width, self._box_height)

    @property
    def drag(self) -> bool:
        return self._drag

    @drag.setter
    def drag(self, value):
        self._drag = value

    def mousePressEvent(self, ev):
        self.drag_offset = ev.pos()
        self.clicked.emit(self)

    def mouseMoveEvent(self, e):
        if self.drag and e.buttons() == Qt.LeftButton:
            width, height = self.width(), self.height()
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            pen = QPen(Qt.blue, 2)
            painter.setPen(pen)
            painter.drawRect(1, 1, width - 2, height - 2)
            painter.end()
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())
            drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._dragged:
            self._dragged = False

    def to_dict(self):
        res_dict = {
            "type": "",
            "sequence_index": self._sequence_index,
            "box_x": self._box_x,
            "box_y": self._box_y,
            "box_width": self._box_width,
            "box_height": self._box_height
        }
        if self.__class__.__name__ == "WidgetImage":
            res_dict['type'] = 'Image'
            res_dict['page_sequence_index'] = self.page.sequence_index
        if self.__class__.__name__ == "WidgetText":
            res_dict['type'] = 'Text'
            res_dict['page_sequence_index'] = self.page.sequence_index
        return res_dict

    def __str__(self):
       return f"{type(self).__name__}, sequence: {self._sequence_index}, geometry: {self.geometry()}, original: {self._box_x, self._box_y, self._box_width, self._box_height}"
