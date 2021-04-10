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
    BAG_ITEM_ID_MARKER = "ItemID:"  # there are Sentence IDs and Bag Item IDs
    SENTENCE_ID_MARKER = "SentenceID:"
    ID_END_MARKER = ": "

    # thread ready boolean
    gui_thread_ready = False
    input_thread_ready = False

    # gui booleans
    gui_use_internal_data = False
    gui_use_interface = False

    @classmethod
    def set_paused(cls, paused):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        if not Global.gui_use_interface: return
        Global.paused = paused
        if Global.paused:
            NARSGUI.NARSGUI.gui_play_pause_button.config(text="PLAY")
        else:
            NARSGUI.NARSGUI.gui_play_pause_button.config(text="PAUSE")

