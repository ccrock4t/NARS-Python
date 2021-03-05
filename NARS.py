import InputBuffer
from NALSyntax import Punctuation
from NARSMemory import Memory
import threading
import os
from NARSDataStructures import *
import tkinter as tk

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
        if task.needs_initial_processing: #
            if task.sentence.punctuation == Punctuation.Judgment:
                self.initial_process_judgment(task)
            elif task.sentence.punctuation == Punctuation.Question:
                self.initial_process_question(task)

        #todo implement continued processing

    def initial_process_judgment(self, task):
        """
            Process a Narsese judgment task, for the first time it is selected
            Add task links if they don't exist
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

        # add judgment into concept belief table
        statement_concept.belief_table.insert(task.sentence)

    def initial_process_question(self, task):
        """
            Process a Narsese question task, for the first time it is selected
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

        # early quit if belief table is empty
        if len(statement_concept.belief_table) == 0: return
        # get the best answer from concept belief table
        best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek()
        if task.is_from_input: print("OUT: " + best_answer.get_formatted_string())

        # initial processing complete
        task.needs_initial_processing = False

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
    Global.current_cycle_number = 0
    Global.PRINT_ATTENTION = False

    # launch NARS thread in Console
    t = threading.Thread(target=do_working_cycle, name="NARS thread")
    t.daemon = True
    t.start()

    # launch GUI
    window = tk.Tk()
    window.title("NARS in Python")
    window.geometry('450x40')

    # input GUI
    def input_clicked(event=None):
        # put input into NARS input buffer
        InputBuffer.add_input(input_field.get())
        # empty input field
        input_field.delete(0, tk.END)
        input_field.insert(0, "")

    input_lbl = tk.Label(window, text="Input: ")
    input_lbl.grid(column=0, row=0)
    input_field = tk.Entry(window,width=50)
    input_field.grid(column=1, row=0)

    window.bind('<Return>', func=input_clicked)
    send_input_btn = tk.Button(window, text="Send input.", command=input_clicked)
    send_input_btn.grid(column=2, row=0)

    window.mainloop()

def do_working_cycle():
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
