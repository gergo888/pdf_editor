import copy

from pdf_editor.model.PDFObject.pdf_object import PDFObject


class Command():
    def __init__(self, pdf_object, operation):
        self.pdf_object = pdf_object
        self.operation = operation
        self.transformation_matrix = None
        self.inverse_transformation_matrix = None
        self.deleted_instructions = None
        self.start_index = None
        self.end_index = None
        self.original_x = None
        self.original_y = None
        self.original_width = None
        self.original_height = None
        self.new_x = None
        self.new_y = None
        self.new_width = None
        self.new_height = None
        self.original_scale = None
        self.new_scale = None
        self.new_degree = None
        # self.old_pdf_object = None
        # self.new_pdf_object = None

    # def set_old_object(self, old_pdf_object: PDFObject):
    #     self.old_pdf_object = old_pdf_object.copy()
    #
    # def set_new_object(self, new_pdf_object: PDFObject):
    #     self.new_pdf_object = new_pdf_object.copy()

    def save_original_geometry(self, pdf_object):
        self.original_x = pdf_object._box_x
        self.original_y = pdf_object._box_y
        self.original_width = pdf_object._box_width
        self.original_height = pdf_object._box_height

    def save_original_size(self, pdf_object):
        self.original_width = pdf_object._box_width
        self.original_height = pdf_object._box_height

    def save_new_geometry(self, pdf_object):
        self.new_x = pdf_object._box_x
        self.new_y = pdf_object._box_y
        self.new_width = pdf_object._box_width
        self.new_height = pdf_object._box_height

    def save_delete(self, deleted_instructions, start_index, end_index):
        self.deleted_instructions = deleted_instructions
        self.start_index = start_index
        self.end_index = end_index

    def save_trasnformation(self, transformation_matrix, inverse_transformation_matrix):
        self.transformation_matrix = transformation_matrix
        self.inverse_transformation_matrix = inverse_transformation_matrix

    def copy(self):
        return copy.copy(self)
