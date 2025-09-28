from io import BytesIO
from typing import List

import pikepdf
from PIL.ImageDraw import ImageDraw
from PySide6.QtGui import QPixmap
from pdf2image import convert_from_bytes

from pdf_editor.model.PDFObject.pdf_page import PDFPage
from pdf_editor.model.PDFObject.pdf_image import PDFImage
from pdf_editor.model.PDFObject.pdf_object import PDFObject
from pdf_editor.model.PDFObject.pdf_text import PDFText
from pdf_editor.model.operation import Operation
from pdf_editor.model.command import Command

import fitz
import io
import math


class DocumentModel:

    def __init__(self):
        self._pike_pdf_file: pikepdf.Pdf = None
        self.pdf_pages: List[PDFPage] = []

    def create_pages_and_objects(self, path):
        try:
            if self._pike_pdf_file is not None:
                self.close()
                self.pdf_pages = []
            self._pike_pdf_file = pikepdf.open(path, allow_overwriting_input=True)
            self._extract_pages()
            self._extract_objects()
        except pikepdf.PdfError as e:
            raise ValueError("Érvénytelen vagy sérült PDF fájl.") from e

    def _extract_pages(self):
        for sequence, pdf_page in enumerate(self._pike_pdf_file.pages):
            x1, y1, x2, y2 = pdf_page['/MediaBox']
            width = x2 - x1
            height = y2 - y1
            page = PDFPage(sequence, width, height)
            self.pdf_pages.append(page)

    def _extract_objects(self, page_sequence_index = None):
        if page_sequence_index is None:
            pdf_page_list = self.pdf_pages
        else:
            pdf_page_list = [self.pdf_pages[page_sequence_index]]
        for pdf_page in pdf_page_list:
            pike_page = self._pike_pdf_file.pages[pdf_page.sequence_index]
            instructions_list = pikepdf.parse_content_stream(pike_page)
            graphical_state = False
            instruction_index = 0
            text_sequence = 0
            image_sequence = 0
            page_height = pike_page['/MediaBox'][3]
            user_CTM = pikepdf.Matrix()
            font_type = None
            for instruction in instructions_list:
                operands, operator = instruction
                if operator == pikepdf.Operator('q'):
                    graphical_state = True
                    saved_user_CTM = user_CTM
                if operator == pikepdf.Operator('Q'):
                    graphical_state = False
                    user_CTM = saved_user_CTM
                if graphical_state and operator != pikepdf.Operator('q'):
                    if operator == pikepdf.Operator('cm'):
                        cm = pikepdf.Matrix(operands)
                        user_CTM = cm @ user_CTM
                if operator == pikepdf.Operator('BT'):
                    TM = pikepdf.Matrix()
                    text_state_parameters = {
                        'charSpace': 0,
                        'wordSpace': 0,
                        'scale': 100,
                        'leading': 0,
                        'font_size': None,
                        'render': 0,
                        'rise': 0,
                    }
                if operator == pikepdf.Operator('Tm'):
                    explicit_tm = pikepdf.Matrix(operands)
                    TM = TM @ explicit_tm
                if operator == pikepdf.Operator('Td'):
                    text_offset_x = operands[0]
                    text_offset_y = operands[1]
                    TLM = pikepdf.Matrix(1, 0, 0, 1, text_offset_x, text_offset_y)
                    TM = TLM @ TM
                if operator == pikepdf.Operator('Tc'):
                    text_state_parameters['charSpace'] = operands[0]
                if operator == pikepdf.Operator('Tw'):
                    text_state_parameters['wordSpace'] = operands[0]
                if operator == pikepdf.Operator('Tz'):
                    text_state_parameters['scale'] = operands[0] # / 100
                if operator == pikepdf.Operator('TL'):
                    text_state_parameters['leading'] = operands[0]
                if operator == pikepdf.Operator('Tf'):
                    text_state_parameters['font_size'] = operands[1]
                if operator == pikepdf.Operator('Tr'):
                    text_state_parameters['render'] = operands[0]
                if operator == pikepdf.Operator('Ts'):
                    text_state_parameters['rise'] = operands[0]
                if operator == pikepdf.Operator('Tf'):
                    font_type = operands[0]
                if operator == pikepdf.Operator('TJ'):
                    fonts = pike_page['/Resources']['/Font']
                    text_array_object = operands
                    x, y, w, h = self._get_text_geometry(TM, text_state_parameters, fonts, font_type, text_array_object, page_height)
                    text = PDFText(text_sequence, x, y, w, h, pdf_page)
                    pdf_page.pdf_object_list.append(text)
                    text_sequence += 1
                if operator == pikepdf.Operator('ET'):
                    TM = pikepdf.Matrix()
                if operator == pikepdf.Operator('Do'):
                    x, y, w, h = self._get_image_geometry(user_CTM, page_height)
                    image = PDFImage(image_sequence, x, y, w, h, pdf_page)
                    pdf_page.pdf_object_list.append(image)
                    image_sequence += 1
                instruction_index += 1

    def get_qpixmap(self, box_width, box_height, box_x, box_y, page: PDFPage, scale=None) -> QPixmap:
        if scale is None:
            scale = page.scale
        zoom_matrix = fitz.Matrix(scale, scale)
        top_left = box_x, box_y
        bottom_right = box_x + box_width, box_y + box_height
        clip = fitz.Rect(top_left, bottom_right)
        output_stream = io.BytesIO()
        self._pike_pdf_file.save(output_stream)
        output_bytes = output_stream.getvalue()
        fitz_doc = fitz.open(stream=output_bytes)
        fitz_page = fitz_doc[page.sequence_index]
        pix = fitz_page.get_pixmap(matrix=zoom_matrix, clip=clip)
        pix_byte_stream = io.BytesIO(pix.tobytes(output="png"))
        qpixmap = QPixmap()
        qpixmap.loadFromData(pix_byte_stream.getvalue(), "PNG")
        return qpixmap

    def update_content(self, command: Command):
        pdf_object: PDFObject = command.pdf_object
        new_instructions = None
        if command.operation in (Operation.scale, Operation.rotate, Operation.translate):
            command.save_original_geometry(pdf_object)
            if isinstance(pdf_object, PDFText):
                new_instructions, transformation_matrix, inverse_transformation_matrix = self._transform_text(pdf_object, command.operation, command.new_x, command.new_y, command.new_scale, command.new_degree)
            if isinstance(pdf_object, PDFImage):
                new_instructions, transformation_matrix, inverse_transformation_matrix = self._transform_image(pdf_object, command.operation, command.new_x, command.new_y, command.new_scale, command.new_degree)
            command.save_new_geometry(pdf_object)
            command.save_trasnformation(transformation_matrix, inverse_transformation_matrix)
        if command.operation in (Operation.undo_translate, Operation.undo_rotate, Operation.undo_scale):
            if isinstance(pdf_object, PDFText):
                new_instructions = self._apply_transformation_matrix_text(pdf_object, command.inverse_transformation_matrix)
                pdf_object.box_x = command.original_x
                pdf_object.box_y = command.original_y
                pdf_object.box_width = command.original_width
                pdf_object.box_height = command.original_height
            if isinstance(pdf_object, PDFImage):
                new_instructions = self._apply_transformation_matrix_image(pdf_object, command.inverse_transformation_matrix)
                pdf_object.box_x = command.original_x
                pdf_object.box_y = command.original_y
                pdf_object.box_width = command.original_width
                pdf_object.box_height = command.original_height
        if command.operation in (Operation.redo_translate, Operation.redo_rotate, Operation.redo_scale):
            if isinstance(pdf_object, PDFText):
                new_instructions = self._apply_transformation_matrix_text(pdf_object, command.transformation_matrix)
                pdf_object.box_x = command.new_x
                pdf_object.box_y = command.new_y
                pdf_object.box_width = command.new_width
                pdf_object.box_height = command.new_height
            if isinstance(pdf_object, PDFImage):
                new_instructions = self._apply_transformation_matrix_image(pdf_object, command.transformation_matrix)
                pdf_object.box_x = command.new_x
                pdf_object.box_y = command.new_y
                pdf_object.box_width = command.new_width
                pdf_object.box_height = command.new_height
        if command.operation == Operation.delete:
            command.save_original_geometry(pdf_object)
            if isinstance(pdf_object, PDFText):
                new_instructions, deleted_instructions, start_index, end_index = self._delete_text(pdf_object)
            if isinstance(pdf_object, PDFImage):
                new_instructions, deleted_instructions, start_index, end_index = self._delete_image(pdf_object)
            page:PDFObject = pdf_object.pdf_page
            page.remove_pdf_object(pdf_object)
            command.save_delete(deleted_instructions, start_index, end_index)
        if command.operation == Operation.undo_delete:
            page: PDFPage = pdf_object.pdf_page
            page.add_pdf_object(pdf_object)
            if isinstance(pdf_object, PDFText):
                new_instructions = self._undo_delete_text(pdf_object, command.deleted_instructions, command.start_index, command.end_index)
            if isinstance(pdf_object, PDFImage):
                new_instructions = self._undo_delete_image(pdf_object, command.deleted_instructions, command.start_index, command.end_index)
        if command.operation == Operation.redo_delete:
            if isinstance(pdf_object, PDFText):
                new_instructions, deleted_instructions, start_index, end_index = self._delete_text(pdf_object)
            if isinstance(pdf_object, PDFImage):
                new_instructions, deleted_instructions, start_index, end_index = self._delete_image(pdf_object)
            page: PDFPage = pdf_object.pdf_page
            page.remove_pdf_object(pdf_object)
        if new_instructions is not None:
            new_content_stream = pikepdf.unparse_content_stream(new_instructions)
            self._pike_pdf_file.pages[pdf_object.pdf_page.sequence_index].Contents = self._pike_pdf_file.make_stream(new_content_stream)
        return command

    def _delete_text(self, text: PDFText):
        pike_page = self._pike_pdf_file.pages[text.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(pike_page)
        new_instruction_list = pikepdf.parse_content_stream(pike_page)
        deleted_instruction_list = []
        instruction_index = 0
        text_sequence = 0
        start_index = end_index = -1
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('TJ'):
                if text_sequence == text.sequence_index:
                    start_index = instruction_index
                    end_index = instruction_index + 1
                    deleted_instruction_list = [instruction]
                    del (new_instruction_list[instruction_index])
                text_sequence += 1
            instruction_index += 1
        return new_instruction_list, deleted_instruction_list, start_index, end_index

    def _undo_delete_text(self, text: PDFText, deleted_instruction_list, start_index, end_index):
        pike_page = self._pike_pdf_file.pages[text.pdf_page.sequence_index]
        new_instruction_list = pikepdf.parse_content_stream(pike_page)
        new_instruction_list[start_index:start_index] = deleted_instruction_list
        return new_instruction_list

    def _delete_image(self, image: PDFImage):
        page = self._pike_pdf_file.pages[image.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(page)
        new_instruction_list = pikepdf.parse_content_stream(page)
        deleted_instruction_list = []
        instruction_index = 0
        image_sequence = 0
        start_index = end_index = -1
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('Do'):
                if image_sequence == image.sequence_index:
                    start_index = instruction_index
                    end_index = instruction_index + 1
                    deleted_instruction_list = [instruction]
                    del (new_instruction_list[instruction_index])
                image_sequence += 1
            instruction_index += 1
        return new_instruction_list, deleted_instruction_list, start_index, end_index

    def _undo_delete_image(self, image: PDFImage, deleted_instruction_list, start_index, end_index):
        pike_page = self._pike_pdf_file.pages[image.pdf_page.sequence_index]
        new_instruction_list = pikepdf.parse_content_stream(pike_page)
        new_instruction_list[start_index:start_index] = deleted_instruction_list
        return new_instruction_list

    def _translate_matrix(self, matrix, x, y):
        angle_rad = math.atan2(matrix.b, matrix.a)
        angle_deg = math.degrees(angle_rad)
        dX = x / matrix.a
        dY = y / matrix.d
        rotate_to_zero = pikepdf.Matrix().rotated(-angle_deg)
        translate = pikepdf.Matrix().translated(dX, dY)
        rotate_back = pikepdf.Matrix().rotated(angle_deg)
        res_transformation_matrix = rotate_back @ translate @ rotate_to_zero
        translated_text_matrix = res_transformation_matrix @ matrix
        return translated_text_matrix, res_transformation_matrix

    def _transform_text(self, text: PDFText, operation: Operation, new_x:int=None, new_y:int=None, new_scale:float=None, degree:float=None):
        page = self._pike_pdf_file.pages[text.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(page)
        new_instruction_list = pikepdf.parse_content_stream(page)
        transformation_matrix = None
        inverse_transformation_matrix= None
        instruction_index = 0
        text_sequence = 0
        tm_index = 0
        if operation == Operation.translate:
            dx = new_x / text.pdf_page.scale - text._box_x
            dy = text._box_y - new_y / text.pdf_page.scale
            text._box_x = text._box_x + dx
            text._box_y = text._box_y - dy
        if operation == Operation.scale:
            offset = text._box_height * (new_scale - 1)
            text._box_y -= offset
            text._box_width = text._box_width * new_scale
            text._box_height = text._box_height * new_scale
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('Tm'):
                TM = pikepdf.Matrix(operands)
                tm_index = instruction_index
            if operator == pikepdf.Operator('TJ'):
                if text_sequence == text.sequence_index:
                    if operation == Operation.translate:
                        new_tm, transformation_matrix = self._translate_matrix(TM, dx, dy)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_tm_instruction = ([new_tm.a, new_tm.b, new_tm.c, new_tm.d, new_tm.e, new_tm.f], pikepdf.Operator('Tm'))
                        new_instruction_list[tm_index] = new_tm_instruction
                    if operation == Operation.scale:
                        transformation_matrix = pikepdf.Matrix().scaled(new_scale, new_scale)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_tm = transformation_matrix @ TM
                        new_tm_instruction = ([new_tm.a, new_tm.b, new_tm.c, new_tm.d, new_tm.e, new_tm.f], pikepdf.Operator('Tm'))
                        new_instruction_list[tm_index] = new_tm_instruction
                    if operation == Operation.rotate:
                        transformation_matrix = pikepdf.Matrix().rotated(degree)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_tm = transformation_matrix @ TM
                        new_tm_instruction = ([new_tm.a, new_tm.b, new_tm.c, new_tm.d, new_tm.e, new_tm.f], pikepdf.Operator('Tm'))
                        new_instruction_list[tm_index] = new_tm_instruction
                text_sequence += 1
            instruction_index += 1
        return new_instruction_list, transformation_matrix, inverse_transformation_matrix

    def _apply_transformation_matrix_text(self, text: PDFText, transformation_matrix):
        page = self._pike_pdf_file.pages[text.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(page)
        new_instruction_list = pikepdf.parse_content_stream(page)
        instruction_index = 0
        text_sequence = 0
        tm_index = 0
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('Tm'):
                TM = pikepdf.Matrix(operands)
                tm_index = instruction_index
            if operator == pikepdf.Operator('TJ'):
                if text_sequence == text.sequence_index:
                    new_tm = transformation_matrix @ TM
                    new_tm_instruction = ([new_tm.a, new_tm.b, new_tm.c, new_tm.d, new_tm.e, new_tm.f], pikepdf.Operator('Tm'))
                    new_instruction_list[tm_index] = new_tm_instruction
                text_sequence += 1
            instruction_index += 1
        return new_instruction_list

    def _transform_image(self, image: PDFImage, operation: Operation, new_x:int=None, new_y:int=None, new_scale:float=None, degree:float=None):
        pike_page = self._pike_pdf_file.pages[image.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(pike_page)
        new_instruction_list = pikepdf.parse_content_stream(pike_page)
        transformation_matrix = None
        inverse_transformation_matrix= None
        instruction_index = 0
        image_sequence = 0
        cm_index = 0
        re_index = 0
        if operation == Operation.translate:
            dx = new_x / image.pdf_page.scale - image._box_x
            dy = image._box_y - new_y / image.pdf_page.scale
            image._box_x = image._box_x + dx
            image._box_y = image._box_y - dy
        if operation == Operation.scale:
            offset = image._box_height * (new_scale - 1)
            image._box_y -= offset
            image._box_width = image._box_width * new_scale
            image._box_height = image._box_height * new_scale
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('cm'):
                cm = pikepdf.Matrix(operands)
                cm_index = instruction_index
            if operator == pikepdf.Operator('re'):
                re = pikepdf.Rectangle(operands[0], operands[1], operands[2], operands[3])
                re_index = instruction_index
            if operator == pikepdf.Operator('Do'):
                if image_sequence == image.sequence_index:
                    if operation == Operation.translate:
                        rectangle = pikepdf.Rectangle(0, 0, image.pdf_page._box_width, image.pdf_page._box_height)
                        new_re_operands = [rectangle.llx, rectangle.lly, rectangle.urx, rectangle.ury]
                        new_re_instruction = (new_re_operands, pikepdf.Operator('re'))
                        new_instruction_list[re_index] = new_re_instruction
                        new_cm, transformation_matrix = self._translate_matrix(cm, dx, dy)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_cm_instruction = ([new_cm.a, new_cm.b, new_cm.c, new_cm.d, new_cm.e, new_cm.f], pikepdf.Operator('cm'))
                        new_instruction_list[cm_index] = new_cm_instruction
                    if operation == Operation.scale:
                        rectangle = pikepdf.Rectangle(0, 0, image.pdf_page._box_width, image.pdf_page._box_height)
                        new_re_operands = [rectangle.llx, rectangle.lly, rectangle.urx, rectangle.ury]
                        new_re_instruction = (new_re_operands, pikepdf.Operator('re'))
                        new_instruction_list[re_index] = new_re_instruction
                        transformation_matrix = pikepdf.Matrix().scaled(new_scale, new_scale)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_cm = transformation_matrix @ cm
                        new_cm_instruction = ([new_cm.a, new_cm.b, new_cm.c, new_cm.d, new_cm.e, new_cm.f], pikepdf.Operator('cm'))
                        new_instruction_list[cm_index] = new_cm_instruction
                    if operation == Operation.rotate:
                        rectangle = pikepdf.Rectangle(0, 0, image.pdf_page._box_width, image.pdf_page._box_height)
                        new_re_operands = [rectangle.llx, rectangle.lly, rectangle.urx,rectangle.ury]
                        new_re_instruction = (new_re_operands, pikepdf.Operator('re'))
                        new_instruction_list[re_index] = new_re_instruction
                        transformation_matrix = pikepdf.Matrix().rotated(degree)
                        inverse_transformation_matrix = transformation_matrix.inverse()
                        new_cm = transformation_matrix @ cm
                        new_cm_instruction = ([new_cm.a, new_cm.b, new_cm.c, new_cm.d, new_cm.e, new_cm.f], pikepdf.Operator('cm'))
                        new_instruction_list[cm_index] = new_cm_instruction
                image_sequence += 1
            instruction_index += 1
        return new_instruction_list, transformation_matrix, inverse_transformation_matrix

    def _apply_transformation_matrix_image(self, image: PDFImage, transformation_matrix):
        pike_page = self._pike_pdf_file.pages[image.pdf_page.sequence_index]
        old_instruction_list = pikepdf.parse_content_stream(pike_page)
        new_instruction_list = pikepdf.parse_content_stream(pike_page)
        instruction_index = 0
        image_sequence = 0
        cm_index = 0
        re_index = 0
        for instruction in old_instruction_list:
            operands, operator = instruction
            if operator == pikepdf.Operator('cm'):
                cm = pikepdf.Matrix(operands)
                cm_index = instruction_index
            if operator == pikepdf.Operator('re'):
                # re = pikepdf.Rectangle(operands[0], operands[1], operands[2], operands[3])
                re_index = instruction_index
            if operator == pikepdf.Operator('Do'):
                if image_sequence == image.sequence_index:
                    rectangle = pikepdf.Rectangle(0, 0, image.pdf_page._box_width, image.pdf_page._box_height)
                    new_re_operands = [rectangle.llx, rectangle.lly, rectangle.urx, rectangle.ury]
                    new_re_instruction = (new_re_operands, pikepdf.Operator('re'))
                    new_instruction_list[re_index] = new_re_instruction
                    new_cm = transformation_matrix @ cm
                    new_cm_instruction = (
                    [new_cm.a, new_cm.b, new_cm.c, new_cm.d, new_cm.e, new_cm.f], pikepdf.Operator('cm'))
                    new_instruction_list[cm_index] = new_cm_instruction
                image_sequence += 1
            instruction_index += 1
        return new_instruction_list

    def _get_image_geometry(self, user_CTM, page_height):
        DTM = pikepdf.Matrix(1, 0, 0, -1, 0, (float(-page_height) + user_CTM.d) / user_CTM.d)
        device_result_matrix = DTM @ user_CTM
        x = device_result_matrix.e
        y = -1 * device_result_matrix.f
        width = (device_result_matrix.a ** 2 + device_result_matrix.b ** 2) ** 0.5
        height = (device_result_matrix.c ** 2 + device_result_matrix.d ** 2) ** 0.5
        angle_rad = math.atan2(device_result_matrix.b, device_result_matrix.a)
        angle_deg = math.degrees(angle_rad)
        box_width = int(height * math.sin(angle_deg)) + int(width * math.cos(angle_deg))
        box_height = int(height * math.cos(angle_deg)) + int(width * math.sin(angle_deg))
        box_x = x * (width / box_width)
        box_y = y * (height / box_height)
        return box_x, box_y, box_width, box_height

    def _get_text_geometry(self, TM, user_CTM, text_state_parameters, font_descritor, font_type, text_array_object, page_height):
        text_str = ""
        user_space_width = 0
        horizontal_scaling = 1
        font_size = text_state_parameters['font_size']
        for obj in text_array_object[0]:
            if isinstance(obj, str):
                native_value = obj
                text_str += native_value
            elif isinstance(obj, (int, float)):
                native_value = obj
            else:
                native_value = str(obj)
                text_str += native_value

            if isinstance(native_value, str):
                for char in native_value:
                    unicode_value = ord(char)
                    font = font_descritor[font_type]
                    first_char = font['/FirstChar']
                    widths_array = font['/Widths']
                    index_in_widths = unicode_value - first_char
                    if 0 <= index_in_widths < len(widths_array):
                        glyph_width = widths_array[index_in_widths]
                    else:
                        glyph_width = 0
                    user_space_width += (glyph_width * font_size / 1000) * horizontal_scaling
            elif isinstance(native_value, (int, float)):
                # print('adjustment', native_value)
                adjustment = native_value * font_size / 1000
                user_space_width -= adjustment
        height = text_state_parameters['font_size'] * TM.d
        x = TM.e
        y =  page_height - (TM.f + (font_size * TM.d))
        width = user_space_width * TM.a
        angle_rad = math.atan2(TM.b, TM.a)
        angle_deg = math.degrees(angle_rad)
        box_width = int(height * math.sin(angle_deg)) + int(width * math.cos(angle_deg))
        box_height = int(height * math.cos(angle_deg)) + int(width * math.sin(angle_deg))
        box_x = x
        box_y = y
        return box_x, box_y, box_width, box_height

    def get_cid_width(self, cid_font, cid):
        w_array = cid_font.get("/W", [])
        i = 0
        while i < len(w_array):
            current = w_array[i]
            next_item = w_array[i + 1]
            if isinstance(next_item, pikepdf.Array):
                start = current
                widths = next_item
                end = start + len(widths)
                if start <= cid < end:
                    return widths[cid - start]
                i += 2
            elif (
                    isinstance(next_item, int) and
                    isinstance(w_array[i + 2], int)
            ):
                start = current
                end = w_array[i + 1]
                width = w_array[i + 2]
                if start <= cid <= end:
                    return width
                i += 3
        return cid_font.get("/DW", 1000)

    def get_cids_from_text_object(self, obj):
        if isinstance(obj, pikepdf.Object):
            obj_bytes = bytes(obj)
        elif isinstance(obj, str):
            obj_bytes = obj.encode("latin1", errors="ignore")
        elif isinstance(obj, bytes):
            obj_bytes = obj
        else:
            return []
        cids = []
        for i in range(0, len(obj_bytes), 2):
            cid = int.from_bytes(obj_bytes[i:i + 2], byteorder='big')
            cids.append(cid)
        return cids

    def _get_text_geometry(self, TM, text_state_parameters, fonts, font_type, text_array_object, page_height):
        text_str = ""
        user_space_width = 0.0
        horizontal_scaling = 1.0
        font_size = float(text_state_parameters['font_size'])
        font = fonts[font_type]
        if font.get('/Subtype') == '/Type0':
            descendants = font.get("/DescendantFonts", [])
        for obj in text_array_object[0]:
            native_value = obj
            if isinstance(obj, (int, float)):
                native_value = obj
            else:
                if font.get('/Subtype') == '/TrueType':
                    native_value = str(obj)
                    text_str += native_value
                    for char in native_value:
                        unicode_value = ord(char)
                        font = fonts[font_type]
                        first_char = font['/FirstChar']
                        widths_array = font['/Widths']
                        index_in_widths = unicode_value - first_char
                        if 0 <= index_in_widths < len(widths_array):
                            glyph_width = widths_array[index_in_widths]
                        else:
                            glyph_width = 0
                        user_space_width += (glyph_width * font_size / 1000) * horizontal_scaling
                if font.get('/Subtype') == '/Type0' and descendants[0].get('/CIDToGIDMap') == '/Identity':
                    cids = self.get_cids_from_text_object(obj)
                    for cid in cids:
                        glyph_width = self.get_cid_width(descendants[0], cid)
                        user_space_width += (glyph_width * font_size / 1000) * horizontal_scaling
            if isinstance(native_value, (int, float)):
                adjustment = native_value * font_size / 1000
                user_space_width -= adjustment
        height = float(text_state_parameters['font_size']) * TM.d
        x = TM.e
        y =  float(page_height) - (TM.f + (font_size * TM.d))
        width = user_space_width * TM.a
        angle_rad = math.atan2(TM.b, TM.a)
        angle_deg = math.degrees(angle_rad)
        box_width = int(height * math.sin(angle_deg)) + int(width * math.cos(angle_deg))
        box_height = int(height * math.cos(angle_deg)) + int(width * math.sin(angle_deg))
        box_x = x
        box_y = y
        return box_x, box_y, box_width, box_height

    def save_file(self):
        self._pike_pdf_file.save()

    def close(self):
        self._pike_pdf_file.close()
