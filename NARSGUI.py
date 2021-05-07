import queue
import threading

import Global
import InputBuffer
import tkinter as tk

import NALGrammar
import NARSDataStructures
import NARSMemory

"""
    GUI code
    Only use this after Global NARS object has been created.
"""

class NARSGUI:
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None  # delay slider
    gui_total_cycles_lbl = None
    gui_play_pause_button = None

    # Internal Data vars
    # listboxes
    gui_experience_buffer_listbox = None  # output for tasks in experience buffer
    gui_memory_listbox = None  # output for concepts in memory bag
    gui_sensorimotor_buffer_listbox = None # output for tasks in sensorimotor event buffer

    # labels
    gui_sensorimotor_buffer_output_label = None
    gui_experience_buffer_output_label = None
    gui_concepts_bag_output_label = None
    GUI_BUDGET_SYMBOL = "$"

    @classmethod
    def print_to_output(cls, msg, data_structure=None):
        """
             Print a message to an output GUI box
         """
        NARS = Global.Global.NARS
        listbox = None
        if data_structure is NARS.experience_task_buffer:
            listbox = cls.gui_experience_buffer_listbox
        elif data_structure is NARS.memory.concepts_bag:
            listbox = cls.gui_memory_listbox
        elif data_structure is NARS.sensorimotor_event_buffer:
            listbox = cls.gui_sensorimotor_buffer_listbox
        elif data_structure is None:
            # output to interface or shell
            if Global.Global.gui_use_interface:
                cls.gui_output_textbox.insert(tk.END, msg + "\n")
            else:
                print(msg)

        if listbox is None: return
        # internal data output
        # insert item sorted by priority
        if Global.Global.gui_use_internal_data:
            if data_structure is NARS.sensorimotor_event_buffer:
                idx_to_insert = tk.END
            else:
                string_list = listbox.get(0, tk.END)  # get all items in the listbox
                msg_priority = msg[msg.find(cls.GUI_BUDGET_SYMBOL) + 1:msg.rfind(
                    cls.GUI_BUDGET_SYMBOL)]
                idx_to_insert = tk.END  # by default insert at the end
                i = 0
                for row in string_list:
                    row_priority = row[row.find(cls.GUI_BUDGET_SYMBOL) + 1:row.rfind(
                        cls.GUI_BUDGET_SYMBOL)]
                    if float(msg_priority) > float(row_priority):
                        idx_to_insert = i
                        break
                    i += 1

            listbox.insert(idx_to_insert, msg)
            cls.update_datastructure_labels(data_structure)

    @classmethod
    def remove_from_output(cls, msg, data_structure=None):
        """
            Remove a message from an output GUI box
        """

        NARS = Global.Global.NARS
        if NARS is None: return
        if not Global.Global.gui_use_internal_data: return

        if data_structure is NARS.experience_task_buffer:
            listbox = cls.gui_experience_buffer_listbox
        elif data_structure is NARS.memory.concepts_bag:
            listbox = cls.gui_memory_listbox
        elif data_structure is NARS.sensorimotor_event_buffer:
            listbox = cls.gui_sensorimotor_buffer_listbox

        string_list = listbox.get(0, tk.END)
        msg_id = msg[len(Global.Global.ITEM_ID_MARKER):msg.rfind(
            Global.Global.ID_END_MARKER)]  # assuming ID is at the beginning, get characters from ID: to first spacebar
        idx_to_remove = -1
        i = 0
        for row in string_list:
            row_id = row[len(Global.Global.ITEM_ID_MARKER):row.rfind(Global.Global.ID_END_MARKER)]
            if msg_id == row_id:
                idx_to_remove = i
                break
            i = i + 1

        if idx_to_remove == -1:
            assert False, "GUI Error: cannot find msg to remove: " + msg

        listbox.delete(idx_to_remove)

        cls.update_datastructure_labels(data_structure)

    @classmethod
    def update_datastructure_labels(cls, data_structure):
        assert data_structure is not None, "Cannot update label for Null data structure!"
        label_txt = ""
        label = None
        NARS = Global.Global.NARS
        if data_structure is NARS.experience_task_buffer:
            label_txt = "Experience Task "
            label = cls.gui_experience_buffer_output_label
        elif data_structure is NARS.memory.concepts_bag:
            label_txt = "Concepts "
            label = cls.gui_concepts_bag_output_label
        elif data_structure is NARS.sensorimotor_event_buffer:
            label_txt = "Sensorimotor "
            label = cls.gui_sensorimotor_buffer_output_label

        if label is None: return
        length = len(data_structure)
        label.config(
            text=(label_txt + type(data_structure).__name__ + ": " + str(length) + " / " + str(
                data_structure.capacity)))

    @classmethod
    def clear_output_gui(cls, data_structure=None):
        if data_structure is Global.Global.NARS.memory.concepts_bag:
            listbox = cls.gui_memory_listbox
            listbox.delete(0, tk.END)

    @classmethod
    def execute_gui(cls):
        """
            Setup and run 2 windows on a single thread
        """
        internal_data_dimensions = "1000x500"
        if Global.Global.gui_use_interface:
            # launch internal data GUI
            window = tk.Tk()
            window.title("NARS in Python - Interface")
            window.geometry('750x500')
            cls.execute_interface_gui(window)

            if Global.Global.gui_use_internal_data:
                # launch GUI
                toplevel = tk.Toplevel()
                toplevel.title("NARS in Python - Internal Data")
                toplevel.geometry(internal_data_dimensions)
                cls.execute_internal_gui(toplevel)
        elif not Global.Global.gui_use_interface and Global.Global.gui_use_internal_data:
            # launch GUI
            window = tk.Tk()
            window.title("NARS in Python - Internal Data")
            window.geometry(internal_data_dimensions)
            cls.execute_internal_gui(window)

        Global.Global.thread_ready_gui = True
        window.mainloop()

    @classmethod
    def execute_internal_gui(cls,window):
        """
            Setup the internal GUI window, displaying the system's buffers and memory
        """
        listbox_height = 30
        listbox_width = 80

        """
            Sensorimotor event buffer internal contents GUI
        """
        cls.gui_sensorimotor_buffer_output_label = tk.Label(window)
        cls.gui_sensorimotor_buffer_output_label.grid(row=0, column=0, sticky='w')

        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=1, column=2, sticky='ns')
        cls.gui_sensorimotor_buffer_listbox = tk.Listbox(window,
                                                       height=listbox_height//3,
                                                       width=listbox_width, font=('', 8),
                                                       yscrollcommand=buffer_scrollbar.set)
        cls.gui_sensorimotor_buffer_listbox.grid(row=1, column=0, columnspan=1)

        """
            Experience Buffer internal contents GUI
        """
        cls.gui_experience_buffer_output_label = tk.Label(window)
        cls.gui_experience_buffer_output_label.grid(row=2, column=0, sticky='w')

        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=3, column=2, sticky='ns')
        cls.gui_experience_buffer_listbox = tk.Listbox(window,
                                                       height=2*listbox_height//3,
                                                       width=listbox_width, font=('', 8),
                                                       yscrollcommand=buffer_scrollbar.set)
        cls.gui_experience_buffer_listbox.grid(row=3, column=0, columnspan=1)

        """
            Memory internal contents GUI
        """
        cls.gui_concepts_bag_output_label = tk.Label(window)
        cls.gui_concepts_bag_output_label.grid(row=0,
                                                column=3,
                                                sticky='w')

        concept_bag_scrollbar = tk.Scrollbar(window)
        concept_bag_scrollbar.grid(row=1,
                                   column=5,
                                   rowspan=4,
                                   sticky='ns')
        cls.gui_memory_listbox = tk.Listbox(window,
                                            height=listbox_height,
                                            width=listbox_width,
                                            font=('', 8),
                                            yscrollcommand=concept_bag_scrollbar.set)
        cls.gui_memory_listbox.grid(row=1,
                                    column=3,
                                    columnspan=1,
                                    rowspan=4)

        # define callbacks when clicking items in any box
        cls.gui_memory_listbox.bind("<<ListboxSelect>>", listbox_datastructure_item_click_callback)
        cls.gui_experience_buffer_listbox.bind("<<ListboxSelect>>", listbox_datastructure_item_click_callback)

        cls.update_datastructure_labels(Global.Global.NARS.experience_task_buffer)
        cls.update_datastructure_labels(Global.Global.NARS.memory.concepts_bag)
        cls.update_datastructure_labels(Global.Global.NARS.sensorimotor_event_buffer)

    @classmethod
    def execute_interface_gui(cls,window):
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

        cls.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
        cls.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

        # row 2
        cls.gui_total_cycles_lbl = tk.Label(window, text="Cycle #0")
        cls.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

        speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
        speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

        cls.gui_play_pause_button = tk.Button(window, text="", command=toggle_pause)
        Global.Global.set_paused(Global.Global.paused)
        cls.gui_play_pause_button.grid(row=3, column=4, sticky='s')

        def delay_slider_changed(event=None):
            Global.Global.NARS.delay = NARSGUI.gui_delay_slider.get() / 1000


        max_delay = 1000  # in milliseconds
        cls.gui_delay_slider = tk.Scale(window, from_=max_delay, to=0)
        cls.gui_delay_slider.grid(row=3, column=5, sticky='ns')
        cls.gui_delay_slider.bind('<ButtonRelease-1>',delay_slider_changed)
        cls.gui_delay_slider.set(max_delay)
        delay_slider_changed()

        # input GUI
        def input_clicked(event=None):
            """
                Callback when clicking button to send input
            """
            # put input into NARS input buffer
            userinput = input_field.get(index1=1.0, index2=tk.END)
            lines = userinput.splitlines(False)
            for line in lines:
                InputBuffer.add_input_string(line)
            # empty input field
            input_field.delete(1.0, tk.END)

        input_lbl = tk.Label(window, text="Input: ")
        input_lbl.grid(column=0, row=4)

        input_field = tk.Text(window, width=50, height=4)
        input_field.grid(column=1, row=4)
        input_field.focus()

        #window.bind('<Return>', func=input_clicked)  # send input when pressing 'enter'
        send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)  # send input when click button
        send_input_btn.grid(column=2, row=4)

        window.focus()

    @classmethod
    def get_user_input(cls):
        Global.Global.thread_ready_input = True
        userinput = ""
        while userinput != "exit":
            userinput = input("")
            InputBuffer.add_input_string(userinput)

