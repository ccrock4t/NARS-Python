import time

import InputBuffer
import NARSInferenceEngine
from NALInferenceRules import nal_revision, nal_deduction
from NALSyntax import Punctuation
from NARSMemory import Memory
import threading
import os
from NARSDataStructures import *
import tkinter as tk
from Global import GlobalGUI, Global

"""
    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Main loop and NARS definition
"""
class NARS:
    """
       NARS Class
    """
    def __init__(self):
        self.overall_experience_buffer = Bag(item_type=Task)
        self.memory = Memory()

    def Observe(self):
        """
            Process a task from the overall experience buffer
        """
        task_item = self.overall_experience_buffer.take()

        if task_item is None:
            return # nothing to observe

        # process task
        self.process_task(task_item.object)

        # return task to buffer
        self.overall_experience_buffer.put(task_item)

    def Consider(self):
        """
            Process a task from a known concept
        """
        concept_item = self.memory.concepts_bag.take()

        if concept_item is None:
            return # nothing to ponder

        # get task and belief from concept

        # return concept to bag
        self.memory.concepts_bag.put(concept_item)

    def process_task(self, task):
        """
            Process a Narsese task
        """
        assert_task(task)
        if task.sentence.punctuation == Punctuation.Judgment:
            self.process_judgment(task)
        elif task.sentence.punctuation == Punctuation.Question:
            self.process_question(task)



    def process_judgment(self, task):
        """
            Process a Narsese judgment task
        """
        assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term
        subject_term = statement_term.get_subject_term()
        predicate_term = statement_term.get_predicate_term()

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.get_concept(statement_term)

        # get subject-predicate concepts
        subject_concept = self.memory.get_concept(subject_term)
        predicate_concept = self.memory.get_concept(predicate_term)

        # set task links if they don't exist
        statement_concept.set_task_link(task)
        subject_concept.set_task_link(task)
        predicate_concept.set_task_link(task)

        if task.needs_initial_processing:
            """
                Initial Processing
                
                Revise this judgment with the most confident belief, then insert it into the belief table
            """
            belief = statement_concept.belief_table.peek() # get most confident related_belief of the same content
            if (belief is not None) and (not task.sentence.has_evidential_overlap(belief)) and (belief not in task.interacted_beliefs):
                # perform revision on the belief
                derived_task = NARSInferenceEngine.perform_inference(task, belief)[0] # only 1 derived task in Revision
                self.overall_experience_buffer.put_new_item(derived_task)

            # add the judgment itself into concept's belief table
            statement_concept.belief_table.insert(task.sentence)
            task.needs_initial_processing = False
        else:
            """
                Continued processing
                
                Do local/forward inference on a related belief
            """
            related_concept = self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None: return # no related concepts!

            related_belief = related_concept.belief_table.peek() # get most confident related_belief of related concept
            if (related_belief is None) or (task.sentence.has_evidential_overlap(related_belief)) or (related_belief in task.interacted_beliefs): return

            derived_tasks = NARSInferenceEngine.perform_inference(task, related_belief)
            for derived_task in derived_tasks:
                self.overall_experience_buffer.put_new_item(derived_task)

    def process_question(self, task):
        """
            Process a Narsese question task
        """
        assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.get_concept(statement_term)

        if task.needs_initial_processing:
            # early quit if belief table is empty
            if len(statement_concept.belief_table) == 0: return
            # get the best answer from concept belief table
            best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek()
            if best_answer is None: return
            if task.is_from_input:
                GlobalGUI.print_to_output("OUT: " + best_answer.get_formatted_string())

            # initial processing complete
            task.needs_initial_processing = False
        else:
            if len(statement_concept.belief_table) == 0: return


