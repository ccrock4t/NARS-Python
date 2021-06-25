"""
    Author: Christian Hahm
    Created: December 24, 2020
"""

import NARSGUI
import NALGrammar


class Global:
    """
        NARS vars
    """
    NARS = None  # variable to hold NARS instance
    paused = True

    """
        Terms
    """
    TERM_SELF = NALGrammar.Terms.Term.from_string("self")
    TERM_IMAGE_PLACEHOLDER = NALGrammar.Terms.Term.from_string("_")

    """
        ID markers
    """
    MARKER_ITEM_ID = "ItemID:"  # there are Sentence IDs and Bag Item IDs
    MARKER_SENTENCE_ID = "SentenceID:"
    MARKER_ID_END = ":ID "

    """
        GUI
    """
    gui_use_internal_data = True
    gui_use_interface = True
    NARS_object_pipe = None
    NARS_string_pipe = None

    @classmethod
    def get_current_cycle_number(cls):
        return cls.NARS.memory.current_cycle_number

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        data_structure_name = None
        data_structure_len = 0
        if data_structure is not None: data_structure_name = (str(data_structure), type(data_structure).__name__)
        if data_structure is not None: data_structure_len = len(data_structure)
        cls.NARS_string_pipe.send(("print", msg, data_structure_name,data_structure_len))

    @classmethod
    def clear_output_gui(cls, data_structure=None):
        cls.NARS_string_pipe.send(("clear", "", type(data_structure).__name__,0))

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from an output GUI box
        """
        cls.NARS_string_pipe.send(("remove", msg, (str(data_structure), type(data_structure).__name__),len(data_structure)))

    @classmethod
    def set_paused(cls, paused):
        """
            Set global paused variable and GUI
        """
        cls.paused = paused
        cls.NARS_string_pipe.send(("paused", paused, "guibox",0))


