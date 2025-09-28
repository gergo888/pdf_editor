from typing import List
from PySide6.QtWidgets import QWidget

from pdf_editor.view.widgetobjects.widget_object import WidgetObject

class WidgetPage(WidgetObject):

    def __init__(self, sequence_index, box_width, box_height):
        super().__init__(sequence_index, 0, 0, box_width, box_height)
        self.widget_object_list = []
        self.zoom = 1.0

    @property
    def widget_object_list(self) -> List[WidgetObject]:
        return self._widget_pdf_object_list

    @widget_object_list.setter
    def widget_object_list(self, value):
        self._widget_pdf_object_list = value

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        new_zoom = value
        self._zoom = new_zoom
        self.set_pdf_object_list_geometry()
        self.set_page_geometry()

    @property
    def sequence_index(self) -> int:
        return self._sequence_index

    @sequence_index.setter
    def sequence_index(self, value):
        self._sequence_index = int(value)

    @property
    def box_x(self) -> int:
        return self._box_x

    @box_x.setter
    def box_x(self, value):
        self._box_x = round(value)

    @property
    def box_y(self) -> int:
        return self._box_y

    @box_y.setter
    def box_y(self, value):
        self._box_y = round(value)

    @property
    def box_width(self):
        return self._box_width

    @box_width.setter
    def box_width(self, value):
        self._box_width = round(value)

    @property
    def box_height(self):
        return self._box_height

    @box_height.setter
    def box_height(self, value):
        self._box_height = round(value)

    def setup_widget_objects(self, parent_widget: QWidget):
        current_set = set(self.widget_object_list)
        for child in self.findChildren(QWidget):
            if isinstance(child, WidgetObject) and child not in current_set:
                child.deleteLater()
        for widget_object in self.widget_object_list:
            widget_object.setParent(self)
            widget_object.setStyleSheet("QLabel { border: 1px solid blue; }")
            widget_object.clicked.disconnect(parent_widget.request_object_update)
            widget_object.clicked.connect(parent_widget.request_object_update)
            widget_object.clicked.disconnect(parent_widget.enable_drag)
            widget_object.clicked.connect(parent_widget.enable_drag)
            widget_object.show()

    def set_scale_fit_to_width(self, available_width):
        self.zoom = available_width / self._box_width

    def set_pdf_object_list_geometry(self):
        for pdf_object in self.widget_object_list:
            new_x = pdf_object._box_x * self.zoom
            new_y = pdf_object._box_y * self.zoom
            new_width = pdf_object._box_width * self.zoom
            new_height = pdf_object._box_height * self.zoom
            pdf_object.setGeometry(new_x, new_y, new_width, new_height)

    def set_page_geometry(self):
        new_width = int(self._box_width * self.zoom)
        new_height = int(self._box_height * self.zoom)
        self.setFixedSize(new_width, new_height)

    def to_dict(self):
        return {
            "sequence_index": self._sequence_index,
            "box_x": self._box_x,
            "box_y": self._box_y,
            "box_width": self._box_width,
            "box_height": self._box_height,
            "zoom": self.zoom,
            "object_list": [obj.to_dict() for obj in self.widget_object_list]
        }