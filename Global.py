"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
import queue
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

    # Internal Data vars
    gui_experience_buffer_listbox = None # output for tasks in experience buffer
    gui_concept_bag_listbox = None # output for concepts in memory bag
    gui_buffer_output_label = None
    gui_concepts_output_label = None
    gui_total_tasks_in_buffer = 0
    gui_total_concepts_in_memory = 0

    # booleans
    gui_use_internal_data = True
    gui_use_interface = True

    #io daemon
    output_thread = None
    outputs_to_add = queue.Queue()
    outputs_to_remove = queue.Queue()

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        """
            Print a message to an output GUI box
        """
        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
            GlobalGUI.outputs_to_add.put((msg, listbox))
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
            GlobalGUI.outputs_to_add.put((msg, listbox))
        elif data_structure is None:
            GlobalGUI.outputs_to_add.put((msg, None))

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from a data structure's output GUI box
        """
        if data_structure is Global.NARS.overall_experience_buffer:
            listbox = GlobalGUI.gui_experience_buffer_listbox
            GlobalGUI.outputs_to_remove.put((msg, listbox))
        elif data_structure is Global.NARS.memory.concepts_bag:
            listbox = GlobalGUI.gui_concept_bag_listbox
            GlobalGUI.outputs_to_remove.put((msg, listbox))


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
            if msg in string_list: return # already added
            listbox.insert(tk.END, msg)
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
            if msg not in string_list: return  # already removed
            idx = string_list.index(msg)
            listbox.delete(idx)
            if listbox is GlobalGUI.gui_experience_buffer_listbox:
                GlobalGUI.gui_total_tasks_in_buffer = GlobalGUI.gui_total_tasks_in_buffer - 1
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(GlobalGUI.gui_total_tasks_in_buffer))
            elif listbox is GlobalGUI.gui_concept_bag_listbox:
                GlobalGUI.gui_total_concepts_in_memory = GlobalGUI.gui_total_concepts_in_memory - 1
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(GlobalGUI.gui_total_concepts_in_memory))