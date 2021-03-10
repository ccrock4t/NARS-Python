import InputBuffer
from Global import GlobalGUI, Global
import tkinter as tk

"""
    GUI code (excluding GUI Globals)
"""


def execute_internal_gui():
    """
        Setup the internal GUI window, displaying the system's buffers and memory
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Internal Data")
    window.geometry('650x500')

    output_height = 30
    output_width = 50

    # Task Buffer Output
    GlobalGUI.gui_buffer_output_label = tk.Label(window, text="Task Buffer: 0")
    GlobalGUI.gui_buffer_output_label.grid(row=0, column=0, sticky='w')

    buffer_scrollbar = tk.Scrollbar(window)
    buffer_scrollbar.grid(row=1, column=2, sticky='ns')
    GlobalGUI.gui_experience_buffer_listbox = tk.Listbox(window, height=output_height, width=output_width, font=('', 8),
                                                         yscrollcommand=buffer_scrollbar.set)
    GlobalGUI.gui_experience_buffer_listbox.grid(row=1, column=0, columnspan=2)

    # Memory Output
    GlobalGUI.gui_concepts_output_label = tk.Label(window, text="Concepts: 0")
    GlobalGUI.gui_concepts_output_label.grid(row=0, column=3, sticky='w')

    concept_bag_scrollbar = tk.Scrollbar(window)
    concept_bag_scrollbar.grid(row=1, column=5, sticky='ns')
    GlobalGUI.gui_concept_bag_listbox = tk.Listbox(window, height=output_height, width=output_width, font=('', 8),
                                                   yscrollcommand=concept_bag_scrollbar.set)
    GlobalGUI.gui_concept_bag_listbox.grid(row=1, column=3, columnspan=2)

    window.mainloop()


def execute_interface_gui():
    """
        Setup the interface GUI window, displaying the system's i/o channels
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Interface")
    window.geometry('750x500')

    output_width = 3
    output_height = 3

    # row 0
    output_lbl = tk.Label(window, text="Output: ")
    output_lbl.grid(row=0, column=0, columnspan=output_width)

    # row 1
    output_scrollbar = tk.Scrollbar(window)
    output_scrollbar.grid(row=1, column=3, rowspan=output_height, sticky='ns')

    GlobalGUI.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
    GlobalGUI.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

    # row 2
    GlobalGUI.gui_total_cycles_lbl = tk.Label(window, text="Cycle #0")
    GlobalGUI.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

    speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
    speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

    # row 3
    def toggle_pause(event=None):
        # put input into NARS input buffer
        Global.paused = not Global.paused

        if Global.paused:
            GlobalGUI.play_pause_button.config(text="PLAY")
        else:
            GlobalGUI.play_pause_button.config(text="PAUSE")

    GlobalGUI.play_pause_button = tk.Button(window, text="PAUSE", command=toggle_pause)
    GlobalGUI.play_pause_button.grid(row=3, column=4, sticky='s')

    max_delay = 1000  # in milliseconds
    GlobalGUI.gui_delay_slider = tk.Scale(window, from_=max_delay, to=0)
    GlobalGUI.gui_delay_slider.grid(row=3, column=5, sticky='ns')
    GlobalGUI.gui_delay_slider.set(max_delay)

    # input GUI
    def input_clicked(event=None):
        # put input into NARS input buffer
        InputBuffer.add_input(input_field.get())
        # empty input field
        input_field.delete(0, tk.END)
        input_field.insert(0, "")

    input_lbl = tk.Label(window, text="Input: ")
    input_lbl.grid(column=0, row=4)

    input_field = tk.Entry(window, width=50)
    input_field.grid(column=1, row=4)
    input_field.focus()

    window.bind('<Return>', func=input_clicked)
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)
    send_input_btn.grid(column=2, row=4)

    window.focus()

    window.mainloop()


def get_user_input():
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input(userinput)
