"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
import tkinter as tk


class Global:
    """
        NARS vars
    """
    NARS = None  # variable to hold NARS instance
    paused = True
    BAG_ITEM_ID_MARKER = "ItemID:" # there are Sentence IDs and Bag Item IDs
    SENTENCE_ID_MARKER = "SentenceID:"
    ID_END_MARKER = ": "

    @classmethod
    def set_paused(cls, paused):
        """
            Sets the Global paused parameter and changes the GUI button
        """
        Global.paused = paused
        if Global.paused:
            GlobalGUI.gui_play_pause_button.config(text="PLAY")
        else:
            GlobalGUI.gui_play_pause_button.config(text="PAUSE")


class GlobalGUI:
    """
        GUI vars and functions
    """
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None  # delay slider
    gui_total_cycles_lbl = None
    gui_play_pause_button = None

    # Internal Data vars
    gui_experience_buffer_listbox = None  # output for tasks in experience buffer
    gui_concept_bag_listbox = None  # output for concepts in memory bag
    gui_buffer_output_label = None
    gui_concepts_output_label = None
    GUI_BUDGET_SYMBOL = "$"

    # booleans
    gui_use_internal_data = False
    gui_use_interface = False

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        """
            Print a message to an output GUI box
        """

        listbox = None
        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
        elif data_structure is None:
            # output to interface or shell
            if cls.gui_use_interface:
                cls.gui_output_textbox.insert(tk.END, msg + "\n")
            else:
                print(msg)

        if listbox is None: return

        # internal data output
        # insert item sorted by priority
        if GlobalGUI.gui_use_internal_data:
            string_list = listbox.get(0, tk.END)  # get all items in the listbox
            msg_priority = msg[msg.find(GlobalGUI.GUI_BUDGET_SYMBOL) + 1:msg.rfind(GlobalGUI.GUI_BUDGET_SYMBOL)]
            idx_to_insert = tk.END  # by default insert at the end
            i = 0
            for row in string_list:
                row_priority = row[row.find(GlobalGUI.GUI_BUDGET_SYMBOL) + 1:row.rfind(GlobalGUI.GUI_BUDGET_SYMBOL)]
                if float(msg_priority) > float(row_priority):
                    idx_to_insert = i
                    break
                i = i + 1
            listbox.insert(idx_to_insert, msg)
            if data_structure is Global.NARS.overall_experience_buffer:
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(len(data_structure)))
            elif data_structure is Global.NARS.memory.concepts_bag:
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(len(data_structure)))

        cls.update_datastructure_labels(data_structure)

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from an output GUI box
        """
        if Global.NARS is None: return
        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox

        if GlobalGUI.gui_use_internal_data:
            string_list = listbox.get(0, tk.END)
            msg_id = msg[len(Global.BAG_ITEM_ID_MARKER):msg.rfind(Global.ID_END_MARKER)]  # assuming ID is at the beginning, get characters from ID: to first spacebar
            idx_to_remove = -1
            i = 0
            for row in string_list:
                row_id = row[len(Global.BAG_ITEM_ID_MARKER):row.rfind(Global.ID_END_MARKER)]
                if msg_id == row_id:
                    idx_to_remove = i
                    break
                i = i + 1
            if idx_to_remove == -1:
                assert False, "GUI Error: cannot find msg to remove: " + msg
            listbox.delete(idx_to_remove)

        cls.update_datastructure_labels(data_structure)

    @classmethod
    def update_datastructure_labels(cls,data_structure):
        if data_structure is Global.NARS.overall_experience_buffer:
            GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(len(data_structure)))
        elif data_structure is Global.NARS.memory.concepts_bag:
            GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(len(data_structure)) + " / " + str(data_structure.max_capacity))

    @classmethod
    def clear_output_gui(cls, data_structure=None):
        if data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
            listbox.delete(0, tk.END)

