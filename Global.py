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

    # Internal Data vars
    gui_experience_buffer_listbox = None # output for tasks in experience buffer
    gui_concept_bag_listbox = None # output for concepts in memory bag
    gui_buffer_output_label = None
    gui_concepts_output_label = None
    gui_total_tasks_in_buffer = 0
    gui_total_concepts_in_memory = 0

    # booleans
    gui_use_internal_data = True # Setting this to false will significantly increase speed
    gui_use_interface = True # Setting this to false uses console/shell as the interface

    @classmethod
    def print_to_output(cls, msg, selfobj=None):
        """
            Print a message to an output GUI box
        """
        if selfobj is None:
            if cls.gui_use_interface:
                cls.gui_output_textbox.insert(tk.END, msg + "\n")
            else:
                print(msg)

        if GlobalGUI.gui_use_internal_data and Global.NARS is not None:
            if selfobj is Global.NARS.overall_experience_buffer:
                GlobalGUI.gui_experience_buffer_listbox.insert(tk.END, msg)
                GlobalGUI.gui_total_tasks_in_buffer = GlobalGUI.gui_total_tasks_in_buffer + 1
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(GlobalGUI.gui_total_tasks_in_buffer))
            elif selfobj is Global.NARS.memory.concepts_bag:
                GlobalGUI.gui_concept_bag_listbox.insert(tk.END, msg)
                GlobalGUI.gui_total_concepts_in_memory = GlobalGUI.gui_total_concepts_in_memory + 1
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(GlobalGUI.gui_total_concepts_in_memory))

    @classmethod
    def remove_from_output(cls, msg, selfobj=None):
        """
            Remove a message from an output GUI box
        """
        if GlobalGUI.gui_use_internal_data and Global.NARS is not None:
            if selfobj is Global.NARS.overall_experience_buffer:
                idx = GlobalGUI.gui_experience_buffer_listbox.get(0, tk.END).index(msg)
                GlobalGUI.gui_experience_buffer_listbox.delete(idx)
                GlobalGUI.gui_total_tasks_in_buffer = GlobalGUI.gui_total_tasks_in_buffer - 1
                GlobalGUI.gui_buffer_output_label.config(text="Task Buffer: " + str(GlobalGUI.gui_total_tasks_in_buffer))
            elif selfobj is Global.NARS.memory.concepts_bag:
                idx = GlobalGUI.gui_concept_bag_listbox.get(0, tk.END).index(msg)
                GlobalGUI.gui_concept_bag_listbox.delete(idx)
                GlobalGUI.gui_total_concepts_in_memory = GlobalGUI.gui_total_concepts_in_memory - 1
                GlobalGUI.gui_concepts_output_label.config(text="Concepts: " + str(GlobalGUI.gui_total_concepts_in_memory))