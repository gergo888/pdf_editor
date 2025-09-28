from pdf_editor.view.widgetobjects.widget_page import WidgetPage
from pdf_editor.view.widgetobjects.widget_object import WidgetObject


class WidgetText(WidgetObject):

    def __init__(self, sequence_index, box_x: float, box_y: float, box_width: float, box_height: float, page: WidgetPage):
        super().__init__(sequence_index, box_x, box_y, box_width, box_height)
        self.page = page

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
    def box_width(self) -> int:
        return self._box_width

    @box_width.setter
    def box_width(self, value):
        self._box_width = round(value)

    @property
    def box_height(self) -> int:
        return self._box_height

    @box_height.setter
    def box_height(self, value):
        self._box_height = round(value)
