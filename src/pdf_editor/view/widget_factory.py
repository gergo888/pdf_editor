from typing import List
from pdf_editor.view.widgetobjects.widget_image import WidgetImage
from pdf_editor.view.widgetobjects.widget_page import WidgetPage
from pdf_editor.view.widgetobjects.widget_text import WidgetText


class WidgetFactory:

    @staticmethod
    def create_widget_page_list_from_dict(dict_pages: List[dict]):
        widget_page_list = []
        for dict_page in dict_pages:
            widget_page = WidgetPage(dict_page['sequence_index'], dict_page['box_width'], dict_page['box_height'])
            widget_page.widget_object_list = WidgetFactory.create_widget_object_list_from_dict(widget_page, dict_page)
            widget_page_list.append(widget_page)
        return widget_page_list

    @staticmethod
    def create_widget_object_list_from_dict(widget_page: WidgetPage, dict_page: dict):
        widget_object_list = []
        for dict_obj in dict_page['object_list']:
            if dict_obj['type'] == 'Text':
                widget_text = WidgetText(dict_obj['sequence_index'], dict_obj['box_x'], dict_obj['box_y'],
                                         dict_obj['box_width'], dict_obj['box_height'], widget_page)
                widget_object_list.append(widget_text)
            if dict_obj['type'] == 'Image':
                widget_image = WidgetImage(dict_obj['sequence_index'], dict_obj['box_x'], dict_obj['box_y'],
                                           dict_obj['box_width'], dict_obj['box_height'], widget_page)
                widget_object_list.append(widget_image)
        return widget_object_list