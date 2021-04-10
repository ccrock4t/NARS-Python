import time

import NALGrammar
import Global
import NARSDataStructures
import queue

import NARSGUI

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Parses an input string and converts it into a Narsese Task which is fed into NARS' task buffer
"""

input_queue = queue.Queue()

def add_input_string(input_string: str):
    try:
        if input_string == "count":
            NARSGUI.NARSGUI.print_to_output(
                "Memory count (concepts in memory): " + str(Global.Global.NARS.memory.get_number_of_concepts()))
            NARSGUI.NARSGUI.print_to_output(
                "Buffer count (tasks in buffer): " + str(Global.Global.NARS.overall_experience_buffer.count))
            return
        elif input_string == "cycle":
            NARSGUI.NARSGUI.print_to_output("Current cycle: " + str(Global.Global.memory.current_cycle_number))
            return
        elif input_string == "save":
            Global.Global.NARS.save_memory_to_disk()
        elif input_string == "load":
            Global.Global.NARS.load_memory_from_disk()
        elif input_string == "load_input":
            load_input()
        else:
            while Global.Global.NARS is None:
                print("Waiting for NARS to start up...")
                time.sleep(1.0)
            sentence = NALGrammar.Sentence.new_sentence_from_string(input_string)
            add_input_sentence(sentence)
    except AssertionError as msg:
        NARSGUI.NARSGUI.print_to_output("INPUT REJECTED: " + str(msg))
        return

def add_input_sentence(sentence: NALGrammar.Sentence):
    """
        Pend a sentence to be processed.
        :param sentence:
    """
    input_queue.put(item=sentence)


def process_next_pending_sentence():
    """
        Processes the next pending sentence from the input buffer if one exists
    """
    if input_queue.qsize() == 0: return # no inputs
    sentence = input_queue.get()
    process_sentence(sentence)


def process_sentence(sentence: NALGrammar.Sentence):
    """
        Given a Sentence, ingest it into NARS' experience buffer
        :param sentence:
    """
    NARSGUI.NARSGUI.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = NARSDataStructures.Task(sentence, is_input_task=True)
    Global.Global.NARS.overall_experience_buffer.put_new(task)

def load_input(filename="input.nal"):
    """
        Load NAL input from a file
    """
    try:
        with open(filename, "r") as f:
            NARSGUI.NARSGUI.print_to_output("LOADING INPUT FILE: " + filename)
            for line in f.readlines():
                add_input_string(line)
            NARSGUI.NARSGUI.print_to_output("LOAD INPUT SUCCESS")
    except:
        NARSGUI.NARSGUI.print_to_output("LOAD INPUT FAIL")