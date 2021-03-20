import time

import InputBuffer
import NARSGUI
import NARSInferenceEngine
from NALSyntax import Punctuation
from NARSMemory import Memory
import threading

from NARSDataStructures import *
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

    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """
        if GlobalGUI.gui_use_interface:
            GlobalGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(Global.current_cycle_number))

        # working cycle
        rand = random.random()
        if rand < Config.MINDFULNESS:
            # OBSERVE
            self.Observe()
        else:
            # CONSIDER
            self.Consider()

        Global.current_cycle_number = Global.current_cycle_number + 1

    def Observe(self):
        """
            Process a task from the overall experience buffer
        """
        task_item = self.overall_experience_buffer.take()

        if task_item is None:
            return  # nothing to observe

        # process task
        self.process_task(task_item.object)

        # decay priority
        task_item.decay()

        # return task to buffer
        self.overall_experience_buffer.put(task_item)

    def Consider(self):
        """
            Process a task from a known concept
        """
        concept_item = self.memory.concepts_bag.take()

        if concept_item is None:
            return  # nothing to ponder

        # get task and belief from concept

        # decay priority
        concept_item.decay()

        # return concept to bag
        self.memory.concepts_bag.put(concept_item)

    def process_task(self, task: Task):
        """
            Processes any Narsese task
        """
        assert_task(task)
        if task.sentence.punctuation == Punctuation.Judgment:
            self.process_judgment(task)
        elif task.sentence.punctuation == Punctuation.Question:
            self.process_question(task)

    def process_judgment(self, task: Task):
        """
            Processes a Narsese judgment task
        """
        assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term
        subject_term = statement_term.get_subject_term()
        predicate_term = statement_term.get_predicate_term()

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # get subject-predicate concepts
        subject_concept = self.memory.peek_concept(subject_term)
        predicate_concept = self.memory.peek_concept(predicate_term)

        # set task links if they don't exist
        statement_concept.set_task_link(task)
        subject_concept.set_task_link(task)
        predicate_concept.set_task_link(task)

        if task.needs_initial_processing:
            """
                Initial Processing
                
                Revise this judgment with the most confident belief, then insert it into the belief table
            """
            belief = statement_concept.belief_table.peek()  # get most confident related_belief of the same content
            if (belief is not None) and (not task.sentence.has_evidential_overlap(belief)) and (
                    belief not in task.interacted_beliefs):
                # perform revision on the belief
                derived_tasks = NARSInferenceEngine.perform_inference(task, belief)
                if len(derived_tasks) > 0:
                    derived_task = derived_tasks[0]  # only 1 derived task in Revision
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
            if related_concept is None: return  # no related concepts!

            related_belief = related_concept.belief_table.peek()  # get most confident related_belief of related concept

            # can't process if no related belief, they have evidential overlap,
            # or they have already interacted previously
            if (related_belief is None) or (task.sentence.has_evidential_overlap(related_belief)) or (
                    related_belief in task.interacted_beliefs): return

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
        statement_concept = self.memory.peek_concept(statement_term)

        """
            Get and print the best answer to the question by peeking the most confident belief in
            the Question's Concept's Belief Table.
        """
        # get the best answer from concept belief table
        best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek()
        if best_answer is not None:
            # Answer the question
            if task.is_from_input and task.needs_answer_output:
                GlobalGUI.print_to_output("OUT: " + best_answer.get_formatted_string())
                task.needs_answer_output = False

            # initial processing complete
            task.needs_initial_processing = False
        else: # no answer
            related_concept = self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None: return  # no related concepts!

            related_belief = related_concept.belief_table.peek()  # get most confident related_belief of related concept

            # can't process if no related belief, they have evidential overlap,
            # or they have already interacted previously
            if (related_belief is None) or (task.sentence.has_evidential_overlap(related_belief)) or (
                    related_belief in task.interacted_beliefs): return

            derived_tasks = NARSInferenceEngine.perform_inference(task, related_belief)
            for derived_task in derived_tasks:
                self.overall_experience_buffer.put_new_item(derived_task)



def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.
    """
    # set globals
    Global.NARS = NARS()
    GlobalGUI.gui_use_internal_data = True  # Setting this to False will prevent creation of the Internal Data GUI thread
    # todo investigate why using the interface slows down the system
    GlobalGUI.gui_use_interface = True  # Setting this to False uses the shell as interface, and results in a massive speedup

    # setup internal/interface GUI
    if GlobalGUI.gui_use_internal_data or GlobalGUI.gui_use_interface:
        GUI_thread = threading.Thread(target=NARSGUI.execute_gui, name="GUI thread")
        GUI_thread.daemon = True
        GUI_thread.start()

    if not GlobalGUI.gui_use_interface:
        # launch shell input thread
        shell_input_thread = threading.Thread(target=NARSGUI.get_user_input, name="Shell input thread")
        shell_input_thread.daemon = True
        shell_input_thread.start()

    time.sleep(1.00) # give threads time to setup

    # Finally, start NARS in the shell
    run()


def run():
    """
        Infinite loop of working cycles
    """
    while True:
        # global parameters
        if Global.paused:
            continue
        if GlobalGUI.gui_use_interface:
            delay = GlobalGUI.gui_delay_slider.get() / 1000
            if delay > 0:
                time.sleep(delay)

        InputBuffer.process_next_pending_sentence()
        Global.NARS.do_working_cycle()


if __name__ == "__main__":
    main()
