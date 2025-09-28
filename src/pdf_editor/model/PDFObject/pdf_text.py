from pdf_editor.model.PDFObject.pdf_page import PDFPage
from pdf_editor.model.PDFObject.pdf_object import PDFObject

class PDFText(PDFObject):

    def __init__(self, sequence_index, box_x, box_y, box_width, box_height, pdf_page: PDFPage):
        super().__init__(sequence_index, box_x, box_y, box_width, box_height)
        self.pdf_page: PDFPage = pdf_page

    def to_dict(self):
        return {
            "type": "Text",
            "sequence_index": self.sequence_index,
            "box_x": self.box_x,
            "box_y": self.box_y,
            "box_width": self.box_width,
            "box_height": self.box_height
        }

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self.pdf_page == other.pdf_page

    def __hash__(self):
        return hash((super().__hash__(), self.pdf_page))
