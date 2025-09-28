import copy
from abc import ABC, abstractmethod


class PDFObject(ABC):

    def __init__(self, sequence_index, box_x, box_y, box_width, box_height):
        super().__init__()
        self.sequence_index = sequence_index
        self.scale = 1.0
        self.box_x = box_x
        self.box_y = box_y
        self.box_width = box_width
        self.box_height = box_height

    @property
    def sequence_index(self):
        return self._sequence_index

    @sequence_index.setter
    def sequence_index(self, value):
        self._sequence_index = int(value)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = float(value)

    @property
    def box_x(self):
        return self._box_x

    @box_x.setter
    def box_x(self, value):
        self._box_x = float(value)

    @property
    def box_y(self):
        return self._box_y

    @box_y.setter
    def box_y(self, value):
        self._box_y = float(value)

    @property
    def box_width(self):
        return self._box_width

    @box_width.setter
    def box_width(self, value):
        self._box_width = float(value)

    @property
    def box_height(self):
        return self._box_height

    @box_height.setter
    def box_height(self, value):
        self._box_height = float(value)

    def copy(self):
        return copy.deepcopy(self)

    @abstractmethod
    def to_dict(self):
        pass

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.sequence_index == other.sequence_index

    def __hash__(self):
        return hash((type(self), self.sequence_index))

    def __str__(self):
        return (f"{type(self).__name__}, sequence: {self.sequence_index}, "
                f"original: {(self.box_x, self.box_y, self.box_width, self.box_height)}, "
                f"scale: {self.scale}")