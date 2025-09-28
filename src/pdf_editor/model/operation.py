from enum import Enum

class Operation(Enum):
    translate = 1
    rotate = 2
    scale = 3
    delete = 4
    undo_translate = 5
    undo_rotate = 6
    undo_scale = 7
    redo_translate = 8
    redo_rotate = 9
    redo_scale = 10
    undo_delete = 11
    redo_delete = 12
    undo = 13
    redo = 14