def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.
    """
    # set globals
    Global.NARS = NARS()
    GlobalGUI.gui_print_internal_data = True # Setting this to False will significantly increase speed
    GlobalGUI.gui_use_interface = True # Setting this to False uses the shell as interface

    #setup internal GUI
    if GlobalGUI.gui_print_internal_data:
        internal_GUI_thread = threading.Thread(target=setup_internal_gui, name="Internal GUI thread")
        internal_GUI_thread.daemon = True
        internal_GUI_thread.start()
        time.sleep(0.25)

    #setup interface GUI
    if GlobalGUI.gui_use_interface:
        interface_thread = threading.Thread(target=setup_interface_gui, name="Interface GUI thread")
    else:
        # launch user input thread
        interface_thread = threading.Thread(target=get_user_input, name="user input thread")

    interface_thread.daemon = True
    interface_thread.start()
    # let the gui threads initialize
    time.sleep(1)

    # Finally, start NARS in the shell
    do_working_cycles()

def get_user_input():
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        InputBuffer.add_input(userinput)

def setup_internal_gui():
    """
        Setup the internal GUI window, displaying the system's buffers and memory
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Internal Data")
    window.geometry('925x500')

    output_lbl2 = tk.Label(window, text="Task Buffer: ")
    output_lbl2.grid(column=0, row=0)

    GlobalGUI.gui_experience_buffer_listbox = tk.Listbox(window, height=Config.BAG_CAPACITY, width=75, font=('', 8))
    GlobalGUI.gui_experience_buffer_listbox.grid(column=0, row=1, columnspan=2)

    output_lbl3 = tk.Label(window, text="Concepts: ")
    output_lbl3.grid(column=3, row=0)

    GlobalGUI.gui_concept_bag_listbox = tk.Listbox(window, height=Config.BAG_CAPACITY, width=75, font=('', 8))
    GlobalGUI.gui_concept_bag_listbox.grid(column=3, row=1, columnspan=2)

    window.mainloop()

def setup_interface_gui():
    """
        Setup the interface GUI window, displaying the system's i/o channels
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Interface")
    window.geometry('750x500')

    output_width = 3
    output_height = 3

    #row 0
    output_lbl = tk.Label(window, text="Output: ")
    output_lbl.grid(row=0, column=0, columnspan=output_width)

    #row 1
    output_scrollbar = tk.Scrollbar(window)
    output_scrollbar.grid(row=1, column=3, rowspan=output_height, sticky='ns')

    GlobalGUI.gui_output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
    GlobalGUI.gui_output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

    # row 2
    GlobalGUI.gui_total_cycles_lbl = tk.Label(window, text="Cycle #0")
    GlobalGUI.gui_total_cycles_lbl.grid(row=2, column=4, columnspan=2, sticky='n')

    speed_slider_lbl = tk.Label(window, text="Cycle Delay in millisec: ")
    speed_slider_lbl.grid(row=2, column=4, columnspan=2, sticky='s')

    #row 3
    def toggle_pause(event=None):
        # put input into NARS input buffer
        Global.paused = not Global.paused

        if Global.paused:
            GlobalGUI.play_pause_button.config(text="PLAY")
        else:
            GlobalGUI.play_pause_button.config(text="PAUSE")

    GlobalGUI.play_pause_button = tk.Button(window, text="PAUSE", command=toggle_pause)
    GlobalGUI.play_pause_button.grid(row=3, column=4, sticky='s')

    max_delay = 1000 # in milliseconds
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

    input_field = tk.Entry(window,width=50)
    input_field.grid(column=1, row=4)
    input_field.focus()

    window.bind('<Return>', func=input_clicked)
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)
    send_input_btn.grid(column=2, row=4)

    window.focus()

    window.mainloop()

def do_working_cycles():
    """
        Perform one working cycle.
        In each working cycle, NARS either *Observes* OR *Considers*:
    """
    while True:
        if Global.paused:
            continue
        if GlobalGUI.gui_use_interface:
            GlobalGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(Global.current_cycle_number))
            time.sleep(GlobalGUI.gui_delay_slider.get() / 1000)
        rand = random.random()
        if rand < Config.MINDFULNESS:
            # OBSERVE
            Global.NARS.Observe()
        else:
            # CONSIDER
            Global.NARS.Consider()

        Global.current_cycle_number = Global.current_cycle_number + 1



if __name__ == "__main__":
    main()
