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
    current_cycle_number = 0  # total number of working cycles executed so far
    paused = False

class GlobalGUI:
    """
        GUI vars and functions
    """
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None # delay slider
    gui_total_cycles_lbl = None
    play_pause_button = None

    # Internal Data vars
    gui_experience_buffer_listbox = None # output for tasks in experience buffer
    gui_concept_bag_listbox = None # output for concepts in memory bag
    gui_buffer_output_label = None
    gui_concepts_output_label = None
    gui_total_tasks_in_buffer = 0
    gui_total_concepts_in_memory = 0
    GUI_PRIORITY_SYMBOL = "$"

    # booleans
    gui_use_internal_data = True
    gui_use_interface = True

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        """
            Print a message to an output GUI box
        """
        if Global.NARS is None: return

        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
            GlobalGUI._print_to_output(msg, listbox)
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
            GlobalGUI._print_to_output(msg, listbox)
        elif data_structure is None:
            GlobalGUI._print_to_output(msg, None)

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from a data structure's output GUI box
        """
        if Global.NARS is None: return

        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
            GlobalGUI._remove_from_output(msg, listbox)
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
            GlobalGUI._remove_from_output(msg, listbox)


    @classmethod
    def _print_to_output(cls, msg, listbox=None):
        """
            Print a message to an output GUI box

            Should only called by output thread
        """
        if listbox is None: # interface output
            if cls.gui_use_interface:
                cls.gui_output_textbox.insert(tk.END, msg + "\n")
            else:
                print(msg)
            return

        # internal data output
        if GlobalGUI.gui_use_internal_data:
            string_list = listbox.get(0, tk.END)
            msg_priority = msg[msg.find(GlobalGUI.GUI_PRIORITY_SYMBOL)+1:msg.rfind(GlobalGUI.GUI_PRIORITY_SYMBOL)]
            idx_to_insert = tk.END # by default insert at the end
            i = 0
            for row in string_list:
                row_priority = row[row.find(GlobalGUI.GUI_PRIORITY_SYMBOL)+1:row.rfind(GlobalGUI.GUI_PRIORITY_SYMBOL)]
                if float(msg_priority) >= float(row_priority):
                    idx_to_insert = i
                    break
                i = i + 1
            listbox.insert(idx_to_insert, msg)
            if listbox is GlobalGUI.gui_experience_buffer_listbox:
                GlobalGUI.gui_total_tasks_in_buffer = GlobalGUI.gui_total_tasks_in_buffer + 1
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(GlobalGUI.gui_total_tasks_in_buffer))
            elif listbox is GlobalGUI.gui_concept_bag_listbox:
                GlobalGUI.gui_total_concepts_in_memory = GlobalGUI.gui_total_concepts_in_memory + 1
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(GlobalGUI.gui_total_concepts_in_memory))

    @classmethod
    def _remove_from_output(cls, msg, listbox=None):
        """
            Remove a message from an output GUI box

            Should only be called by output thread
        """
        if GlobalGUI.gui_use_internal_data:
            string_list = listbox.get(0, tk.END)
            msg_without_priority = msg[0:msg.find(GlobalGUI.GUI_PRIORITY_SYMBOL)]
            idx_to_remove = -1
            i = 0
            for row in string_list:
                row_string_without_priority = row[0:row.find(GlobalGUI.GUI_PRIORITY_SYMBOL)]
                if msg_without_priority == row_string_without_priority:
                    idx_to_remove = i
                    break
                i = i + 1
            if idx_to_remove == -1: return
            listbox.delete(idx_to_remove)
            if listbox is GlobalGUI.gui_experience_buffer_listbox:
                GlobalGUI.gui_total_tasks_in_buffer = GlobalGUI.gui_total_tasks_in_buffer - 1
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(GlobalGUI.gui_total_tasks_in_buffer))
            elif listbox is GlobalGUI.gui_concept_bag_listbox:
                GlobalGUI.gui_total_concepts_in_memory = GlobalGUI.gui_total_concepts_in_memory - 1
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(GlobalGUI.gui_total_concepts_in_memory))

    @classmethod
    def set_paused(cls, paused):
        """
            Sets the Global paused parameter and changes the GUI button
        """
        Global.paused = paused
        if Global.paused:
            GlobalGUI.play_pause_button.config(text="PLAY")
        else:
            GlobalGUI.play_pause_button.config(text="PAUSE")