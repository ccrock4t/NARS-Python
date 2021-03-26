import Global
import InputBuffer
import tkinter as tk

"""
    GUI code (excluding GUI Globals)
"""

def execute_gui():
    """
        Setup and run 2 windows on a single thread
    """
    if Global.GlobalGUI.gui_use_interface:
        # launch internal data GUI
        window = tk.Tk()
        window.title("NARS in Python - Interface")
        window.geometry('750x500')
        execute_interface_gui(window)

        if Global.GlobalGUI.gui_use_internal_data:
            # launch GUI
            toplevel = tk.Toplevel()
            toplevel.title("NARS in Python - Internal Data")
            toplevel.geometry('650x500')
            execute_internal_gui(toplevel)
    elif Global.GlobalGUI.gui_use_internal_data:
        # launch GUI
        window = tk.Tk()
        window.title("NARS in Python - Internal Data")
        window.geometry('650x500')
        execute_internal_gui(window)

    window.mainloop()

def execute_internal_gui(window):
    """
        Setup the internal GUI window, displaying the system's buffers and memory
    """
    output_height = 30
    output_width = 50

    # Task Buffer Output
    Global.GlobalGUI.gui_buffer_output_label = tk.Label(window, text="Task Buffer: 0")
    Global.GlobalGUI.gui_buffer_output_label.grid(row=0, column=0, sticky='w')

    buffer_scrollbar = tk.Scrollbar(window)
    buffer_scrollbar.grid(row=1, column=2, sticky='ns')
    Global.GlobalGUI.gui_experience_buffer_listbox = tk.Listbox(window, height=output_height, width=output_width, font=('', 8),
                                                                yscrollcommand=buffer_scrollbar.set)
    Global.GlobalGUI.gui_experience_buffer_listbox.grid(row=1, column=0, columnspan=2)

    # Memory Output
    Global.GlobalGUI.gui_concepts_output_label = tk.Label(window, text="Concepts: 0")
    Global.GlobalGUI.gui_concepts_output_label.grid(row=0, column=3, sticky='w')

    concept_bag_scrollbar = tk.Scrollbar(window)
    concept_bag_scrollbar.grid(row=1, column=5, sticky='ns')
    Global.GlobalGUI.gui_concept_bag_listbox = tk.Listbox(window, height=output_height, width=output_width, font=('', 8),
                                                          yscrollcommand=concept_bag_scrollbar.set)
    Global.GlobalGUI.gui_concept_bag_listbox.grid(row=1, column=3, columnspan=2)

    def concept_click_callback(event):
        """
            Presents a window describing the concept's internal data.
            Locks the interface until the window is closed.

            This function is called when the user clicks on a Concept.
        """
        selection = event.widget.curselection()
        if selection:
            Global.GlobalGUI.set_paused(True)
            index = selection[0]
            concept_term_string = event.widget.get(index)
            concept_term_string = concept_term_string[concept_term_string.rfind(Global.Global.ID_END_MARKER) + 2:concept_term_string.find(Global.GlobalGUI.GUI_PRIORITY_SYMBOL) - 1] # remove priority
            key = concept_term_string
            concept = Global.Global.NARS.memory.concepts_bag.peek(key).object

            # window
            concept_info_toplevel = tk.Toplevel()
            concept_info_toplevel.title("Concept Internal Data: " + concept_term_string)
            concept_info_toplevel.geometry('550x500')

            # info
            label = tk.Label(concept_info_toplevel, text="CONCEPT NAME: " + concept_term_string)
            label.grid(row=0,column=0)

            label = tk.Label(concept_info_toplevel, text="Number of Term Links: " + str(concept.term_links.count))
            label.grid(row=1, column=0)

            label = tk.Label(concept_info_toplevel, text="Beliefs")
            label.grid(row=2, column=1)

            belief_listbox = tk.Listbox(concept_info_toplevel, height=20, width=30, font=('', 8))
            belief_listbox.grid(row=3,column=1)
            for belief in concept.belief_table.depq:
                belief_listbox.insert(tk.END,str(belief[0]))

            label = tk.Label(concept_info_toplevel, text="Desires")
            label.grid(row=2, column=2)

            desire_listbox = tk.Listbox(concept_info_toplevel, height=20, width=30, font=('', 8))
            desire_listbox.grid(row=3,column=2)
            for desire in concept.desire_table.depq:
                desire_listbox.insert(tk.END,str(desire[0]))

            concept_info_toplevel.grab_set() # lock the other windows until this window is exited

    Global.GlobalGUI.gui_concept_bag_listbox.bind("<<ListboxSelect>>", concept_click_callback)


def execute_interface_gui(window):
    """
        Setup the interface GUI window, displaying the system's i/o channels
    """
    output_width = 3
    output_height = 3

    # row 0
    output_lbl = tk.Label(window, text="Output: ")
    output_lbl.grid(row=0, column=0, columnspan=output_width)

    # row 1
    output_scrollbar = tk.Scrollbar(window)
    output_scrollbar.grid(row=1, column=3, rowspan=output_height, sticky='ns')

    Global.GlobalGUI.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
    Global.GlobalGUI.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

    # row 2
    Global.GlobalGUI.gui_total_cycles_lbl = tk.Label(window, text="Cycle #0")
    Global.GlobalGUI.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

    speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
    speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

    # row 3
    def toggle_pause(event=None):
        # put input into NARS input buffer
        Global.GlobalGUI.set_paused(not Global.Global.paused)

    Global.GlobalGUI.play_pause_button = tk.Button(window, text="PAUSE", command=toggle_pause)
    Global.GlobalGUI.play_pause_button.grid(row=3, column=4, sticky='s')

    max_delay = 1000  # in milliseconds
    Global.GlobalGUI.gui_delay_slider = tk.Scale(window, from_=max_delay, to=0)
    Global.GlobalGUI.gui_delay_slider.grid(row=3, column=5, sticky='ns')
    Global.GlobalGUI.gui_delay_slider.set(max_delay)

    # input GUI
    def input_clicked(event=None):
        # put input into NARS input buffer
        userinput = input_field.get()
        InputBuffer.add_input_string(userinput)
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

def get_user_input():
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input_string(userinput)