def listbox_sentence_item_click_callback(event, iterable_with_sentences):
    selection = event.widget.curselection()
    if selection:
        index = selection[0]
        sentence_string = event.widget.get(index)

        needs_indexing = isinstance(iterable_with_sentences, NARSDataStructures.Table)
        for sentence_from_iterable in iterable_with_sentences:
            if needs_indexing:
                sentence_from_iterable = sentence_from_iterable[0]
            if str(sentence_from_iterable) == sentence_string:  # found clicked sentence
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
                label.grid(row=4, column=0, columnspan=2)

                evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                     width=object_listbox_width, font=('', 8))
                evidential_base_listbox.grid(row=5, column=0, columnspan=2)

                stamp = NALGrammar.Sentence.Stamp = sentence_from_iterable.stamp
                evidential_base_iterator = iter(stamp.evidential_base)
                next(evidential_base_iterator) #skip the first element, which is just the sentence's ID so already displayed
                for sentence in evidential_base_iterator:
                    evidential_base_listbox.insert(tk.END, str(sentence))
                evidential_base_listbox.bind("<<ListboxSelect>>",
                                             lambda event: listbox_sentence_item_click_callback(event,
                                                                                                sentence_from_iterable.stamp.evidential_base))



def listbox_datastructure_item_click_callback(event):
    """
        Presents a window describing the clicked data structure's item's internal data.
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

        if event.widget is NARSGUI.gui_memory_listbox:
            key = item_string[item_string.rfind(Global.Global.ID_END_MARKER) + len(Global.Global.ID_END_MARKER):item_string.find(
                NARSGUI.GUI_BUDGET_SYMBOL) - 1]  # remove ID and priority, concept term string is the key
            data_structure = Global.Global.NARS.memory.concepts_bag
        elif event.widget is NARSGUI.gui_experience_buffer_listbox:
            key = item_string[item_string.find(Global.Global.ITEM_ID_MARKER) + len(
                Global.Global.ITEM_ID_MARKER):item_string.rfind(Global.Global.ID_END_MARKER)]
            data_structure = Global.Global.NARS.experience_task_buffer

        assert key is not None, "Couldn't get key from item click callback"

        item = data_structure.peek(key)
        if item is None:
            NARSGUI.print_to_output("Error - could not get item: " + key)
            return

        object = item.object

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

            label = tk.Label(item_info_window, text="Number of Term Links: ", justify=tk.LEFT)
            label.grid(row=1, column=0)

            label = tk.Label(item_info_window, text=str(object.term_links.count), justify=tk.LEFT)
            label.grid(row=1, column=1)

            label = tk.Label(item_info_window, text="", justify=tk.LEFT)
            label.grid(row=2, column=0)

            # beliefs table listbox
            beliefs_capacity_text = "("+str(len(object.belief_table)) + "/" + str(object.belief_table.capacity)+")"
            label = tk.Label(item_info_window, text="Beliefs " + beliefs_capacity_text, font=('bold'))
            label.grid(row=4, column=0, columnspan=2)


            belief_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            belief_listbox.grid(row=5, column=0, columnspan=2)
            for belief in object.belief_table:
                if isinstance(object.belief_table, NARSDataStructures.Bag):
                    belief_listbox.insert(tk.END, str(belief.object))
                elif isinstance(object.belief_table, NARSDataStructures.Table):
                    belief_listbox.insert(tk.END, str(belief[0]))

            belief_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                        object.belief_table))  # define callback

            # desires table listbox
            desires_capacity_text = "("+str(len(object.desire_table)) + "/" + str(object.desire_table.capacity)+")"
            label = tk.Label(item_info_window, text="Desires " + desires_capacity_text, font=('bold'))
            label.grid(row=4, column=2, columnspan=2)

            desire_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            desire_listbox.grid(row=5, column=2, columnspan=2)
            for desire in object.desire_table:
                desire_listbox.insert(tk.END, str(desire[0]))
            desire_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                        object.desire_table))  # define callback

        elif isinstance(object, NARSDataStructures.Task):
            # Evidential base listbox
            label = tk.Label(item_info_window, text="Sentence: ", justify=tk.LEFT)
            label.grid(row=1, column=0)

            labelClickable = tk.Listbox(item_info_window, height=1)
            labelClickable.insert(tk.END, str(object.sentence))
            labelClickable.grid(row=1, column=1)
            labelClickable.bind("<<ListboxSelect>>",
                                lambda event: listbox_sentence_item_click_callback(event,
                                                                                   [object.sentence]))

            label = tk.Label(item_info_window, text="", justify=tk.LEFT)
            label.grid(row=2, column=0)

            # Evidential base listbox
            label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
            label.grid(row=3, column=0, columnspan=2)

            evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                 width=object_listbox_width, font=('', 8))
            evidential_base_listbox.grid(row=4, column=0, columnspan=2)
            for sentence in object.sentence.stamp.evidential_base:
                evidential_base_listbox.insert(tk.END, str(sentence))
            evidential_base_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                                 object.sentence.stamp.evidential_base))


def toggle_pause(event=None):
    """
        Toggle the global paused parameter
    """
    Global.Global.set_paused(not Global.Global.paused)
