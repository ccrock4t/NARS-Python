import pickle
import random
import time

import Config
import InputBuffer
import NARSGUI
import NARSInferenceEngine
import NALGrammar
import NALSyntax
import NARSMemory
import threading

import NARSDataStructures
import Global

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
        self.overall_experience_buffer = NARSDataStructures.Buffer(item_type=NARSDataStructures.Task)
        self.memory = NARSMemory.Memory()
        Global.Global.NARS = self # there can only be one NARS running

    def save_memory_to_disk(self, filename="memory.nars"):
        """
            Save the NARS Memory instance to disk
        """
        with open(filename, "wb") as f:
            Global.GlobalGUI.print_to_output("SAVING SYSTEM MEMORY TO FILE: " + filename)
            pickle.dump(self.memory, f, pickle.HIGHEST_PROTOCOL)
            Global.GlobalGUI.print_to_output("SAVE MEMORY SUCCESS")

    def load_memory_from_disk(self, filename="memory.nars"):
        """
            Load a NARS Memory instance from disk.
            This will override the NARS current memory
        """
        try:
            with open(filename, "rb") as f:
                Global.GlobalGUI.print_to_output("LOADING SYSTEM MEMORY FILE: " + filename)
                # load memory from file
                self.memory = pickle.load(f)
                # Print memory contents to internal data GUI
                if Global.GlobalGUI.gui_use_internal_data:
                    Global.GlobalGUI.clear_output_gui(data_structure=self.memory.concepts_bag)
                    for item in self.memory.concepts_bag:
                        if item not in self.memory.concepts_bag:
                            Global.GlobalGUI.print_to_output(msg=str(item), data_structure=self.memory.concepts_bag)

                if Global.GlobalGUI.gui_use_interface:
                    Global.GlobalGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(self.memory.current_cycle_number))

                Global.GlobalGUI.print_to_output("LOAD MEMORY SUCCESS")
        except:
            Global.GlobalGUI.print_to_output("LOAD MEMORY FAIL")

    def run(self):
        """
            Infinite loop of working cycles
        """
        while True:
            # global parameters
            if Global.Global.paused:
                continue
            if Global.GlobalGUI.gui_use_interface:
                delay = Global.GlobalGUI.gui_delay_slider.get() / 1000
                if delay > 0:
                    time.sleep(delay)

            self.do_working_cycle()

    def do_working_cycle(self):
        """
            Performs 1 working cycle.
            In each working cycle, NARS either *Observes* OR *Considers*:
        """
        if Global.GlobalGUI.gui_use_interface:
            Global.GlobalGUI.gui_total_cycles_lbl.config(text="Cycle #" + str(self.memory.current_cycle_number))

        InputBuffer.process_next_pending_sentence()

        # working cycle
        rand = random.random()
        if rand < Config.MINDFULNESS and len(self.overall_experience_buffer) > 0:
            # OBSERVE
            self.Observe()
        else:
            # CONSIDER
            self.Consider()

        self.memory.current_cycle_number = self.memory.current_cycle_number + 1

    def do_working_cycles(self, cycles: int):
        """
            Performs an arbitrary number of working cycles.
        """
        for i in range(cycles):
            self.do_working_cycle()


    def Observe(self):
        """
            Process a task from the overall experience buffer
        """
        task_item = self.overall_experience_buffer.take()

        if task_item is None:
            return  # nothing to observe

        # process task
        self.process_task(task_item.object)

        if isinstance(task_item.object.sentence, NALGrammar.Question):
            # decay priority
            task_item.decay()

            # return task to buffer
            self.overall_experience_buffer.put(task_item)

    def Consider(self):
        """
            Process a task from a known concept
        """
        concept_item = self.memory.concepts_bag.temporary_take()

        if concept_item is None:
            return  # nothing to ponder

        sentence = concept_item.object.belief_table.peek_max()

        if isinstance(sentence, NALGrammar.Judgment):
            # process the judgment
            self.process_judgment_sentence(sentence)

        # decay priority
        concept_item.decay()

        # return concept to bag
        self.memory.concepts_bag.put(concept_item)

    def process_task(self, task: NARSDataStructures.Task):
        """
            Processes any Narsese task
        """
        NARSDataStructures.assert_task(task)

        if task.sentence.punctuation == NALSyntax.Punctuation.Question or NALGrammar.VariableTerm.QUERY_SYM in str(task.sentence.statement.term):
            self.process_question(task)
        elif task.sentence.punctuation == NALSyntax.Punctuation.Judgment:
            self.process_judgment_task(task)

    def process_judgment_task(self, task: NARSDataStructures.Task):
        """
            Processes a Narsese Judgment Task

            :param Judgment Task to process
        """
        NARSDataStructures.assert_task(task)

        j1 = task.sentence

        # get terms from sentence
        statement_term = j1.statement.term

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if statement_term.contains_variable(): return #todo handle variables
        
        if task.needs_initial_processing:
            """
                Initial Processing
                
                Revise this judgment with the most confident belief, then insert it into the belief table
            """
            # revise the judgment
            self.process_judgment_sentence(j1, statement_concept)
            # add the judgment itself into concept's belief table
            statement_concept.belief_table.put(j1)
            task.needs_initial_processing = False
        else:
            """
                Continued processing
                
                Do local/forward inference on a related belief
            """
            self.process_judgment_sentence(j1)


    def process_judgment_sentence(self, j1, related_concept=None):
        """
            Processes a Judgment Sentence with a related belief.

            :param j1 - judgment sentence to process
            :param related_concept - (Optional) concept to process the judgment with

            #todo handle variables
            #todo handle tenses
        """
        statement_term = j1.statement.term
        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        if statement_term.contains_variable(): return

        if related_concept is None: # get a related concept
            related_concept = self.memory.get_semantically_related_concept(statement_concept)
            if related_concept is None:
                print("none!")
                return  # no related concepts!

        j2 = related_concept.belief_table.peek_max()  # get most confident related_belief of related concept

        # done if can't interact
        if not NALGrammar.Sentence.may_interact(j1,j2): return

        derived_tasks = NARSInferenceEngine.do_inference(j1, j2)
        for derived_task in derived_tasks:
            self.overall_experience_buffer.put(derived_task)

    def process_question(self, task):
        """
            Process a Narsese question task

            Get the best answer to the question if it's known and perform inference with it;
            otherwise, use backward inference to derive new questions that could lead to an answer.

            #todo handle variables
            #todo handle tenses
        """
        NARSDataStructures.assert_task(task)

        # get terms from sentence
        statement_term = task.sentence.statement.term

        if statement_term.contains_variable(): return  # todo handle variables

        # get (or create if necessary) statement concept, and sub-term concepts recursively
        statement_concept = self.memory.peek_concept(statement_term)

        # get the best answer from concept belief table
        best_answer: NALGrammar.Judgment = statement_concept.belief_table.peek_max()
        j1 = None
        if best_answer is not None:
            #
            # Answer the question
            #
            if task.is_from_input and task.needs_to_be_answered_in_output:
                Global.GlobalGUI.print_to_output("OUT: " + best_answer.get_formatted_string())
                task.needs_to_be_answered_in_output = False

            # do inference between answer and a related belief
            j1 = best_answer
        else:
            # do inference between question and a related belief
            j1 = task.sentence

        # get a related concept
        related_concept = self.memory.get_semantically_related_concept(statement_concept)
        j2 = related_concept.belief_table.peek_max()  # get most confident related_belief of related concept
        if related_concept is None: return  # no related concepts!

        # done if can't interact
        if not NALGrammar.Sentence.may_interact(j1,j2): return

        derived_tasks = NARSInferenceEngine.do_inference(j1, j2)
        # add all derived tasks to the buffer
        for derived_task in derived_tasks:
            self.overall_experience_buffer.put(derived_task)




def main():
    """
        This is where the program starts
        Creates threads, populates globals, and runs the NARS.
    """
    # set globals
    Global.GlobalGUI.gui_use_internal_data = True  # Setting this to False will prevent creation of the Internal Data GUI thread
    # todo investigate why using the interface slows down the system
    Global.GlobalGUI.gui_use_interface = True # Setting this to False uses the shell as interface, and results in a massive speedup

    # setup internal/interface GUI
    if Global.GlobalGUI.gui_use_internal_data or Global.GlobalGUI.gui_use_interface:
        GUI_thread = threading.Thread(target=NARSGUI.execute_gui, name="GUI thread")
        GUI_thread.daemon = True
        GUI_thread.start()

    if not Global.GlobalGUI.gui_use_interface:
        # launch shell input thread
        shell_input_thread = threading.Thread(target=NARSGUI.get_user_input, name="Shell input thread")
        shell_input_thread.daemon = True
        shell_input_thread.start()

    Global.Global.paused = Global.GlobalGUI.gui_use_interface

    time.sleep(0.5) # give threads time to setup

    # Finally, create the NARS
    NARS()
    # and run it in the shell
    Global.Global.NARS.run()



if __name__ == "__main__":
    main()
