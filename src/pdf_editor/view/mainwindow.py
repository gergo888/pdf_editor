from PySide6.QtWidgets import QMainWindow, QToolBar, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QIcon, QGuiApplication
from pathlib import Path

from pdf_editor.view.widgetobjects.widget_object import WidgetObject
from pdf_editor.view.pagearea import PageArea
from pdf_editor.view.widgetobjects.widget_page import WidgetPage
from pdf_editor.viewmodel.document_view_model import DocumentViewModel


class MainWindow(QMainWindow):

    def __init__(self, document_view_model):
        super().__init__()
        self.document_view_model: DocumentViewModel = document_view_model
        self._selected_button: int = None

        self.setWindowTitle("PDF szerkesztő")
        self.setGeometry(100, 100, 1024, 768)
        self.create_actions()
        self.create_menubar()
        self.top_toolbar = self.create_top_toolbar()
        self.addToolBar(self.top_toolbar)
        self.operations_toolbar = self.create_operations_toolbar()
        self.addToolBar(Qt.RightToolBarArea, self.operations_toolbar)
        self.page_area = PageArea(self)
        self.setCentralWidget(self.page_area)
        self.connect_slots()

    @staticmethod
    def get_icon_path(file_name):
        base_path = Path.cwd()
        full_path = base_path.joinpath("pdf_editor", "view", "icons", file_name)
        return str(full_path)

    def create_actions(self):
        self.action_show_top_toolbar = QAction(self)
        self.action_show_top_toolbar.setCheckable(True)
        self.action_show_top_toolbar.setChecked(True)
        self.action_show_top_toolbar.setText("Műveletek eszköztár")

        self.action_show_operations_toolbar = QAction(self)
        self.action_show_operations_toolbar.setCheckable(True)
        self.action_show_operations_toolbar.setChecked(True)
        self.action_show_operations_toolbar.setText("Módosítás eszköztár")

        self.action_about = QAction("Névjegy", self)

        self.action_open = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-opened-folder-100.png"))
        self.action_open.setIcon(icon)
        self.action_open.setText("Megnyitás")

        self.action_save = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-save-100.png"))
        self.action_save.setIcon(icon)
        self.action_save.setText("Mentés")

        self.action_undo = QAction()
        icon = QIcon(self.get_icon_path("icons8-undo-100.png"))
        self.action_undo.setIcon(icon)
        self.action_undo.setText("Visszavonás")

        self.action_redo = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-redo-100.png"))
        self.action_redo.setIcon(icon)
        self.action_redo.setText("Újra")

        self.action_object_delete = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-close-100-4.png"))
        self.action_object_delete.setIcon(icon)
        self.action_object_delete.setText("Törlés")

        self.action_object_move = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-drag-100.png"))
        self.action_object_move.setIcon(icon)
        self.action_object_move.setText("Mozgatás")

        self.action_object_rotate = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-rotate-100.png"))
        self.action_object_rotate.setIcon(icon)
        self.action_object_rotate.setText("Forgatás")

        self.action_object_scale = QAction(self)
        icon = QIcon(self.get_icon_path("icons8-zoom-to-extents-100.png"))
        self.action_object_scale.setIcon(icon)
        self.action_object_scale.setText("Nagyítás")

    def create_menubar(self):
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("Fájl")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        edit_menu = self.menu_bar.addMenu("Szerkesztés")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        view_menu = self.menu_bar.addMenu("Nézet")
        view_menu.addAction(self.action_show_top_toolbar)
        view_menu.addAction(self.action_show_operations_toolbar)
        about_menu = self.menu_bar.addMenu("Névjegy")
        about_menu.addAction(self.action_about)

    def create_top_toolbar(self):
        toolbar = QToolBar("Fájl műveletek eszköztár")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)
        return toolbar

    def create_operations_toolbar(self):
        toolbar = QToolBar("Módosítás eszköztár")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.addAction(self.action_object_move)
        toolbar.addAction(self.action_object_delete)
        toolbar.addAction(self.action_object_rotate)
        toolbar.addAction(self.action_object_scale)
        return toolbar

    def connect_slots(self):
        self.action_open.triggered.connect(self.open_document)
        self.action_save.triggered.connect(self.save_document)
        self.action_undo.triggered.connect(self.undo)
        self.action_redo.triggered.connect(self.redo)

        self.action_object_move.triggered.connect(self.move_cursor)
        self.action_object_delete.triggered.connect(self.delete_cursor)
        self.action_object_rotate.triggered.connect(self.rotate_cursor)
        self.action_object_scale.triggered.connect(self.scale_cursor)

        self.action_about.triggered.connect(self.show_about)
        self.action_show_top_toolbar.triggered.connect(self.show_top_toolbar)
        self.action_show_operations_toolbar.triggered.connect(self.show_operations_toolbar)

        self.document_view_model.content_changed.connect(self.page_area.refresh_page)
        self.page_area.dropped.connect(self.request_object_translate)

    @Slot()
    def show_top_toolbar(self, res):
        if res:
            self.top_toolbar.show()
        else:
            self.top_toolbar.hide()

    @Slot()
    def show_operations_toolbar(self, res):
        if res:
            self.operations_toolbar.show()
        else:
            self.operations_toolbar.hide()

    @Slot()
    def show_about(self):
        about_message = QMessageBox(self)
        about_message.setWindowTitle("Névjegy")
        about_message.setText("<b>PDF Szerkesztő</b><br><br>"
                              "Készítette: Szabó Gergely<br>"
                              "Neptun: C3BOW2<br><br>"
                              "Az ikonok származása: <a href='https://icons8.com/'>Icons8</a>")
        about_message.setIcon(QMessageBox.Information)
        about_message.setStandardButtons(QMessageBox.Ok)
        about_message.exec()

    @Slot()
    def open_document(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("PDF fájlok (*.pdf)")  # Csak PDF
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                if self.document_view_model._document.pdf_pages != 0:
                    self.page_area.remove_document()
                file_path = selected_files[0]
                try:
                    if self.document_view_model._document.pdf_pages != 0:
                        self.page_area.remove_document()
                    self.document_view_model.open_document(file_path)
                    self.page_area.show_document(self.document_view_model)
                except ValueError as e:
                    QMessageBox.critical(
                        self,
                        "Hibás fájl",
                        str(e)
                    )
                # self.document_view_model.open_document(file_path)
                # self.page_area.show_document(self.document_view_model)

    @Slot(object)
    def enable_drag(self, pdf_object: WidgetObject):
        if self._selected_button == 1 and not isinstance(pdf_object, WidgetPage):
            pdf_object.drag = True

    @Slot(object)
    def request_object_update(self, widget_pdf_object: WidgetObject):
        if not isinstance(widget_pdf_object, WidgetPage):
            object_dict = widget_pdf_object.to_dict()
            if self._selected_button == 2:
                self.document_view_model.object_delete(object_dict)
            elif self._selected_button == 3:
                self.document_view_model.object_rotate(object_dict, 45)
            elif self._selected_button == 4:
                new_scale = 1.1
                self.document_view_model.object_scale(object_dict, new_scale)

    @Slot(object)
    def request_object_translate(self, widget_object: WidgetObject):
        if self._selected_button == 1:
            object_dict = widget_object.to_dict()
            new_x = widget_object.geometry().x()
            new_y = widget_object.geometry().y()
            self.document_view_model.object_translate(object_dict, new_x, new_y)

    @Slot()
    def save_document(self):
        self.document_view_model.save()

    @Slot()
    def move_cursor(self):
        if self._selected_button != 1 or self._selected_button == None:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.SizeAllCursor)
            self._selected_button = 1
        elif self._selected_button == 1:
            QGuiApplication.restoreOverrideCursor()
            self._selected_button = None

    @Slot()
    def delete_cursor(self):
        if self._selected_button != 2 or self._selected_button == None:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
            self._selected_button = 2
        elif self._selected_button == 2:
            QGuiApplication.restoreOverrideCursor()
            self._selected_button = None

    @Slot()
    def rotate_cursor(self):
        if self._selected_button != 3 or self._selected_button == None:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
            self._selected_button = 3
        elif self._selected_button == 3:
            QGuiApplication.restoreOverrideCursor()
            self._selected_button = None

    @Slot()
    def scale_cursor(self):
        if self._selected_button != 4 or self._selected_button == None:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.CrossCursor)
            self._selected_button = 4
        elif self._selected_button == 4:
            QGuiApplication.restoreOverrideCursor()
            self._selected_button = None

    @Slot()
    def undo(self):
        self.document_view_model.undo()

    @Slot()
    def redo(self):
        self.document_view_model.redo()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Mentés szükséges?",
            "Szeretné menteni a dokumentumot, mielőtt bezárja?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Yes:
            self.document_view_model.save()
            self.document_view_model.close()
            event.accept()
        elif reply == QMessageBox.No:
            self.document_view_model.close()
            event.accept()
        else:
            event.ignore()