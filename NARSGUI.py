
import Config
import NALSyntax
import NARSDataStructures
import NARSMemory
import NALInferenceRules

from PIL import Image, ImageTk, ImageOps

import Global
import tkinter as tk
import numpy as np
"""
    GUI code
    Runs on its own separate process, and communicate with the NARS process using commands.
"""

class NARSGUI:
    # Interface vars
    gui_output_textbox = None  # primary output gui
    gui_delay_slider = None  # delay slider
    gui_total_cycles_lbl = None
    gui_total_cycles_stringvar = None
    gui_play_pause_button = None
    gui_show_non_statement_concepts = False

    # Internal Data vars
    # listboxes
    gui_global_buffer_listbox = None  # output for tasks in global buffer
    gui_memory_listbox = None  # output for concepts in memory bag
    gui_event_buffer_listbox = None # output for tasks in event buffer

    # arrays
    gui_global_buffer_full_contents = []
    gui_memory_full_contents = []
    gui_event_buffer_listbox_full_contents = []

    # labels
    gui_event_buffer_output_label = None
    gui_global_buffer_output_label = None
    gui_concepts_bag_output_label = None

    # dictionary of data structure name to listbox
    dict_listbox_from_id = {}
    gui_object_pipe = None # two-way object request communication
    gui_string_pipe = None # one way string communication

    # copied variables from Global
    gui_use_interface = None
    gui_use_internal_data = None

    # Keys
    KEY_STRING = "String"
    KEY_TRUTH_VALUE = "TruthValue"
    KEY_TIME_PROJECTED_TRUTH_VALUE = "TimeProjectedTruthValue"
    KEY_IS_ARRAY = "IsArray"
    KEY_STRING_NOID = "StringNoID"
    KEY_ID = "ID"
    KEY_OCCURRENCE_TIME = "OccurrenceTime"
    KEY_SENTENCE_TYPE = "SentenceType"
    KEY_DERIVED_BY = "DerivedBy"
    KEY_PARENT_PREMISES = "ParentPremises"
    KEY_LIST_EVIDENTIAL_BASE = "ListEvidentialBase"
    KEY_LIST_INTERACTED_SENTENCES = "ListInteractedSentences"
    KEY_ARRAY_IMAGE = "ArrayImage"
    KEY_ARRAY_ALPHA_IMAGE = "ArrayAlphaImage"
    KEY_ARRAY_ELEMENT_STRINGS = "ArrayElementStrings"

    KEY_KEY = "Key"
    KEY_CLASS_NAME = "ClassName"
    KEY_OBJECT_STRING = "ObjectString"
    KEY_TERM_TYPE = "TermType"
    KEY_LIST_BELIEFS = "ListBeliefs"
    KEY_LIST_DESIRES = "ListDesires"
    KEY_LIST_TERM_LINKS = "ListTermLinks"
    KEY_LIST_PREDICTION_LINKS = "ListPredictionLinks"
    KEY_LIST_EXPLANATION_LINKS = "ListExplanationLinks"
    KEY_CAPACITY_BELIEFS = "CapacityBeliefs"
    KEY_CAPACITY_DESIRES = "CapacityDesires"

    KEY_CAPACITY_TERM_LINKS = "CapacityTermLinks"
    KEY_CAPACITY_PREDICTION_LINKS = "CapacityPredictionLinks"
    KEY_CAPACITY_EXPLANATION_LINKS = "CapacityExplanationLinks"
    KEY_SENTENCE_STRING = "SentenceString"

    def __init__(self):
        pass

    def print_to_output(self, msg, data_structure_info=None, length=0):
        """
             Print a message to an output GUI box
         """
        listbox = None
        if data_structure_info is not None and data_structure_info[0] in self.dict_listbox_from_id:
            data_structure_id, data_structure_name = data_structure_info
            listbox = self.dict_listbox_from_id[data_structure_id]
        elif data_structure_info is None:
            # output to interface or shell
            if self.gui_use_interface:
                self.gui_output_textbox.insert(tk.END, msg + "\n")
            print(msg,flush=True)

        if listbox is None: return
        # internal data output
        # insert item sorted by priority
        if self.gui_use_internal_data:
            if listbox is self.gui_event_buffer_listbox:
                idx_to_insert = tk.END
            else:
                string_list = listbox.get(0, tk.END)  # get all items in the listbox
                msg_priority = msg[msg.find(NALSyntax.StatementSyntax.BudgetMarker.value) + 1:msg.rfind(
                    NALSyntax.StatementSyntax.BudgetMarker.value)]
                idx_to_insert = tk.END  # by default insert at the end
                i = 0
                for row in string_list:
                    row_priority = row[row.find(NALSyntax.StatementSyntax.BudgetMarker.value) + 1:row.rfind(
                        NALSyntax.StatementSyntax.BudgetMarker.value)]
                    if float(msg_priority) > float(row_priority):
                        idx_to_insert = i
                        break
                    i += 1


            if listbox is self.gui_global_buffer_listbox:
                self.gui_global_buffer_full_contents.insert(len(self.gui_global_buffer_full_contents) if idx_to_insert == tk.END else idx_to_insert, msg)
                listbox.insert(idx_to_insert, msg)
            elif listbox is self.gui_memory_listbox:
                self.gui_memory_full_contents.insert(len(self.gui_memory_full_contents) if idx_to_insert == tk.END else idx_to_insert, msg)
                is_statement = NALSyntax.Copula.contains_top_level_copula(msg)
                if (is_statement) or (not is_statement and self.gui_show_non_statement_concepts):
                    listbox.insert(idx_to_insert, msg)
            elif listbox is self.gui_event_buffer_listbox:
                self.gui_event_buffer_listbox_full_contents.insert(len(self.gui_event_buffer_listbox_full_contents) if idx_to_insert == tk.END else idx_to_insert, msg)
                listbox.insert(idx_to_insert, msg)

            self.update_datastructure_labels(data_structure_info, length=length)

    def remove_from_output(self, msg, data_structure_info=None, length=0):
        """
            Remove a message from an output GUI box
        """

        if data_structure_info is not None and data_structure_info[0] in self.dict_listbox_from_id:
            data_structure_id, data_structure_name = data_structure_info
            listbox = self.dict_listbox_from_id[data_structure_id]
        else:
            assert False,'ERROR: Data structure name invalid ' + str(data_structure_info)

        msg_id = msg[len(Global.Global.MARKER_ITEM_ID):msg.rfind(
            Global.Global.MARKER_ID_END)]  # assuming ID is at the beginning, get characters from ID: to first spacebar

        if listbox is self.gui_memory_listbox:
            # if memory listbox, non-statement concept
            # remove it from memory contents
            i = 0
            for row in self.gui_memory_full_contents:
                row_id = row[len(Global.Global.MARKER_ITEM_ID):row.rfind(Global.Global.MARKER_ID_END)]
                if msg_id == row_id:
                    break
                i = i + 1
            del self.gui_memory_full_contents[i]

        # if non-statement and not showing non-statements, don't bother trying to remove it from GUI output
        if not NALSyntax.Copula.contains_top_level_copula(msg) and not self.gui_show_non_statement_concepts: return

        string_list = listbox.get(0, tk.END)
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

        contents = None
        if listbox is self.gui_global_buffer_listbox:
            contents = self.gui_global_buffer_full_contents
        elif listbox is self.gui_memory_listbox:
            contents = None # already removed at beginning of function
        elif listbox is self.gui_event_buffer_listbox:
            contents = self.gui_event_buffer_listbox_full_contents

        if contents is not None: contents.pop(idx_to_remove)

        self.update_datastructure_labels(data_structure_info, length=length)

    def update_datastructure_labels(self, data_structure_info, length=0):
        assert data_structure_info is not None, "Cannot update label for Null data structure!"
        data_structure_id, data_structure_name = data_structure_info
        label_txt = ""
        label = None

        listbox = self.dict_listbox_from_id[data_structure_id]
        if listbox is self.gui_global_buffer_listbox:
            label_txt = "Global Task "
            label = self.gui_global_buffer_output_label
        elif listbox is self.gui_memory_listbox:
            label_txt = "Memory - Concepts "
            label = self.gui_concepts_bag_output_label
        elif listbox is self.gui_event_buffer_listbox:
            label = self.gui_event_buffer_output_label

        if label is None: return
        label.config(
            text=(label_txt + data_structure_name + ": " + str(length) + " / " + str(
                self.dict_listbox_from_id[data_structure_id + "capacity"])))

    def clear_listbox(self, listbox=None):
        listbox.delete(0, tk.END)

    def toggle_show_non_statement_concepts(self):
        """
            Toggles showing atomic concepts in the memory listbox
        :return:
        """
        self.gui_show_non_statement_concepts = not self.gui_show_non_statement_concepts
        self.clear_listbox(self.gui_memory_listbox)
        if self.gui_show_non_statement_concepts:
            for concept_string in self.gui_memory_full_contents:
                self.gui_memory_listbox.insert(tk.END, concept_string)
        else:
            self.clear_listbox(self.gui_memory_listbox)
            for concept_string in self.gui_memory_full_contents:
                if NALSyntax.Copula.contains_top_level_copula(concept_string):
                    self.gui_memory_listbox.insert(tk.END, concept_string)


    def execute_gui(self, gui_use_interface, gui_use_internal_data, data_structure_IDs, data_structure_capacities, pipe_gui_objects, pipe_gui_strings):
        """
            Setup and run 2 windows on a single thread
        """
        internal_data_dimensions = "1250x500"
        self.gui_object_pipe = pipe_gui_objects
        self.gui_string_pipe = pipe_gui_strings
        self.gui_use_interface = gui_use_interface
        self.gui_use_internal_data = gui_use_internal_data

        if self.gui_use_interface:
            # launch internal data GUI
            window = tk.Tk()
            window.title("NARS in Python - Interface")
            window.geometry('750x500')
            self.execute_interface_gui(window)

            if self.gui_use_internal_data:
                # launch GUI
                toplevel = tk.Toplevel()
                toplevel.title("NARS in Python - Internal Data")
                toplevel.geometry(internal_data_dimensions)
                self.execute_internal_gui(toplevel, data_structure_IDs, data_structure_capacities)
        elif not self.gui_use_interface and self.gui_use_internal_data:
            # launch GUI
            window = tk.Tk()
            window.title("NARS in Python - Internal Data")
            window.geometry(internal_data_dimensions)
            self.execute_internal_gui(window)

        # main GUI loop
        def handle_pipes(self):
            while self.gui_string_pipe.poll():  # check if there are messages to be received
                (command, msg, data_structure_info, data_structure_length) = self.gui_string_pipe.recv()
                if command == "print":
                    self.print_to_output(msg=msg, data_structure_info=data_structure_info, length=data_structure_length)
                elif command == "remove":
                    self.remove_from_output(msg=msg, data_structure_info=data_structure_info, length=data_structure_length)
                elif command == "clear":
                    self.clear_listbox(data_structure_id=data_structure_info)
                elif command == "paused":
                    self.set_paused(msg)
                elif command == "cycles":
                    self.gui_total_cycles_stringvar.set(msg)

            window.after(1, handle_pipes,self)

        window.after(1, handle_pipes,self)
        pipe_gui_objects.send('ready')
        window.mainloop()


    def set_paused(self, paused):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        if not self.gui_use_interface: return
        self.paused = paused
        if self.paused:
            self.gui_play_pause_button.config(text="PLAY")
        else:
            self.gui_play_pause_button.config(text="PAUSE")

    def toggle_paused(self):
        """
            Sets the Global paused parameter and changes the GUI button

            Does nothing if GUI is not enabled
        """
        self.set_paused(not self.paused)
        self.gui_string_pipe.send(("paused", self.paused))

    def execute_internal_gui(self, window, data_structure_IDs, data_structure_capacities):
        """
            Setup the internal GUI window, displaying the system's buffers and memory
        """
        listbox_height = 30
        listbox_width = 80

        ((global_task_buffer_ID,_), (event_buffer_ID,_), (memory_bag_ID,_)) = data_structure_IDs
        """
            Event buffer internal contents GUI
        """
        row = 0
        self.gui_event_buffer_output_label = tk.Label(window)
        self.gui_event_buffer_output_label.grid(row=row, column=0, sticky='w')

        row += 1
        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=row, column=2, sticky='ns')
        self.gui_event_buffer_listbox = tk.Listbox(window,
                                                  height=listbox_height//3,
                                                  width=listbox_width, font=('', 8),
                                                  yscrollcommand=buffer_scrollbar.set)
        self.gui_event_buffer_listbox.grid(row=row, column=0, columnspan=1)
        self.dict_listbox_from_id[event_buffer_ID] = self.gui_event_buffer_listbox

        """
            Global Buffer internal contents GUI
        """
        row += 1
        self.gui_global_buffer_output_label = tk.Label(window)
        self.gui_global_buffer_output_label.grid(row=row, column=0, sticky='w')

        row += 1
        buffer_scrollbar = tk.Scrollbar(window)
        buffer_scrollbar.grid(row=row , column=2, sticky='ns')
        self.gui_global_buffer_listbox = tk.Listbox(window,
                                                    height=2*listbox_height//3,
                                                    width=listbox_width, font=('', 8),
                                                    yscrollcommand=buffer_scrollbar.set)
        self.gui_global_buffer_listbox.grid(row=row , column=0, columnspan=1)
        self.dict_listbox_from_id[global_task_buffer_ID] = self.gui_global_buffer_listbox

        """
            Memory internal contents GUI
        """
        row = 0
        self.gui_concepts_bag_output_label = tk.Label(window)
        self.gui_concepts_bag_output_label.grid(row=row,
                                                column=3,
                                                sticky='w')

        row += 1
        concept_bag_scrollbar = tk.Scrollbar(window)
        concept_bag_scrollbar.grid(row=row,
                                   column=5,
                                   rowspan=4,
                                   sticky='ns')
        self.gui_memory_listbox = tk.Listbox(window,
                                            height=listbox_height,
                                            width=listbox_width,
                                            font=('', 8),
                                            yscrollcommand=concept_bag_scrollbar.set)
        self.gui_memory_listbox.grid(row=row,
                                    column=3,
                                    columnspan=1,
                                    rowspan=4)
        self.dict_listbox_from_id[memory_bag_ID] = self.gui_memory_listbox

        checkbutton = tk.Checkbutton(window, text='Show non-statement concepts', onvalue=1,
                                     offvalue=0, command=self.toggle_show_non_statement_concepts)
        checkbutton.grid(row=row, column=6)

        # define callbacks when clicking items in any box
        self.gui_memory_listbox.bind("<<ListboxSelect>>", self.listbox_datastructure_item_click_callback)
        self.gui_global_buffer_listbox.bind("<<ListboxSelect>>", self.listbox_datastructure_item_click_callback)

        for i,(id,name) in enumerate(data_structure_IDs):
            self.dict_listbox_from_id[id + "capacity"] = data_structure_capacities[i]
            if i == len(data_structure_IDs) - 1:
                # final name is the memory
                length = 1 # system starts with self concept
            else:
                length = 0
            self.update_datastructure_labels((id,name),length)


    def execute_interface_gui(self,window):
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

        self.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
        self.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

        # row 2
        self.gui_total_cycles_stringvar = tk.StringVar()
        self.gui_total_cycles_stringvar.set("Cycle #0")
        self.gui_total_cycles_lbl = tk.Label(window, textvariable=self.gui_total_cycles_stringvar)
        self.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

        speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
        speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

        self.gui_play_pause_button = tk.Button(window, text="", command=self.toggle_paused)
        self.gui_play_pause_button.grid(row=3, column=4, sticky='s')

        max_delay = 1000  # in milliseconds
        gui_delay_slider = tk.Scale(window, from_=max_delay, to=1)
        self.gui_delay_slider = gui_delay_slider
        self.gui_delay_slider.grid(row=3, column=5, sticky='ns')

        strings_pipe = self.gui_string_pipe

        def delay_slider_changed(event=None):
            strings_pipe.send(("delay", gui_delay_slider.get() / 1000))

        self.gui_delay_slider.bind('<ButtonRelease-1>',delay_slider_changed)
        self.gui_delay_slider.set(max_delay)
        delay_slider_changed() # set delay to max value


        # input GUI
        def input_clicked(event=None):
            """
                Callback when clicking button to send input
            """
            # put input into NARS input buffer
            userinput = input_field.get(index1=1.0, index2=tk.END)
            strings_pipe.send(("userinput", userinput)) # send user input to NARS
            input_field.delete(1.0, tk.END) # empty input field

        input_lbl = tk.Label(window, text="Input: ")
        input_lbl.grid(column=0, row=4)

        input_field = tk.Text(window, width=50, height=4)
        input_field.grid(column=1, row=4)
        input_field.focus()

        send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)  # send input when click button
        send_input_btn.grid(column=2, row=4)

        window.focus()

    def listbox_sentence_item_click_callback(self,event):
        selection = event.widget.curselection()

        if selection:
            index = selection[0]
            sentence_string = event.widget.get(index)
            self.gui_object_pipe.send(("getsentence", sentence_string, None))
            sentence = self.gui_object_pipe.recv()
            if sentence is not None:
                self.draw_sentence_internal_data(sentence)

    def listbox_concept_item_click_callback(self,event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            concept_term_string = event.widget.get(index)
            self.gui_object_pipe.send(("getconcept", concept_term_string, None))
            concept_item = self.gui_object_pipe.recv()
            if concept_item is not None:
                self.draw_concept_internal_data(concept_item,concept_term_string)

    def listbox_datastructure_item_click_callback(self,event):
        """
            Presents a window describing the clicked data structure's item's internal data.
            Locks the interface until the window is closed.

            This function is called when the user clicks on an item in the internal data.
        """
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            item_string = event.widget.get(index)

            data_structure_name = ""
            if event.widget is self.gui_memory_listbox:
                ID = item_string[item_string.rfind(Global.Global.MARKER_ID_END) + len(Global.Global.MARKER_ID_END):item_string.find(
                    NALSyntax.StatementSyntax.BudgetMarker.value) - 1]  # remove ID and priority, concept term string is the key
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_memory_listbox)
            elif event.widget is self.gui_global_buffer_listbox:
                ID = item_string[item_string.find(Global.Global.MARKER_ITEM_ID) + len(
                    Global.Global.MARKER_ITEM_ID):item_string.rfind(Global.Global.MARKER_ID_END)]
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_global_buffer_listbox)
                ID = int(ID)
            else:
                # clicked concept within another concept
                ID = item_string
                data_structure_name = self.get_data_structure_name_from_listbox(self.gui_memory_listbox)
            self.gui_object_pipe.send(("getitem", ID, data_structure_name))
            item = self.gui_object_pipe.recv()

            if item is None:
                self.print_to_output("ERROR: could not get item with key: " + ID)
                return

            classname = item[NARSGUI.KEY_CLASS_NAME]
            assert classname == NARSMemory.Concept.__name__ or classname == NARSDataStructures.Other.Task.__name__, "ERROR: Data Structure clickback only defined for Concept and Task"

            if classname == NARSMemory.Concept.__name__:
                self.draw_concept_internal_data(item,item_string)
            elif classname == NARSDataStructures.Other.Task.__name__:
                # window
                item_info_window = tk.Toplevel()
                item_info_window.title(classname + " Internal Data: " + item_string)
                item_info_window.geometry('1100x700')
                # item_info_window.grab_set()  # lock the other windows until this window is exited

                row = 0
                column = 0

                # name
                create_key_item_label(parent=item_info_window,
                                      row=row,
                                      column=column,
                                      key_label=classname + " Name: ",
                                      value_label=item[NARSGUI.KEY_OBJECT_STRING])

                # term type
                row += 1
                create_key_item_label(parent=item_info_window,
                                      row=row,
                                      column=column,
                                      key_label="Term Type: ",
                                      value_label=item[NARSGUI.KEY_TERM_TYPE])

                row += 1
                create_key_item_label(parent=item_info_window,
                                      row=row,
                                      column=0,
                                      key_label="Sentence: ",
                                      value_label=item[NARSGUI.KEY_SENTENCE_STRING])

                row += 1
                label = tk.Label(item_info_window, text="", justify=tk.LEFT)
                label.grid(row=row, column=column)

                # Listboxes
                row += 1
                # Evidential base listbox
                create_clickable_listbox(parent=item_info_window,
                                         row=row,
                                         column=column,
                                         title_label="Sentence Evidential Base",
                                         listbox_contents=item[NARSGUI.KEY_LIST_EVIDENTIAL_BASE],
                                         content_click_callback=self.listbox_sentence_item_click_callback)

                # Interacted sentences listbox
                column += 2
                create_clickable_listbox(parent=item_info_window,
                                         row=row,
                                         column=column,
                                         title_label="Sentence Interacted Sentences",
                                         listbox_contents=item[NARSGUI.KEY_LIST_INTERACTED_SENTENCES],
                                         content_click_callback=self.listbox_sentence_item_click_callback)


    def draw_concept_internal_data(self, item, item_string):
        # window
        classname = item[NARSGUI.KEY_CLASS_NAME]
        item_info_window = tk.Toplevel()
        item_info_window.title(classname + "Internal Data: " + item_string)
        item_info_window.geometry('1100x700')
        # item_info_window.grab_set()  # lock the other windows until this window is exited

        row = 0
        column = 0

        # name
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label=classname + " Name: ",
                              value_label=item[NARSGUI.KEY_OBJECT_STRING])

        # term type
        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Term Type: ",
                              value_label=item[NARSGUI.KEY_TERM_TYPE])

        row += 1
        if classname == NARSMemory.Concept.__name__:
            label = tk.Label(item_info_window, text="", justify=tk.LEFT)
            label.grid(row=row, column=column)

            # Row 1
            # beliefs table listbox
            row += 1
            beliefs_capacity_text = "Beliefs (" + str(len(item[NARSGUI.KEY_LIST_BELIEFS])) + "/" + item[
                NARSGUI.KEY_CAPACITY_BELIEFS] + ")"
            create_clickable_listbox(parent=item_info_window,
                                     row=row,
                                     column=column,
                                     title_label=beliefs_capacity_text,
                                     listbox_contents=item[NARSGUI.KEY_LIST_BELIEFS],
                                     content_click_callback=self.listbox_sentence_item_click_callback)

            # desires table listbox
            column += 2
            desires_capacity_text = "Desires (" + str(len(item[NARSGUI.KEY_LIST_DESIRES])) + "/" + item[
                NARSGUI.KEY_CAPACITY_DESIRES] + ")"
            create_clickable_listbox(parent=item_info_window,
                                     row=row,
                                     column=column,
                                     title_label=desires_capacity_text,
                                     listbox_contents=item[NARSGUI.KEY_LIST_DESIRES],
                                     content_click_callback=self.listbox_sentence_item_click_callback)

            # Term Links listbox
            column += 2
            term_links_text = "Term Links (" + str(len(item[NARSGUI.KEY_LIST_TERM_LINKS])) + ")"
            create_clickable_listbox(parent=item_info_window,
                                     row=row,
                                     column=column,
                                     title_label=term_links_text,
                                     listbox_contents=item[NARSGUI.KEY_LIST_TERM_LINKS],
                                     content_click_callback=self.listbox_concept_item_click_callback)

            # Next row
            column = 0
            row += 2

            # Prediction Links Listbox
            prediction_links_text = "Prediction Links (" + str(len(item[NARSGUI.KEY_LIST_PREDICTION_LINKS])) + ")"
            create_clickable_listbox(parent=item_info_window,
                                     row=row,
                                     column=column,
                                     title_label=prediction_links_text,
                                     listbox_contents=item[NARSGUI.KEY_LIST_PREDICTION_LINKS],
                                     content_click_callback=self.listbox_concept_item_click_callback)

            # Explanation Links Listbox
            column += 2
            explanation_links_text = "Explanation Links (" + str(len(item[NARSGUI.KEY_LIST_EXPLANATION_LINKS])) + ")"
            create_clickable_listbox(parent=item_info_window,
                                     row=row,
                                     column=column,
                                     title_label=explanation_links_text,
                                     listbox_contents=item[NARSGUI.KEY_LIST_EXPLANATION_LINKS],
                                     content_click_callback=self.listbox_concept_item_click_callback)

    def draw_sentence_internal_data(self, sentence_to_draw):
        item_info_window = tk.Toplevel()
        item_info_window.title("Sentence Internal Data: " + sentence_to_draw[NARSGUI.KEY_STRING])
        is_array = sentence_to_draw[NARSGUI.KEY_IS_ARRAY]
        if is_array:
            item_info_window.geometry('1300x500')
        else:
            item_info_window.geometry('1000x500')

        row = 0
        column = 0

        # sentence
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Sentence: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_STRING_NOID])

        # sentence ID
        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Sentence ID: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_ID])
        # original truth value
        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Truth Value: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_TRUTH_VALUE])

        # sentence occurrence time
        row += 1
        oc_time = sentence_to_draw[NARSGUI.KEY_OCCURRENCE_TIME]
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Occurrence Time: ",
                              value_label=str("Eternal" if oc_time is None else oc_time))

        if oc_time is not None:
            create_key_item_label(parent=item_info_window,
                                  row=row,
                                  column=column,
                                  key_label="Time projected Truth Value: ",
                                  value_label=sentence_to_draw[NARSGUI.KEY_TIME_PROJECTED_TRUTH_VALUE])

        # sentence type
        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Sentence Type: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_SENTENCE_TYPE])

        # sentence type
        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Derived By: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_DERIVED_BY])

        row += 1
        create_key_item_label(parent=item_info_window,
                              row=row,
                              column=column,
                              key_label="Parent Premises: ",
                              value_label=sentence_to_draw[NARSGUI.KEY_PARENT_PREMISES])

        # blank
        row += 1
        label = tk.Label(item_info_window, text="")
        label.grid(row=row, column=1)

        # Listboxes
        row += 1

        # Evidential base listbox
        create_clickable_listbox(parent=item_info_window,
                                 row=row,
                                 column=column,
                                 title_label="Sentence Evidential Base",
                                 listbox_contents=sentence_to_draw[NARSGUI.KEY_LIST_EVIDENTIAL_BASE],
                                 content_click_callback=self.listbox_sentence_item_click_callback)

        # Interacted sentences listbox
        column += 2
        create_clickable_listbox(parent=item_info_window,
                                 row=row,
                                 column=column,
                                 title_label="Sentence Interacted Sentences",
                                 listbox_contents=sentence_to_draw[NARSGUI.KEY_LIST_INTERACTED_SENTENCES],
                                 content_click_callback=self.listbox_sentence_item_click_callback)


        MAX_IMAGE_SIZE = 2000
        image_array = sentence_to_draw[NARSGUI.KEY_ARRAY_IMAGE]
        image_alpha_array = sentence_to_draw[NARSGUI.KEY_ARRAY_ALPHA_IMAGE]
        if is_array and image_array is not None:
            column += 2

            # set image defaults
            gui_array_image_dimensions = [300, 300]
            gui_array_use_confidence_opacity = [True]

            # Percept elements label
            label = tk.Label(item_info_window, text="Array Visualization (scroll to zoom in/out)", font=('bold'))
            label.grid(row=row, column=column, columnspan=2)

            if not Config.ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS:
                """
                    Array - Draw entire image (faster)
                """

                # create image frame
                image_frame = tk.Frame(item_info_window, width=MAX_IMAGE_SIZE, height=MAX_IMAGE_SIZE,
                                       name="array image frame")
                image_frame.grid(row=row + 1, column=column, columnspan=2, rowspan=2)

                # create image container
                img_container = tk.Label(image_frame, image=None)
                img_container.grid(row=row + 1, column=column, columnspan=2, rowspan=2)

                def zoom_image_array(event):
                    # zoom the image array depending on how the user scrolled
                    if event is None:
                        offset = 0  # initialize
                    else:
                        offset = 3 if event.delta > 0 else -3
                    pil_image = Image.fromarray(np.swapaxes(image_array,axis1=0,axis2=1))
                    #pil_image = ImageOps.flip(pil_image).rotate(angle=90)
                    if gui_array_use_confidence_opacity[0]:
                        pil_alpha = Image.fromarray(image_alpha_array,mode="L")
                        pil_image.putalpha(pil_alpha)
                        pil_image = pil_image.convert(mode="RGBA")

                    gui_array_image_dimensions[0] += offset
                    if gui_array_image_dimensions[0] < 1: gui_array_image_dimensions[0] = 1
                    gui_array_image_dimensions[1] += offset
                    if gui_array_image_dimensions[1] < 1: gui_array_image_dimensions[1] = 1
                    pil_image = pil_image.resize(gui_array_image_dimensions, resample=Image.NEAREST)
                    render = ImageTk.PhotoImage(pil_image)
                    img_container.config(image=render)
                    img_container.image = render

                image_frame.bind_all("<MouseWheel>", zoom_image_array)
                zoom_image_array(None)
            else:
                """
                    Array - Draw Individual Cells (slower)
                """
                PIXELS_PER_ELEMENT = [int(300 / image_array.shape[0])] # use an array to keep a pointer of the integer
                if PIXELS_PER_ELEMENT[0] < 1: PIXELS_PER_ELEMENT[0] = 1  # minimum size 1 pixel

                def create_array_element_click_lambda(sentence):
                    return None #lambda: self.draw_sentence_internal_data(sentence) #todo

                image_frame = [None]
                def create_image_array():
                    if image_frame[0] is not None:
                        image_frame[0].destroy()

                    image_frame[0] = tk.Frame(item_info_window, width=MAX_IMAGE_SIZE, height=MAX_IMAGE_SIZE,
                                           name="array image frame")
                    image_frame[0].grid(row=row, column=column, columnspan=2, rowspan=2)

                    image_frame[0].bind_all("<MouseWheel>", zoom_image_array)

                    # iterate over each element and draw a pixel for it
                    if len(image_array.shape) == 2:
                        for (x, y), pixel_value in np.ndenumerate(image_array):
                            f = tk.Frame(image_frame[0], width=PIXELS_PER_ELEMENT[0],
                                         height=PIXELS_PER_ELEMENT[0])
                            f.grid(row=y, column=x, columnspan=1, rowspan=1)
                            f.rowconfigure(0, weight=1)
                            f.columnconfigure(0, weight=1)
                            f.grid_propagate(0)

                            element_string = sentence_to_draw[NARSGUI.KEY_ARRAY_ELEMENT_STRINGS][x, y]
                            img_array = np.array([
                                [
                                    [
                                        [pixel_value]
                                    ]
                                ],
                                [
                                    [
                                        [pixel_value]
                                    ]
                                ],
                                [
                                    [
                                        [pixel_value]
                                    ]
                                ],
                                [
                                    [
                                        [image_alpha_array[(x, y)]]
                                    ]
                                ]
                            ])

                            img_array = img_array.T
                            img = Image.fromarray(img_array, mode="RGBA")
                            if not gui_array_use_confidence_opacity[0]:
                                img = img.convert(mode="RGB")

                            img = img.resize((PIXELS_PER_ELEMENT[0], PIXELS_PER_ELEMENT[0]), Image.NEAREST)
                            button = tk.Button(f,
                                               command=create_array_element_click_lambda(element_string))
                            render = ImageTk.PhotoImage(img)
                            button.config(image=render)
                            button.image = render
                            button.config(relief='solid', borderwidth=0)
                            button.grid(sticky="NWSE")
                            CreateToolTip(button, text=(element_string))

                    if len(image_array.shape) == 3:
                        for (x, y, z), pixel_value in np.ndenumerate(image_array):
                            if z > 0: continue # only iterate through first layer
                            f = tk.Frame(image_frame[0], width=PIXELS_PER_ELEMENT[0],
                                         height=PIXELS_PER_ELEMENT[0])
                            f.grid(row=y, column=x, columnspan=1, rowspan=1)
                            f.rowconfigure(0, weight=1)
                            f.columnconfigure(0, weight=1)
                            f.grid_propagate(0)

                            element_string = sentence_to_draw[NARSGUI.KEY_ARRAY_ELEMENT_STRINGS][x, y,z]
                            img_array = np.array([
                                [
                                    [
                                        [image_array[x,y,0]]
                                    ]
                                ],
                                [
                                    [
                                        [image_array[x,y,1]]
                                    ]
                                ],
                                [
                                    [
                                        [image_array[x,y,2]]
                                    ]
                                ],
                                [
                                    [
                                        [image_alpha_array[(x, y)]]
                                    ]
                                ]
                            ])

                            img_array = img_array.T
                            img = Image.fromarray(img_array, mode="RGBA")
                            if not gui_array_use_confidence_opacity[0]:
                                img = img.convert(mode="RGB")

                            img = img.resize((PIXELS_PER_ELEMENT[0], PIXELS_PER_ELEMENT[0]), Image.NEAREST)
                            button = tk.Button(f,
                                               command=create_array_element_click_lambda(element_string))
                            render = ImageTk.PhotoImage(img)
                            button.config(image=render)
                            button.image = render
                            button.config(relief='solid', borderwidth=0)
                            button.grid(sticky="NWSE")
                            CreateToolTip(button, text=(element_string))

                def zoom_image_array(event):
                    # zoom the image array depending on how the user scrolled
                    if event is not None:
                        if event.delta > 0:
                            PIXELS_PER_ELEMENT[0] += 1
                        else:
                            PIXELS_PER_ELEMENT[0] -= 1
                    create_image_array()

            # checkbox to toggle array confidence opacity
            def toggle_confidence_opacity():
                gui_array_use_confidence_opacity[0] = not gui_array_use_confidence_opacity[0]
                zoom_image_array(None)

            check_var = tk.Variable()
            row += 1
            checkbutton = tk.Checkbutton(item_info_window, text='Visualize confidence using pixel opacity', onvalue=1, offvalue=0, variable=check_var, command=toggle_confidence_opacity)
            checkbutton.invoke()
            checkbutton.grid(row=row, column=column+2)

    def get_data_structure_name_from_listbox(self,listbox):
        keys = list(self.dict_listbox_from_id.keys())
        values = list(self.dict_listbox_from_id.values())
        return keys[values.index(listbox)]

