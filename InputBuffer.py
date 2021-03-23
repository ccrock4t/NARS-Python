import queue

from NALGrammar import *
from Global import GlobalGUI
import Config
from NARSDataStructures import Task

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Parses an input string and converts it into a Narsese Task which is fed into NARS' task buffer
"""

input_queue = queue.Queue()

def add_input_string(input_string: str):
    try:
        if input_string == "count":
            GlobalGUI.print_to_output(
                "Memory count (concepts in memory): " + str(Global.NARS.memory.get_number_of_concepts()))
            GlobalGUI.print_to_output(
                "Buffer count (tasks in buffer): " + str(Global.NARS.overall_experience_buffer.count))
            return
        elif input_string == "cycle":
            GlobalGUI.print_to_output("Current cycle: " + str(Global.current_cycle_number))
            return
        else:
            sentence = Sentence.parse_sentence_from_string(input_string)
            input_queue.put(item=sentence)
    except AssertionError as msg:
        GlobalGUI.print_to_output("INPUT REJECTED: " + str(msg))
        return

def add_input_sentence(sentence: Sentence):
    input_queue.put(item=sentence)


def process_next_pending_sentence():
    """
        Processes the next pending sentence from input buffer if one exists
    """
    if input_queue.qsize() > 0:
        sentence = input_queue.get()
        process_sentence(sentence)


def process_sentence(sentence: Sentence):
    GlobalGUI.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = Task(sentence, is_input_task=True)
    Global.NARS.overall_experience_buffer.put_new_item(task)
