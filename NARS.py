import InputBuffer
import NALGrammar
from NARSMemory import Memory
import Global
import threading
import os
from NARSDataStructures import *
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
        self.process_judgment(task)

    def process_judgment(self, task):
        """
            Process a Narsese judgment task
            Add task links
        """
        assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term
        subject_term = statement_term.get_subject_term()
        predicate_term = statement_term.get_predicate_term()

        # get/create statement concept, and sub-term concepts recursively
        statement_concept = self.get_concept_from_term(statement_term)

        # get subject-predicate concepts
        subject_concept = self.get_concept_from_term(subject_term)
        predicate_concept = self.get_concept_from_term(predicate_term)

        # set task links if they don't exist
        statement_concept.set_task_link(task)
        subject_concept.set_task_link(task)
        predicate_concept.set_task_link(task)

        # add judgment to concept belief table
        statement_concept.merge_into_belief_table(task)

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
    Global.PRINT_ATTENTION = True
    Global.current_cycle_number = 0

    # launch user input thread
    t = threading.Thread(target=get_user_input, name="user input thread")
    t.daemon = True
    t.start()

    # run NARS
    while True:
        do_working_cycle()
        Global.current_cycle_number = Global.current_cycle_number + 1


def do_working_cycle():
    """
        Perform one working cycle.
        In each working cycle, NARS either *Observes* OR *Considers*:
    """
    rand = random.random()

    if rand < Config.MINDFULNESS:
        # OBSERVE
        Global.NARS.Observe()
    else:
        # CONSIDER
        Global.NARS.Consider()


def get_user_input():
    """
        Get user input from standard I/O
    """
    userinput = ""

    while userinput != "exit":
        userinput = input("")
        if userinput == "count":
            print("Memory count: " + str(Global.NARS.memory.get_number_of_concepts()))
            print("Buffer count: " + str(Global.NARS.overall_experience_buffer.count))
        else:
            InputBuffer.add_input(userinput)

    os._exit()


if __name__ == "__main__":
    main()
