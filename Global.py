"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
import tkinter as tk

class Global:
    NARS = None  # variable to hold NARS instance
    current_cycle_number = 0  # total number of working cycles executed so far
    PRINT_ATTENTION = False  # Whether or not to print what the system is focusing on

    """
        GUI vars
    """
    output_textbox = None  # output textbox for gui
    experience_buffer_listbox = None # output for tasks in experience buffer
    concept_bag_listbox = None # output for concepts in memory bag

    @classmethod
    def print_to_output(cls, msg, selfobj=None):
        if selfobj is None:
            cls.output_textbox.insert(tk.END, msg + "\n")
        elif selfobj is Global.NARS.overall_experience_buffer:
            Global.experience_buffer_listbox.insert(tk.END, msg)
        elif selfobj is Global.NARS.memory.concepts_bag:
            Global.concept_bag_listbox.insert(tk.END, msg)

    @classmethod
    def remove_from_output(cls, msg, selfobj=None):
        if selfobj is Global.NARS.overall_experience_buffer:
            idx = Global.experience_buffer_listbox.get(0, tk.END).index(msg)
            Global.experience_buffer_listbox.delete(idx)
        elif selfobj is Global.NARS.memory.concepts_bag:
            idx = Global.concept_bag_listbox.get(0, tk.END).index(msg)
            Global.concept_bag_listbox.delete(idx)