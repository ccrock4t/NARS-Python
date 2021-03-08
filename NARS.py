import time

import InputBuffer
from NALInferenceRules import nal_revision
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
        statement_concept = self.get_concept_from_term(statement_term)

        # get subject-predicate concepts
        subject_concept = self.get_concept_from_term(subject_term)
        predicate_concept = self.get_concept_from_term(predicate_term)

        # set task links if they don't exist
        statement_concept.set_task_link(task)
        subject_concept.set_task_link(task)
        predicate_concept.set_task_link(task)

        if task.needs_initial_processing:
            # add judgment into concept belief table
            statement_concept.belief_table.insert(task.sentence)
            task.needs_initial_processing = False
        else:
            # get most confident belief of the same content
            belief = statement_concept.belief_table.peek()
            if belief is None: return
            if belief.has_evidential_overlap(task.sentence): return
            # do revision
            derived_sentence = nal_revision(belief, task.sentence)
            derived_task = Task(derived_sentence)
            print("Revision derived new task " + str(derived_task))
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
        statement_concept = self.get_concept_from_term(statement_term)

        # get subject-predicate concepts
        subject_concept = self.get_concept_from_term(subject_term)
        predicate_concept = self.get_concept_from_term(predicate_term)

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


    def get_concept_from_term(self, term):
        """
            Get the concept named by a term, and create it if it doesn't exist.
            Also creates all sub-term concepts if they do not exist.
        """
        concept = self.memory.get_concept(term)

        if concept is None:
            # concept must be created, and potentially sub-concepts
            concept = self.memory.conceptualize_term(term)
            if isinstance(term, NALGrammar.CompoundTerm):
                for subterm in term.subterms:
                    # get subterm concepts
                    subconcept = self.get_concept_from_term(subterm)
                    # do term linking with subterms
                    concept.set_term_link(subconcept)

        return concept

def main():
    # set globals
    Global.NARS = NARS()

    #setup GUI
    interface_GUI_thread = threading.Thread(target=setup_interface_gui, name="Interface GUI thread")
    interface_GUI_thread.daemon = True
    interface_GUI_thread.start()

    #setup GUI
    interal_GUI_thread = threading.Thread(target=setup_internal_gui, name="Internal GUI thread")
    interal_GUI_thread.daemon = True
    interal_GUI_thread.start()

    # Start NARS
    do_working_cycles()



def setup_internal_gui():
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
    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python - Interface")
    window.geometry('650x500')

    output_scrollbar = tk.Scrollbar(window)
    output_scrollbar.grid(row=1, column=3, sticky='ns')

    output_lbl = tk.Label(window, text="Output: ")
    output_lbl.grid(column=0, row=0, columnspan=3)

    Global.output_textbox = tk.Text(window, height=25, width=75, yscrollcommand=output_scrollbar.set)
    Global.output_textbox.grid(column=0, row=1, columnspan=3)

    # input GUI
    def input_clicked(event=None):
        # put input into NARS input buffer
        InputBuffer.add_input(input_field.get())
        # empty input field
        input_field.delete(0, tk.END)
        input_field.insert(0, "")

    input_lbl = tk.Label(window, text="Input: ")
    input_lbl.grid(column=0, row=2)

    input_field = tk.Entry(window,width=50)
    input_field.grid(column=1, row=2)
    input_field.focus()

    window.bind('<Return>', func=input_clicked)
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)
    send_input_btn.grid(column=2, row=2)

    window.mainloop()

def do_working_cycles():
    """
        Perform one working cycle.
        In each working cycle, NARS either *Observes* OR *Considers*:
    """
    while True:
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
