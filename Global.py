"""
    Author: Christian Hahm
    Created: December 24, 2020
"""
import tkinter as tk

class Global:
    NARS = None  # variable to hold NARS instance
    current_cycle_number = 0  # total number of working cycles executed so far
    PRINT_ATTENTION = False  # Whether or not to print what the system is focusing on
    output_textbox = None  # output textbox for gui

    @classmethod
    def print_to_output(cls, msg):
        cls.output_textbox.insert(tk.END, msg + "\n")