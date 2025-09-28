from pdf_editor.model.PDFObject.pdf_object import PDFObject
from typing import List


class PDFPage(PDFObject):

    def __init__(self, sequence_index, box_width, box_height):
        super().__init__(sequence_index, 0, 0, box_width, box_height)
        self.pdf_object_list: List[PDFObject] = []

    def add_pdf_object(self, new_pdf_object: PDFObject):
        new_type = type(new_pdf_object)
        new_sequence = new_pdf_object.sequence_index
        for obj in self.pdf_object_list:
            if isinstance(obj, new_type) and obj.sequence_index >= new_sequence:
                obj.sequence_index += 1
        self.pdf_object_list.append(new_pdf_object)

    def remove_pdf_object(self, delete_pdf_object: PDFObject):
        delete_pdf_object_type = type(delete_pdf_object)
        delete_pdf_object_sequence = delete_pdf_object.sequence_index
        for pdf_obj in self.pdf_object_list:
            if pdf_obj == delete_pdf_object:
                self.pdf_object_list.remove(pdf_obj)
                break
        for obj in self.pdf_object_list:
            if isinstance(obj, delete_pdf_object_type) and obj.sequence_index > delete_pdf_object_sequence:
                obj.sequence_index -= 1

    def to_dict(self):
        return {
            "sequence_index": self.sequence_index,
            "box_x": self.box_x,
            "box_y": self.box_y,
            "box_width": self.box_width,
            "box_height": self.box_height,
            "scale": self.scale,
            "object_list": [obj.to_dict() for obj in self.pdf_object_list]
        }

