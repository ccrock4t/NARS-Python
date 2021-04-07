import Global
import InputBuffer
import tkinter as tk

import NARSDataStructures
import NARSMemory

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

    Global.Global.gui_thread_ready = True
    window.mainloop()

def execute_internal_gui(window):
    """
        Setup the internal GUI window, displaying the system's buffers and memory
    """
    listbox_height = 30
    listbox_width = 50

    # Task Buffer Output
    Global.GlobalGUI.gui_buffer_output_label = tk.Label(window, text="Task Buffer: 0")
    Global.GlobalGUI.gui_buffer_output_label.grid(row=0, column=0, sticky='w')

    buffer_scrollbar = tk.Scrollbar(window)
    buffer_scrollbar.grid(row=1, column=2, sticky='ns')
    Global.GlobalGUI.gui_experience_buffer_listbox = tk.Listbox(window, height=listbox_height, width=listbox_width, font=('', 8),
                                                                yscrollcommand=buffer_scrollbar.set)
    Global.GlobalGUI.gui_experience_buffer_listbox.grid(row=1, column=0, columnspan=2)

    # Memory Output
    Global.GlobalGUI.gui_concepts_output_label = tk.Label(window, text="Concepts: 0")
    Global.GlobalGUI.gui_concepts_output_label.grid(row=0, column=3, sticky='w')

    concept_bag_scrollbar = tk.Scrollbar(window)
    concept_bag_scrollbar.grid(row=1, column=5, sticky='ns')
    Global.GlobalGUI.gui_concept_bag_listbox = tk.Listbox(window, height=listbox_height, width=listbox_width, font=('', 8),
                                                          yscrollcommand=concept_bag_scrollbar.set)
    Global.GlobalGUI.gui_concept_bag_listbox.grid(row=1, column=3, columnspan=2)

    def listbox_sentence_item_click_callback(event, iterable_with_sentences):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            sentence_string = event.widget.get(index)
            needs_indexing = isinstance(iterable_with_sentences, NARSDataStructures.Table)
            for sentence_from_iterable in iterable_with_sentences:
                if needs_indexing:
                    sentence_from_iterable = sentence_from_iterable[0]
                if str(sentence_from_iterable) == sentence_string: # found clicked sentence
                    # window
                    item_info_window = tk.Toplevel()
                    item_info_window.title("Sentence Internal Data: " + str(sentence_from_iterable))
                    item_info_window.geometry('600x500')
                    item_info_window.grab_set()  # lock the other windows until this window is exited

                    object_listbox_width = 40
                    object_listbox_height = 20

                    label = tk.Label(item_info_window, text="Sentence: ")
                    label.grid(row=0, column=0)

                    label = tk.Label(item_info_window, text=sentence_from_iterable.get_formatted_string_no_id())
                    label.grid(row=0, column=1)

                    label = tk.Label(item_info_window, text="Sentence ID: ")
                    label.grid(row=1, column=0)

                    label = tk.Label(item_info_window, text=str(sentence_from_iterable.stamp.id))
                    label.grid(row=1, column=1)

                    label = tk.Label(item_info_window, text="Occurence Time: ")
                    label.grid(row=2, column=0)

                    oc_time = sentence_from_iterable.stamp.occurrence_time

                    label = tk.Label(item_info_window, text=str("Eternal" if oc_time is None else oc_time))
                    label.grid(row=2, column=1)

                    label = tk.Label(item_info_window, text="")
                    label.grid(row=3, column=1)

                    # Evidential base listbox
                    label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
                    label.grid(row=4, column=0,columnspan=2)

                    evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                         width=object_listbox_width, font=('', 8))
                    evidential_base_listbox.grid(row=5, column=0,columnspan=2)
                    for sentence in sentence_from_iterable.stamp.evidential_base:
                        evidential_base_listbox.insert(tk.END, str(sentence))
                    evidential_base_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,sentence_from_iterable.stamp.evidential_base))

                    # Interacted sentences listbox
                    label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
                    label.grid(row=4, column=2,columnspan=2)

                    interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                              width=object_listbox_width, font=('', 8))
                    interacted_sentences_listbox.grid(row=5, column=2,columnspan=2)
                    for sentence in sentence_from_iterable.stamp.interacted_sentences:
                        interacted_sentences_listbox.insert(tk.END, str(sentence))
                    interacted_sentences_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,sentence_from_iterable.stamp.interacted_sentences))

    def listbox_datastructure_item_click_callback(event):
        """
            Presents a window describing the concept's internal data.
            Locks the interface until the window is closed.

            This function is called when the user clicks on an item in the internal data.
        """
        selection = event.widget.curselection()
        if selection:
            Global.Global.set_paused(True)
            index = selection[0]
            item_string = event.widget.get(index)

            key = None
            data_structure = None

            if event.widget is Global.GlobalGUI.gui_concept_bag_listbox:
                key = item_string[item_string.rfind(Global.Global.ID_END_MARKER) + 2:item_string.find(Global.GlobalGUI.GUI_BUDGET_SYMBOL) - 1]  # remove ID and priority, concept term string is the key
                data_structure = Global.Global.NARS.memory.concepts_bag
            elif event.widget is Global.GlobalGUI.gui_experience_buffer_listbox:
                key = item_string[item_string.find(Global.Global.BAG_ITEM_ID_MARKER)+len(Global.Global.BAG_ITEM_ID_MARKER):item_string.rfind(Global.Global.ID_END_MARKER)]
                data_structure = Global.Global.NARS.overall_experience_buffer

            assert key is not None, "Couldn't get key from item click callback"

            object = data_structure.peek(key)

            # window
            item_info_window = tk.Toplevel()
            item_info_window.title(type(object).__name__ + " Internal Data: " + item_string)
            item_info_window.geometry('600x500')
            item_info_window.grab_set()  # lock the other windows until this window is exited

            # info
            label = tk.Label(item_info_window, text=type(object).__name__ + " Name: ")
            label.grid(row=0, column=0)

            label = tk.Label(item_info_window, text=str(object))
            label.grid(row=0, column=1)

            object_listbox_width = 40
            object_listbox_height = 20

            if isinstance(object, NARSMemory.Concept):

                label = tk.Label(item_info_window, text="Number of Term Links: ",justify=tk.LEFT)
                label.grid(row=1, column=0)

                label = tk.Label(item_info_window, text=str(object.term_links.count),justify=tk.LEFT)
                label.grid(row=1, column=1)

                label = tk.Label(item_info_window, text="",justify=tk.LEFT)
                label.grid(row=2, column=0)

                label = tk.Label(item_info_window, text="Beliefs", font=('bold'))
                label.grid(row=4, column=0,columnspan=2)

                # beliefs table listbox
                belief_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width, font=('', 8))
                belief_listbox.grid(row=5,column=0,columnspan=2)
                for belief in object.belief_table:
                    if isinstance(object.belief_table, NARSDataStructures.Bag):
                        belief_listbox.insert(tk.END,str(belief.object))
                    elif isinstance(object.belief_table, NARSDataStructures.Table):
                        belief_listbox.insert(tk.END, str(belief[0]))

                belief_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,object.belief_table)) # define callback

                # desires table listbox
                label = tk.Label(item_info_window, text="Desires", font=('bold'))
                label.grid(row=4, column=2,columnspan=2)

                desire_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width, font=('', 8))
                desire_listbox.grid(row=5,column=2,columnspan=2)
                for desire in object.desire_table:
                    desire_listbox.insert(tk.END,str(desire[0]))
                desire_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,object.desire_table)) # define callback

            elif isinstance(object, NARSDataStructures.Task):
                # Evidential base listbox

                label = tk.Label(item_info_window, text="Sentence: ",justify=tk.LEFT)
                label.grid(row=1, column=0)

                labelClickable = tk.Listbox(item_info_window, height=1)
                labelClickable.insert(tk.END, str(object.sentence))
                labelClickable.grid(row=1, column=1)
                labelClickable.bind("<<ListboxSelect>>",
                                                  lambda event: listbox_sentence_item_click_callback(event,
                                                                                                     [object.sentence]))

                label = tk.Label(item_info_window, text="",justify=tk.LEFT)
                label.grid(row=2, column=0)

                # Evidential base listbox
                label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
                label.grid(row=3, column=0,columnspan=2)

                evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width, font=('', 8))
                evidential_base_listbox.grid(row=4,column=0,columnspan=2)
                for sentence in object.sentence.stamp.evidential_base:
                    evidential_base_listbox.insert(tk.END,str(sentence))
                evidential_base_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,object.sentence.stamp.evidential_base))

                # Interacted sentences listbox
                label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
                label.grid(row=3, column=2,columnspan=2)

                interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width, font=('', 8))
                interacted_sentences_listbox.grid(row=4,column=2,columnspan=2)
                for sentence in object.sentence.stamp.interacted_sentences:
                    interacted_sentences_listbox.insert(tk.END,str(sentence))
                interacted_sentences_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,object.sentence.stamp.interacted_sentences))


    # define callbacks when clicking items in any box
    Global.GlobalGUI.gui_concept_bag_listbox.bind("<<ListboxSelect>>", listbox_datastructure_item_click_callback)
    Global.GlobalGUI.gui_experience_buffer_listbox.bind("<<ListboxSelect>>", listbox_datastructure_item_click_callback)


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
        """
            Toggle the global paused parameter
        """
        Global.Global.set_paused(not Global.Global.paused)

    Global.GlobalGUI.gui_play_pause_button = tk.Button(window, text="", command=toggle_pause)
    Global.Global.set_paused(Global.Global.paused)
    Global.GlobalGUI.gui_play_pause_button.grid(row=3, column=4, sticky='s')

    max_delay = 1000  # in milliseconds
    Global.GlobalGUI.gui_delay_slider = tk.Scale(window, from_=max_delay, to=0)
    Global.GlobalGUI.gui_delay_slider.grid(row=3, column=5, sticky='ns')
    Global.GlobalGUI.gui_delay_slider.set(max_delay)

    # input GUI
    def input_clicked(event=None):
        """
            Callback when clicking button to send input
        """
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

    window.bind('<Return>', func=input_clicked) # send input when pressing 'enter'
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked) # send input when click button
    send_input_btn.grid(column=2, row=4)

    window.focus()

def get_user_input():
    Global.Global.input_thread_ready = True
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input_string(userinput)
