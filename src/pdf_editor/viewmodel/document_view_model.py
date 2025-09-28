from typing import List

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QPixmap

from pdf_editor.model.PDFObject.pdf_image import PDFImage
from pdf_editor.model.PDFObject.pdf_object import PDFObject
from pdf_editor.model.PDFObject.pdf_page import PDFPage
from pdf_editor.model.PDFObject.pdf_text import PDFText
from pdf_editor.model.command import Command
from pdf_editor.model.document_model import DocumentModel
from pdf_editor.model.operation import Operation


class DocumentViewModel(QObject):

    content_changed = Signal(object)

    def __init__(self, document):
        super().__init__()
        self._document: DocumentModel = document
        self.dict_pages_list: List[dict] = []
        self._command_list: List[Command] = []
        self._command_index: int = None

    def open_document(self, path):
        self._document.create_pages_and_objects(path)
        dict_pages_list = []
        for pdf_page in self._document.pdf_pages:
            dict_pages_list.append(pdf_page.to_dict())
        self.dict_pages_list = dict_pages_list

    def get_scaled_pixmap_for_page(self, pdf_page: PDFPage) -> QPixmap:
        pixmap = self._document.get_qpixmap(pdf_page._box_width, pdf_page._box_height, 0, 0, pdf_page)
        return pixmap

    def get_scaled_pixmap_for_dict_page(self, dict_page: dict) -> QPixmap:
        pdf_page = self._getpdf_page(dict_page)
        pixmap = self._document.get_qpixmap(pdf_page._box_width, pdf_page._box_height, 0, 0, pdf_page)
        return pixmap

    def _getpdf_page(self, page_dict: dict) -> PDFPage:
        res_pdf_page = None
        for pdf_page in self._document.pdf_pages:
            if pdf_page.sequence_index == page_dict['sequence_index']:
                res_pdf_page = pdf_page
        return res_pdf_page

    def _getpdf_object(self, object_dict: dict) -> PDFObject:
        res_pdf_object = None
        for pdf_page in self._document.pdf_pages:
            if pdf_page.sequence_index == object_dict['page_sequence_index']:
                for pdf_object in pdf_page.pdf_object_list:
                    if (pdf_object.sequence_index == object_dict['sequence_index'] and isinstance(pdf_object, PDFText)
                            and object_dict['type'] == 'Text'):
                        res_pdf_object = pdf_object
                    if (pdf_object.sequence_index == object_dict['sequence_index'] and isinstance(pdf_object, PDFImage)
                            and object_dict['type'] == 'Image'):
                        res_pdf_object = pdf_object
        return res_pdf_object

    def aplly_update(self, pdf_object: PDFObject, res_command: Command):
        dict_pages_list = []
        for pdf_page in self._document.pdf_pages:
            dict_pages_list.append(pdf_page.to_dict())
        self.dict_pages_list = dict_pages_list
        if self._command_index != len(self._command_list) - 1:
            self._command_list = []
        self._command_list.append(res_command)
        self._command_index = len(self._command_list) - 1
        self.content_changed.emit(pdf_object.pdf_page.to_dict())

    def object_translate(self, dict_object: dict, new_x: int, new_y: int):
        pdf_object = self._getpdf_object(dict_object)
        command = Command(pdf_object, Operation.translate)
        command.new_x = new_x
        command.new_y = new_y
        if self._command_index != len(self._command_list) - 1:
            self._command_list = []
        res_command = self._document.update_content(command)
        self.aplly_update(pdf_object, res_command)

    def object_rotate(self, dict_object: dict, new_degree: int):
        pdf_object = self._getpdf_object(dict_object)
        command = Command(pdf_object, Operation.rotate)
        command.new_degree = new_degree
        res_command = self._document.update_content(command)
        self.aplly_update(pdf_object, res_command)

    def object_scale(self, dict_object: dict, new_scale: float):
        pdf_object = self._getpdf_object(dict_object)
        command = Command(pdf_object, Operation.scale)
        command.new_scale = new_scale
        res_command = self._document.update_content(command)
        self.aplly_update(pdf_object, res_command)

    def object_delete(self, dict_object: dict):
        pdf_object = self._getpdf_object(dict_object)
        command = Command(pdf_object, Operation.delete)
        res_command = self._document.update_content(command)
        self.aplly_update(pdf_object, res_command)

    def undo(self):
        self.undo_redo(Operation.undo)

    def redo(self):
        self.undo_redo(Operation.redo)

    def apply_undo_redo(self, pdf_object: PDFObject):
        dict_pages_list = []
        for pdf_page in self._document.pdf_pages:
            dict_pages_list.append(pdf_page.to_dict())
        self.dict_pages_list = dict_pages_list
        dict_page = self.dict_pages_list[pdf_object.pdf_page.sequence_index]
        self.content_changed.emit(dict_page)

    def undo_redo(self, operation: Operation):
        if len(self._command_list) > 0:  # undo, redo
            if operation == Operation.undo and self._command_index >= 0:
                command = self._command_list[self._command_index]
                self._command_index -= 1
                pdf_object = command.pdf_object
                undo_command = command.copy()
                if command.operation == Operation.translate:
                    undo_command.operation = Operation.undo_translate
                    self._document.update_content(undo_command)
                if command.operation == Operation.rotate:
                    undo_command.operation = Operation.undo_rotate
                    self._document.update_content(undo_command)
                if command.operation == Operation.scale:
                    undo_command.operation = Operation.undo_scale
                    self._document.update_content(undo_command)
                if command.operation == Operation.delete:
                    undo_command.operation = Operation.undo_delete
                    self._document.update_content(undo_command)
                self.apply_undo_redo(pdf_object)
            elif operation == Operation.redo:
                if self._command_index < len(self._command_list) - 1:
                    self._command_index += 1
                    command = self._command_list[self._command_index]
                    pdf_object = command.pdf_object
                    redo_command = command.copy()
                    if command.operation == Operation.translate:
                        redo_command.operation = Operation.redo_translate
                        self._document.update_content(redo_command)
                    if command.operation == Operation.rotate:
                        redo_command.operation = Operation.redo_rotate
                        self._document.update_content(redo_command)
                    if command.operation == Operation.scale:
                        redo_command.operation = Operation.redo_scale
                        self._document.update_content(redo_command)
                    if command.operation == Operation.delete:
                        redo_command.operation = Operation.redo_delete
                        self._document.update_content(redo_command)
                    self.apply_undo_redo(pdf_object)

    def save(self):
        self._document.save_file()

    def close(self):
        self._document.close()


