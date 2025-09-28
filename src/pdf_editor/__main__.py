import sys

from pdf_editor.model.document_model import DocumentModel
from pdf_editor.viewmodel.document_view_model import DocumentViewModel
from pdf_editor.view.mainwindow import MainWindow
from PySide6.QtWidgets import QApplication


if __name__ == "__main__":
    app = QApplication(sys.argv)
    document = DocumentModel()
    document_view_model = DocumentViewModel(document)
    mainwindow = MainWindow(document_view_model)
    mainwindow.show()
    app.exec()
