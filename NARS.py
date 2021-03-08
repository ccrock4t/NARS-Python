import time

import InputBuffer
from NALInferenceRules import nal_revision, nal_deduction
from NALSyntax import Punctuation
from NARSMemory import Memory
import threading
import os
from NARSDataStructures import *
import tkinter as tk
from Global import Global

"""
    Author: Christian Hahm
    Created: October 8, 2020
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

        if Global.PRINT_ATTENTION:
            print("Observe: " + str(task_item.object))

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

        if Global.PRINT_ATTENTION:
            print("Consider: " + str(concept_item.object))

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
            # add judgment into concept belief table
            statement_concept.belief_table.insert(task.sentence)
            task.needs_initial_processing = False
        else:
            """
                Revision stage
            """
            belief = statement_concept.belief_table.peek() # get most confident belief of the same content
            if (belief is not None) and (not task.sentence.has_evidential_overlap(belief)) and (belief not in task.interacted_beliefs):
                derived_sentence = nal_revision(belief, task.sentence) #perform revision
                task.interacted_beliefs.append(belief)
                derived_task = Task(derived_sentence)
                print("Revision derived new task " + str(derived_task))
                print("Derived task evidential base " + str(derived_task.sentence.stamp.evidential_base.base))
                self.overall_experience_buffer.put_new_item(derived_task)

            """
                Forward Inference stage
            """
            related_concept = self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None: return # no related concepts!
            belief = related_concept.belief_table.peek() # get most confident belief of the same content
            if not task.sentence.has_evidential_overlap(belief) and (belief not in task.interacted_beliefs):
                if subject_term == belief.statement.term.get_predicate_term() :
                    # M-->P, S-->M
                    # deduction
                    derived_sentence = nal_deduction(task.sentence, belief)
                elif predicate_term == belief.statement.term.get_subject_term():
                    # S-->M, M-->P
                    # deduction
                    derived_sentence = nal_deduction(belief, task.sentence)
                else:
                    assert False, "error, concept not related"

                task.interacted_beliefs.append(belief)
                derived_task = Task(derived_sentence)
                print("Deduction derived new task " + str(derived_task))
                print("Derived task evidential base " + str(derived_task.sentence.stamp.evidential_base.base))
                self.overall_experience_buffer.put_new_item(derived_task)

    def process_question(self, task):
        """
            Process a Narsese question task
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

        if task.needs_initial_processing:
            # early quit if belief table is empty
            if len(statement_concept.belief_table) == 0: return
            # get the best answer from concept belief table
            best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek()
            if best_answer is None: return
            if task.is_from_input:
                Global.print_to_output("OUT: " + best_answer.get_formatted_string())

            # initial processing complete
            task.needs_initial_processing = False
        else:
            if len(statement_concept.belief_table) == 0: return


def main():
    """
        This is where the program starts
        Creates threads, populates some globals, and runs the NARS.
    """
    # set globals
    Global.NARS = NARS()

    #setup internal GUI
    internal_GUI_thread = threading.Thread(target=setup_internal_gui, name="Internal GUI thread")
    internal_GUI_thread.daemon = True
    internal_GUI_thread.start()

    time.sleep(0.25)

    #setup interface GUI
    interface_GUI_thread = threading.Thread(target=setup_interface_gui, name="Interface GUI thread")
    interface_GUI_thread.daemon = True
    interface_GUI_thread.start()
    # let the gui threads initialize
    time.sleep(1)

    # Finally, start NARS
    do_working_cycles()


def setup_internal_gui():
    """
        Setup the internal GUI window, displaying the system's buffers and memory
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Internal Data")
    window.geometry('925x425')

    output_lbl2 = tk.Label(window, text="Task Buffer: ")
    output_lbl2.grid(column=0, row=0)

    Global.experience_buffer_listbox = tk.Listbox(window, height=25, width=75)
    Global.experience_buffer_listbox.grid(column=0, row=1, columnspan=2)

    output_lbl3 = tk.Label(window, text="Concepts: ")
    output_lbl3.grid(column=3, row=0)

    Global.concept_bag_listbox = tk.Listbox(window, height=25, width=75)
    Global.concept_bag_listbox.grid(column=3, row=1, columnspan=2)

    window.mainloop()

def setup_interface_gui():
    """
        Setup the interface GUI window, displaying the system's i/o channels
    """
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Interface")
    window.geometry('700x500')

    output_width = 3
    output_height = 2

    #row 0
    output_lbl = tk.Label(window, text="Output: ")
    output_lbl.grid(row=0, column=0, columnspan=output_width)

    #row 1
    output_scrollbar = tk.Scrollbar(window)
    output_scrollbar.grid(row=1, column=3, sticky='ns')

    Global.output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
    Global.output_textbox.grid(row=1, column=0, columnspan=output_width, rowspan=output_height)

    speed_slider_lbl = tk.Label(window, text="millisec/step: ")
    speed_slider_lbl.grid(row=1, column=4, sticky='s')

    #row 2
    Global.speed_slider = tk.Scale(window,from_=1000, to=0)
    Global.speed_slider.grid(row=2, column=4,sticky='ns')

    # input GUI
    def input_clicked(event=None):
        # put input into NARS input buffer
        InputBuffer.add_input(input_field.get())
        # empty input field
        input_field.delete(0, tk.END)
        input_field.insert(0, "")

    input_lbl = tk.Label(window, text="Input: ")
    input_lbl.grid(column=0, row=3)

    input_field = tk.Entry(window,width=50)
    input_field.grid(column=1, row=3)
    input_field.focus()

    window.bind('<Return>', func=input_clicked)
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)
    send_input_btn.grid(column=2, row=3)

    window.focus()

    window.mainloop()

def do_working_cycles():
    """
        Perform one working cycle.
        In each working cycle, NARS either *Observes* OR *Considers*:
    """
    while True:
        time.sleep(Global.speed_slider.get() / 1000)
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