def create_key_item_label(parent,row,column,key_label,value_label):
    """
        Dimensions: 1 row; 2 columns
    """
    label = tk.Label(parent, text=key_label, borderwidth=2, relief="raised", bg="white")
    label.grid(row=row, column=column, sticky='e')

    label = tk.Label(parent, text=value_label, borderwidth=2, relief="sunken", bg="white")
    label.grid(row=row, column=column + 1, columnspan=3, sticky='w')

def create_clickable_listbox(parent, row, column, title_label, listbox_contents, content_click_callback):
    """
        Dimensions 1 row; 3 columns
    """
    object_listbox_width = 60
    object_listbox_height = 20

    label = tk.Label(parent, text=title_label, font=('bold'))
    label.grid(row=row, column=column, columnspan=2)

    listbox = tk.Listbox(parent, height=object_listbox_height,
                                              width=object_listbox_width, font=('', 8))
    listbox.grid(row=row + 1, column=column, columnspan=2)
    for content in listbox_contents:
        listbox.insert(tk.END, content)
    listbox.bind("<<ListboxSelect>>",
                 lambda event: content_click_callback(event))

def start_gui(gui_use_internal_data, gui_use_interface, data_structure_IDs, data_structure_capacities, pipe_gui_objects,
              pipe_gui_strings):
    gui = NARSGUI()
    gui.execute_gui(gui_use_internal_data, gui_use_interface, data_structure_IDs,
                    data_structure_capacities,
                    pipe_gui_objects,
                    pipe_gui_strings)


def from_rgb_to_tkinter_color(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb


# from https://stackoverflow.com/questions/20399243/display-message-when-hovering-over-something-with-mouse-cursor-in-python
class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.widget.config(relief="groove",borderwidth=2)
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        self.widget.config( relief="solid",borderwidth=0)
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