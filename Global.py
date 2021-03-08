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


    """
        GUI vars and functions
    """
    output_textbox = None  # primary output gui
    experience_buffer_listbox = None # output for tasks in experience buffer
    concept_bag_listbox = None # output for concepts in memory bag
    speed_slider = None
    PRINT_ATTENTION = False  # Whether or not to print what the system is focusing on

    @classmethod
    def print_to_output(cls, msg, selfobj=None):
        """
            Print a message to an output GUI box
        """
        if selfobj is None:
            cls.output_textbox.insert(tk.END, msg + "\n")
        elif selfobj is Global.NARS.overall_experience_buffer:
            Global.experience_buffer_listbox.insert(tk.END, msg)
        elif selfobj is Global.NARS.memory.concepts_bag:
            Global.concept_bag_listbox.insert(tk.END, msg)

    @classmethod
    def remove_from_output(cls, msg, selfobj=None):
        """
            Remove a message from an output GUI box
        """
        if selfobj is Global.NARS.overall_experience_buffer:
            idx = Global.experience_buffer_listbox.get(0, tk.END).index(msg)
            Global.experience_buffer_listbox.delete(idx)
        elif selfobj is Global.NARS.memory.concepts_bag:
            idx = Global.concept_bag_listbox.get(0, tk.END).index(msg)
            Global.concept_bag_listbox.delete(idx)