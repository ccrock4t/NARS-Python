import queue
import threading

import Global
import InputBuffer
import tkinter as tk

import NALGrammar
import NARSDataStructures
import NARSMemory

from PIL import Image, ImageTk

"""
    GUI code
    Only use this after Global NARS object has been created.
"""

class NARSGUI:
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None  # delay slider
    gui_total_cycles_lbl = None
    gui_total_cycles_stringvar = None
    gui_play_pause_button = None

    # Internal Data vars
    # listboxes
    gui_experience_buffer_listbox = None  # output for tasks in experience buffer
    gui_memory_listbox = None  # output for concepts in memory bag
    gui_event_buffer_listbox = None # output for tasks in event buffer

    # labels
    gui_event_buffer_output_label = None
    gui_experience_buffer_output_label = None
    gui_concepts_bag_output_label = None
    GUI_BUDGET_SYMBOL = "$"

    # array visualization
    gui_array_image_frame = None

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
        elif data_structure is NARS.event_buffer:
            listbox = cls.gui_event_buffer_listbox
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
            if data_structure is NARS.event_buffer:
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
        elif data_structure is NARS.event_buffer:
            listbox = cls.gui_event_buffer_listbox

        string_list = listbox.get(0, tk.END)
        msg_id = msg[len(Global.Global.MARKER_ITEM_ID):msg.rfind(
            Global.Global.MARKER_ID_END)]  # assuming ID is at the beginning, get characters from ID: to first spacebar
        idx_to_remove = -1
        i = 0
        for row in string_list:
            row_id = row[len(Global.Global.MARKER_ITEM_ID):row.rfind(Global.Global.MARKER_ID_END)]
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
            label_txt = "Memory - Concepts "
            label = cls.gui_concepts_bag_output_label
        elif data_structure is NARS.event_buffer:
            label = cls.gui_event_buffer_output_label

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
            Event buffer internal contents GUI
        """
        cls.gui_event_buffer_output_label = tk.Label(window)
        cls.gui_event_buffer_output_label.grid(row=0, column=0, sticky='w')

        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=1, column=2, sticky='ns')
        cls.gui_event_buffer_listbox = tk.Listbox(window,
                                                  height=listbox_height//3,
                                                  width=listbox_width, font=('', 8),
                                                  yscrollcommand=buffer_scrollbar.set)
        cls.gui_event_buffer_listbox.grid(row=1, column=0, columnspan=1)

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
        cls.update_datastructure_labels(Global.Global.NARS.event_buffer)

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
        cls.gui_total_cycles_stringvar = tk.StringVar()
        cls.gui_total_cycles_stringvar.set("Cycle #0")
        cls.gui_total_cycles_lbl = tk.Label(window, textvariable=cls.gui_total_cycles_stringvar)
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
        for sentence in iterable_with_sentences:
            if needs_indexing:
                sentence = sentence[0]
            if str(sentence) == sentence_string:  # found clicked sentence
                # window
                item_info_window = tk.Toplevel()
                item_info_window.title("Sentence Internal Data: " + str(sentence))
                if sentence.is_array:
                    item_info_window.geometry('1000x500')
                else:
                    item_info_window.geometry('600x500')
                #item_info_window.grab_set()  # lock the other windows until this window is exited

                object_listbox_width = 40
                object_listbox_height = 20

                rownum = 0

                # sentence
                label = tk.Label(item_info_window, text="Sentence: ")
                label.grid(row=rownum, column=0)

                label = tk.Label(item_info_window, text=sentence.get_formatted_string_no_id())
                label.grid(row=rownum, column=1)

                # sentence ID
                rownum += 1
                label = tk.Label(item_info_window, text="Sentence ID: ")
                label.grid(row=rownum, column=0)

                label = tk.Label(item_info_window, text=str(sentence.stamp.id))
                label.grid(row=rownum, column=1)

                # sentence occurrence time
                rownum += 1
                label = tk.Label(item_info_window, text="Occurrence Time: ")
                label.grid(row=rownum, column=0)

                oc_time = sentence.stamp.occurrence_time

                label = tk.Label(item_info_window, text=str("Eternal" if oc_time is None else oc_time))
                label.grid(row=rownum, column=1)

                # sentence type
                rownum += 1
                label = tk.Label(item_info_window, text="Sentence Type: ")
                label.grid(row=rownum, column=0)

                label = tk.Label(item_info_window, text=type(sentence).__name__)
                label.grid(row=rownum, column=1)

                # blank
                rownum += 1
                label = tk.Label(item_info_window, text="")
                label.grid(row=rownum, column=1)

                #Listbox labels
                rownum += 1
                label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
                label.grid(row=rownum, column=0, columnspan=2)

                label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
                label.grid(row=rownum, column=2, columnspan=2)

                # Evidential base listbox
                rownum += 1
                evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                     width=object_listbox_width, font=('', 8))
                evidential_base_listbox.grid(row=rownum, column=0, columnspan=2)

                stamp: NALGrammar.Stamp = sentence.stamp
                evidential_base_iterator = iter(stamp.evidential_base)
                next(evidential_base_iterator) #skip the first element, which is just the sentence's ID so it' already displayed
                for sentence in evidential_base_iterator:
                    evidential_base_listbox.insert(tk.END, str(sentence))
                evidential_base_listbox.bind("<<ListboxSelect>>",
                                             lambda event: listbox_sentence_item_click_callback(event,
                                                                                                sentence.stamp.evidential_base))

                # Interacted sentences listbox
                interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                          width=object_listbox_width, font=('', 8))
                interacted_sentences_listbox.grid(row=rownum, column=2, columnspan=2)
                for sentence in sentence.stamp.interacted_sentences:
                    interacted_sentences_listbox.insert(tk.END, str(sentence))
                interacted_sentences_listbox.bind("<<ListboxSelect>>",
                                                  lambda event: listbox_sentence_item_click_callback(event,
                                                                                                     sentence.stamp.interacted_sentences))

                if isinstance(sentence, NALGrammar.Array) and sentence.is_array and not isinstance(sentence, NALGrammar.Question):
                    # Percept elements label
                    label = tk.Label(item_info_window, text="Array Visualization (scroll to zoom in/out)", font=('bold'))
                    label.grid(row=rownum-1, column=4, columnspan=2)

                    MAX_IMAGE_SIZE = 2000
                    PIXEL_SIZE_PER_ELEMENT = 300 / len(sentence.image_array[0][0])
                    if PIXEL_SIZE_PER_ELEMENT < 1: PIXEL_SIZE_PER_ELEMENT = 1 # minimum size 1 pixel

                    def zoom_image_array(event):
                        # zoom the image array depending on how the user scrolled
                        offset = 1 if event.delta > 0 else -1
                        for child in NARSGUI.gui_array_image_frame.winfo_children():
                            child.config(width=child.winfo_width()+offset, height=child.winfo_height()+offset)

                    image_frame = tk.Frame(item_info_window, width=MAX_IMAGE_SIZE, height=MAX_IMAGE_SIZE, name="array image frame")
                    image_frame.grid(row=rownum, column=4, columnspan=2, rowspan=2)
                    image_frame.bind_all("<MouseWheel>", zoom_image_array)

                    # iterate over each element and draw a pixel for it
                    for z, layer in enumerate(sentence.image_array):
                        for y, row in enumerate(layer):
                            for x, value in enumerate(row):
                                f = tk.Frame(image_frame, width=PIXEL_SIZE_PER_ELEMENT, height=PIXEL_SIZE_PER_ELEMENT)
                                f.grid(row=y,column=x, columnspan=1, rowspan=1)
                                f.rowconfigure(0, weight=1)
                                f.columnconfigure(0, weight=1)
                                f.grid_propagate(0)

                                color = from_rgb_to_tkinter_color((value, value, value))
                                button = tk.Button(f,bg=color)
                                button.config(relief='solid', borderwidth=0)
                                button.grid(sticky = "NWSE")
                                CreateToolTip(button, text=(sentence[(x,y)]))

                    NARSGUI.gui_array_image_frame = image_frame


def from_rgb_to_tkinter_color(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb


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

        if event.widget is NARSGUI.gui_memory_listbox:
            key = item_string[item_string.rfind(Global.Global.MARKER_ID_END) + len(Global.Global.MARKER_ID_END):item_string.find(
                NARSGUI.GUI_BUDGET_SYMBOL) - 1]  # remove ID and priority, concept term string is the key
            data_structure = Global.Global.NARS.memory.concepts_bag
        elif event.widget is NARSGUI.gui_experience_buffer_listbox:
            key = item_string[item_string.find(Global.Global.MARKER_ITEM_ID) + len(
                Global.Global.MARKER_ITEM_ID):item_string.rfind(Global.Global.MARKER_ID_END)]
            data_structure = Global.Global.NARS.experience_task_buffer
        else:
            # clicked concept within another concept
            key = item_string
            data_structure = Global.Global.NARS.memory.concepts_bag

        assert key is not None, "Couldn't get key from item click callback"

        item = data_structure.peek(key)
        if item is None:
            NARSGUI.print_to_output("Error - could not get item: " + key)
            return

        object = item.object
        assert isinstance(object, NARSMemory.Concept) or isinstance(object, NARSDataStructures.Task), "ERROR: Data Structure clickback only defined for Concept and Task"

        # window
        item_info_window = tk.Toplevel()
        item_info_window.title(type(object).__name__ + " Internal Data: " + item_string)
        item_info_window.geometry('750x700')
        #item_info_window.grab_set()  # lock the other windows until this window is exited

        row_num = 0

        # name
        label = tk.Label(item_info_window, text=type(object).__name__ + " Name: ")
        label.grid(row=row_num, column=0)

        label = tk.Label(item_info_window, text=str(object))
        label.grid(row=row_num, column=1)

        # term type
        row_num += 1
        label = tk.Label(item_info_window, text="Term Type: ")
        label.grid(row=row_num, column=0)

        label = tk.Label(item_info_window, text=type(object.get_term()).__name__)
        label.grid(row=row_num, column=1)

        object_listbox_width = 40
        object_listbox_height = 20

        row_num += 1
        if isinstance(object, NARSMemory.Concept):
            label = tk.Label(item_info_window, text="", justify=tk.LEFT)
            label.grid(row=row_num, column=0)

            # Row 1 Listbox labels
            beliefs_capacity_text = "("+str(len(object.belief_table)) + "/" + str(object.belief_table.capacity)+")"
            label = tk.Label(item_info_window, text="Beliefs " + beliefs_capacity_text, font=('bold'))
            row_num += 2
            label.grid(row=row_num, column=0, columnspan=2)

            desires_capacity_text = "("+str(len(object.desire_table)) + "/" + str(object.desire_table.capacity)+")"
            label = tk.Label(item_info_window, text="Desires " + desires_capacity_text, font=('bold'))
            label.grid(row=row_num, column=2, columnspan=2)

            term_links_text = "(" + str(object.term_links.count) + ")"
            label = tk.Label(item_info_window, text="Term Links " + term_links_text, font=('bold'))
            label.grid(row=row_num, column=4, columnspan=2)

            # beliefs table listbox
            belief_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            row_num += 1
            belief_listbox.grid(row=row_num, column=0, columnspan=2)
            for belief in object.belief_table:
                if isinstance(object.belief_table, NARSDataStructures.Bag):
                    belief_listbox.insert(tk.END, str(belief.object))
                elif isinstance(object.belief_table, NARSDataStructures.Table):
                    belief_listbox.insert(tk.END, str(belief[0]))

            belief_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                        object.belief_table))  # define callbac
            # desires table listbox
            desire_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            desire_listbox.grid(row=row_num, column=2, columnspan=2)
            for desire in object.desire_table:
                desire_listbox.insert(tk.END, str(desire[0]))
            desire_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                        object.desire_table))  # define callback
            # Term Links listbox
            termlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            termlinks_listbox.grid(row=row_num, column=4, columnspan=2)
            for concept_item in object.term_links:
                termlinks_listbox.insert(tk.END, str(concept_item.object))
            termlinks_listbox.bind("<<ListboxSelect>>", lambda event: listbox_datastructure_item_click_callback(event))

            row_num += 1

            # Row 2 Listbox labels
            # Prediction Links listbox
            prediction_links_text = "(" + str(object.prediction_links.count) + ")"
            label = tk.Label(item_info_window, text="Prediction Links " + prediction_links_text, font=('bold'))
            label.grid(row=row_num, column=0, columnspan=2)

            explanation_links_text = "(" + str(object.explanation_links.count) + ")"
            label = tk.Label(item_info_window, text="Explanation Links " + explanation_links_text, font=('bold'))
            label.grid(row=row_num, column=2, columnspan=2)

            row_num += 1

            # Prediction Links Listbox
            predictionlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height, width=object_listbox_width,
                                        font=('', 8))
            predictionlinks_listbox.grid(row=row_num, column=0, columnspan=2)
            for concept_item in object.prediction_links:
                predictionlinks_listbox.insert(tk.END, str(concept_item.object))
            predictionlinks_listbox.bind("<<ListboxSelect>>", lambda event: listbox_datastructure_item_click_callback(event))

            # Explanation Links Listbox
            explanationlinks_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                 width=object_listbox_width,
                                                 font=('', 8))
            explanationlinks_listbox.grid(row=row_num, column=2, columnspan=2)
            for concept_item in object.explanation_links:
                explanationlinks_listbox.insert(tk.END, str(concept_item.object))
            explanationlinks_listbox.bind("<<ListboxSelect>>",
                                         lambda event: listbox_datastructure_item_click_callback(event))


        elif isinstance(object, NARSDataStructures.Task):
            # Evidential base listbox
            label = tk.Label(item_info_window, text="Sentence: ", justify=tk.LEFT)
            label.grid(row=row_num, column=0)

            labelClickable = tk.Listbox(item_info_window, height=1)
            labelClickable.insert(tk.END, str(object.sentence))
            labelClickable.grid(row=row_num, column=1)
            labelClickable.bind("<<ListboxSelect>>",
                                lambda event: listbox_sentence_item_click_callback(event,
                                                                                   [object.sentence]))

            row_num += 1
            label = tk.Label(item_info_window, text="", justify=tk.LEFT)
            label.grid(row=row_num, column=0)

            # Listbox labels
            row_num += 1

            label = tk.Label(item_info_window, text="Sentence Evidential Base", font=('bold'))
            label.grid(row=row_num, column=0, columnspan=2)

            label = tk.Label(item_info_window, text="Sentence Interacted Sentences", font=('bold'))
            label.grid(row=row_num, column=2, columnspan=2)

            # Evidential base listbox
            row_num += 1
            evidential_base_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                 width=object_listbox_width, font=('', 8))
            evidential_base_listbox.grid(row=row_num, column=0, columnspan=2)
            for sentence in object.sentence.stamp.evidential_base:
                evidential_base_listbox.insert(tk.END, str(sentence))
            evidential_base_listbox.bind("<<ListboxSelect>>", lambda event: listbox_sentence_item_click_callback(event,
                                                                                                                 object.sentence.stamp.evidential_base))
            # Interacted sentences listbox
            interacted_sentences_listbox = tk.Listbox(item_info_window, height=object_listbox_height,
                                                      width=object_listbox_width, font=('', 8))
            interacted_sentences_listbox.grid(row=row_num, column=2, columnspan=2)
            for sentence in object.sentence.stamp.interacted_sentences:
                interacted_sentences_listbox.insert(tk.END, str(sentence))
            interacted_sentences_listbox.bind("<<ListboxSelect>>",
                                              lambda event: listbox_sentence_item_click_callback(event,
                                                                                                 object.sentence.stamp.interacted_sentences))



def toggle_pause(event=None):
    """
        Toggle the global paused parameter
    """
    Global.Global.set_paused(not Global.Global.paused)



# from https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)