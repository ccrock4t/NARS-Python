import InputBuffer
from NARSMemory import Memory
import Globals
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

        if Globals.PRINT_ATTENTION:
            print("OBSERVED: Task "+ str(task_item.object))

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

        if Globals.PRINT_ATTENTION:
            print("CONSIDERED: Concept " + str(concept_item.object))

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
        subject_term = task.sentence.statement.term.get_subject_term()
        predicate_term = task.sentence.statement.term.get_predicate_term()
        statement_term = task.sentence.statement.term

        # get concepts
        statement_concept = self.memory.get_concept(statement_term)
        subject_concept = self.memory.get_concept(subject_term)
        predicate_concept = self.memory.get_concept(predicate_term)

        # create it if it doesn't exist
        if statement_concept is None:
            statement_concept, subject_concept, predicate_concept = self.process_new_judgment(task)

        # add task links if they don't exist
        statement_concept.add_task_link(task)
        subject_concept.add_task_link(task)
        predicate_concept.add_task_link(task)

    def process_new_judgment(self, task):

        """
            Create a new statement concept
            Also creates new subject/predicate concepts if they don't exist
            Also connects term links
        """
        assert_task(task)
        # get terms
        statement_term = task.sentence.statement.term
        subject_term = statement_term.get_subject_term()
        predicate_term = statement_term.get_predicate_term()

        # get concepts
        subject_concept = self.memory.get_concept(subject_term)
        predicate_concept = self.memory.get_concept(predicate_term)

        # create concepts if they don't exist
        if subject_concept is None:
            subject_concept = self.memory.conceptualize_term(subject_term)
        if predicate_concept is None:
            predicate_concept = self.memory.conceptualize_term(predicate_term)

        # create new statement concept
        statement_concept = self.memory.conceptualize_term(statement_term)

        # do term linking
        statement_concept.add_term_link(subject_concept)
        statement_concept.add_term_link(predicate_concept)
        subject_concept.add_term_link(statement_concept)
        predicate_concept.add_term_link(statement_concept)

        return statement_concept, subject_concept, predicate_concept



def main():
    # set globals
    Globals.NARS = NARS()
    Globals.PRINT_ATTENTION = False
    Globals.executed_cycles = 0

    # launch user input thread
    t = threading.Thread(target=get_user_input, name="user input thread")
    t.daemon = True
    t.start()

    # run NARS
    while True:
        do_working_cycle()
        Globals.executed_cycles = Globals.executed_cycles + 1


def do_working_cycle():
    """
        Perform one working cycle.
        In each working cycle, NARS either *Observes* OR *Considers*:
    """
    rand = random.random()

    if rand < Config.MINDFULNESS: #OBSERVE
        Globals.NARS.Observe()
    else: #CONSIDER
        Globals.NARS.Consider()


def get_user_input():
    """
        Get user input from standard I/O
    """
    userinput = ""

    while userinput != "exit":
        userinput = input("")
        if userinput == "count":
            print("Memory count: " + str(Globals.NARS.memory.get_number_of_concepts()))
            print("Buffer count: " + str(Globals.NARS.overall_experience_buffer.count))
        else:
            InputBuffer.add_input(userinput)

    os._exit()


if __name__ == "__main__":
    main()
