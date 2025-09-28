from typing import List

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy, QToolButton, QMessageBox
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QPalette, QColor
from pathlib import Path


from pdf_editor.view.clickable_line_edit import ClickableLineEdit
from pdf_editor.view.widget_factory import WidgetFactory
from pdf_editor.viewmodel.document_view_model import DocumentViewModel
from pdf_editor.view.widgetobjects.widget_page import WidgetPage

class PageArea(QWidget):

    scrolled = Signal(int)
    dropped = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.widget_page_list: List[WidgetPage] = []

        self.document_view_model: DocumentViewModel = None
        self.page_top: List = []
        self.scrolled_page_number: int = 1
        self.current_zoom:float = 1

        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setAcceptDrops(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("lightgray"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.create_actions()
        self.create_button_area()
        self.create_content_area()
        self.connect_slots()

    @staticmethod
    def get_icon_path(file_name):
        base_path = Path.cwd()
        full_path = base_path.joinpath("pdf_editor", "view", "icons", file_name)
        return str(full_path)

    def create_button_area(self):
        self.button_area = QWidget()
        self.button_area.setFixedHeight(40)
        self.button_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button_layout = QHBoxLayout(self.button_area)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        self.main_layout.addWidget(self.button_area)

        zoom_in_button = QToolButton()
        zoom_in_button.setDefaultAction(self.action_zoom_in)
        zoom_out_button = QToolButton()
        zoom_out_button.setDefaultAction(self.action_zoom_out)
        fit_to_width_button = QToolButton()
        fit_to_width_button.setDefaultAction(self.action_fit_to_width)
        original_width_button = QToolButton()
        original_width_button.setDefaultAction(self.action_original_width)

        last_page_button = QToolButton()
        last_page_button.setDefaultAction(self.action_last_page)
        self.page_number_input = ClickableLineEdit()
        self.page_number_input.setFixedWidth(40)
        self.page_number_input.setAlignment(Qt.AlignCenter)
        self.page_number_input.returnPressed.connect(self.to_page)
        self.page_number_input.clicked.connect(self.clear_page_number_input)

        next_page_button = QToolButton()
        next_page_button.setDefaultAction(self.action_next_page)

        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 0, 0, 0)
        left_layout.setSpacing(5)
        left_layout.addWidget(zoom_in_button)
        left_layout.addWidget(zoom_out_button)
        left_layout.addWidget(fit_to_width_button)
        left_layout.addWidget(original_width_button)
        left_layout.addStretch()

        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 20, 0)
        right_layout.setSpacing(5)
        right_layout.addStretch()
        right_layout.addWidget(last_page_button)
        right_layout.addWidget(self.page_number_input)
        right_layout.addWidget(next_page_button)

        self.button_layout.addWidget(left_widget, alignment=Qt.AlignLeft)
        self.button_layout.addStretch()
        self.button_layout.addWidget(right_widget, alignment=Qt.AlignRight)

    def create_content_area(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.scroll_contents.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_contents)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def create_actions(self):
        self.action_zoom_in = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-zoom-in-100.png"))
        self.action_zoom_in.setIcon(icon)
        self.action_zoom_in.setText("Nagyítás")

        self.action_zoom_out = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-zoom-out-100.png"))
        self.action_zoom_out.setIcon(icon)
        self.action_zoom_out.setText("Kicsinyítés")

        self.action_fit_to_width = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-width-100.png"))
        self.action_fit_to_width.setIcon(icon)
        self.action_fit_to_width.setText("Ilesztés")

        self.action_original_width = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-page-size-100.png"))
        self.action_original_width.setIcon(icon)
        self.action_original_width.setText("Eredeti méret")

        self.action_last_page = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-up-100.png"))
        self.action_last_page.setIcon(icon)
        self.action_last_page.setText("Előző")

        self.action_next_page = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-down-100.png"))
        self.action_next_page.setIcon(icon)
        self.action_next_page.setText("Következő")

    def connect_slots(self):
        self.action_zoom_in.triggered.connect(self.btn_zoom_in)
        self.action_zoom_out.triggered.connect(self.btn_zoom_out)
        self.action_fit_to_width.triggered.connect(self.btn_fit_to_width)
        self.action_original_width.triggered.connect(self.btn_original_size)

        self.action_last_page.triggered.connect(self.btn_last)
        self.action_next_page.triggered.connect(self.btn_next)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.show_page_number)

    def show_document(self, document_view_model: DocumentViewModel) -> None:
        self.document_view_model = document_view_model
        pdf_pages = self.document_view_model._document.pdf_pages
        self.page_number_input.setText("1")
        spacing = self.scroll_layout.spacing()
        top = spacing
        self.page_top = []
        dict_pages_list = document_view_model.dict_pages_list
        self.widget_page_list = WidgetFactory.create_widget_page_list_from_dict(dict_pages_list)
        for widget_page in self.widget_page_list:
            widget_page.setup_widget_objects(self.parent())
            pdf_page = pdf_pages[widget_page.sequence_index]
            pixmap = document_view_model.get_scaled_pixmap_for_page(pdf_page)
            widget_page.setPixmap(pixmap)
            self.scroll_layout.addWidget(widget_page)
            self.page_top.append(top)
            top += spacing + widget_page.height()

    @Slot(object)
    def refresh_page(self, dict_page: dict):
        res_widget_page = self.widget_page_list[dict_page['sequence_index']]
        res_widget_page.clear()
        pixmap = self.document_view_model.get_scaled_pixmap_for_dict_page(dict_page)
        res_widget_page.setPixmap(pixmap)
        res_widget_page.widget_object_list = WidgetFactory.create_widget_object_list_from_dict(res_widget_page, dict_page)
        res_widget_page.setup_widget_objects(self.parent())
        res_widget_page.set_pdf_object_list_geometry()

    def remove_document(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.page_top = []
        self.page_number_input.clear()

    def update_page_top(self):
        spacing = self.scroll_layout.spacing()
        top = spacing
        self.page_top = []
        for page in self.widget_page_list:
            self.page_top.append(top)
            top += spacing + page.height()

    def dragEnterEvent(self, event):
        widget_object = event.source()
        if widget_object.drag and not isinstance(widget_object, WidgetPage):
            event.setDropAction(Qt.MoveAction)
            event.accept()

    def dropEvent(self, event):
        widget_object = event.source()
        if widget_object.drag and not isinstance(widget_object, WidgetPage):
            global_pos = event.position().toPoint()
            page = widget_object.parent()
            local_pos = page.mapFrom(self, global_pos)
            corrected_pos = local_pos - widget_object.drag_offset
            widget_object.move(corrected_pos)
            widget_object.raise_()
            widget_object.drag = False
            page = widget_object.parent()
            self.dropped.emit(widget_object)

    @Slot()
    def show_page_number(self, position):
        self.scrolled_page_number = 1
        for i, top in enumerate(self.page_top):
            if position < top:
                break
            self.scrolled_page_number = i + 1
            self.page_number_input.setText(str(self.scrolled_page_number))

    @Slot()
    def to_page(self):
        try:
            text_value = self.page_number_input.text()
            if not text_value.isdigit():
                raise ValueError("Az oldalszámnak pozitív egész számnak kell lennie.")
            page_num = int(text_value)
            if not (1 <= page_num <= len(self.page_top)):
                raise ValueError(f"Az oldalszámnak 1 és {len(self.page_top)} között kell lennie.")
            scroll_bar = self.scroll_area.verticalScrollBar()
            target_position = self.page_top[page_num - 1]
            scroll_bar.setValue(target_position)

        except ValueError as e:
            QMessageBox.critical(self, "Hiba", str(e), QMessageBox.Ok)

    @Slot()
    def clear_page_number_input(self):
        self.page_number_input.clear()

    @Slot()
    def btn_next(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        if self.scrolled_page_number < len(self.page_top):
            self.scrolled_page_number += 1
            target_position = self.page_top[self.scrolled_page_number - 1]
            scroll_bar.setValue(target_position)

    @Slot()
    def btn_last(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        if self.scrolled_page_number > 1:
            self.scrolled_page_number -= 1
            target_position = self.page_top[self.scrolled_page_number - 1]
            scroll_bar.setValue(target_position)

    def set_pages_zoom(self, zoom):
        for act_widget_page in self.widget_page_list:
            act_widget_page.zoom = zoom
            self.refresh_page_image(act_widget_page)

    @Slot()
    def btn_zoom_in(self):
        self.current_zoom = self.current_zoom * 1.1
        self.set_pages_zoom(self.current_zoom)

    @Slot()
    def btn_zoom_out(self):
        if self.current_zoom * 0.9 >= 1:
            self.current_zoom = self.current_zoom * 0.9
            self.set_pages_zoom(self.current_zoom)

    @Slot()
    def btn_original_size(self):
        self.set_pages_zoom(1)

    @Slot()
    def btn_fit_to_width(self):
        available_width = self.scroll_area.viewport().width()
        for widget_page in self.widget_page_list:
            widget_page.set_scale_fit_to_width(available_width)
            self.refresh_page_image(widget_page)

    def refresh_page_image(self, widget_page: WidgetPage):
        pdf_page = self.document_view_model._document.pdf_pages[widget_page.sequence_index]
        zoom = widget_page.zoom
        pdf_page.scale = zoom
        pixmap = self.document_view_model.get_scaled_pixmap_for_page(pdf_page)
        widget_page.setPixmap(pixmap)
        self.update_page_top()
