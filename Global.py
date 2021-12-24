"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
import Config
import NALGrammar.Terms

class Global:
    """
        NARS vars
    """
    NARS = None  # variable to hold NARS instance
    paused = False

    """
        Terms
    """
    TERM_SELF = None
    TERM_IMAGE_PLACEHOLDER = None

    """
        ID markers
    """
    MARKER_ITEM_ID = "ItemID:"  # there are Sentence IDs and Bag Item IDs
    MARKER_SENTENCE_ID = "SentenceID:"
    MARKER_ID_END = ":ID "

    """
        GUI
    """
    NARS_object_pipe = None
    NARS_string_pipe = None

    @classmethod
    def get_current_cycle_number(cls):
        return cls.NARS.memory.current_cycle_number

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        try:
            data_structure_name = None
            data_structure_len = 0
            if data_structure is None: print(msg)
            if not(data_structure is cls.NARS.memory.concepts_bag or
                   data_structure is cls.NARS.temporal_module or
                   data_structure is cls.NARS.global_buffer or
                   data_structure is None): return # must be a valid data structure
            if data_structure is not None:
                data_structure_name = (str(data_structure), type(data_structure).__name__)
                data_structure_len = len(data_structure)
            if Config.GUI_USE_INTERFACE: cls.NARS_string_pipe.send(("print", msg, data_structure_name, data_structure_len))
        except:
            print(msg)

    @classmethod
    def clear_output_gui(cls, data_structure=None):
        cls.NARS_string_pipe.send(("clear", "", type(data_structure).__name__,0))

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from an output GUI box
        """
        if cls.NARS_string_pipe is None: return
        if not(data_structure is cls.NARS.memory.concepts_bag or
               data_structure is cls.NARS.temporal_module or
               data_structure is cls.NARS.global_buffer): return
        cls.NARS_string_pipe.send(("remove", msg, (str(data_structure), type(data_structure).__name__),len(data_structure)))

    @classmethod
    def set_paused(cls, paused):
        """
            Set global paused variable and GUI
        """
        cls.paused = paused
        if Config.GUI_USE_INTERFACE: cls.NARS_string_pipe.send(("paused", paused, "guibox", 0))


    @classmethod
    def debug_print(cls,msg):
        if msg is None: return
        print(str(cls.get_current_cycle_number()) + ": gb(" + str(len(cls.NARS.global_buffer)) + "): " + msg)

    @classmethod
    def create_inherent_terms(cls):
        cls.TERM_SELF = NALGrammar.Terms.from_string("{SELF}")
        cls.TERM_IMAGE_PLACEHOLDER = NALGrammar.Terms.from_string("_")

Global.create_inherent_terms()