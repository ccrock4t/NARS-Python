"""
    Author: Christian Hahm
    Created: December 24, 2020
"""

import NARSGUI

class Global:
    """
        NARS vars
    """
    NARS = None  # variable to hold NARS instance
    paused = True
    ITEM_ID_MARKER = "ItemID:"  # there are Sentence IDs and Bag Item IDs
    SENTENCE_ID_MARKER = "SentenceID:"
    ID_END_MARKER = ":ID "

    # thread ready boolean
    thread_ready_gui = False
    thread_ready_input = False

    # gui booleans
    gui_use_internal_data = False
    gui_use_interface = False

    @classmethod
    def set_paused(cls, paused):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        if not cls.gui_use_interface: return
        cls.paused = paused
        if cls.paused:
            NARSGUI.NARSGUI.gui_play_pause_button.config(text="PLAY")
        else:
            NARSGUI.NARSGUI.gui_play_pause_button.config(text="PAUSE")

    @classmethod
    def get_current_cycle_number(cls):
        return cls.NARS.memory.current_cycle_number

