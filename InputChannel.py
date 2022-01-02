import timeit as time

import numpy as np

import Config
import NALGrammar.Sentences
import Global
import NALSyntax
import NARSDataStructures
import NALInferenceRules.TruthValueFunctions

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Parses an input string and converts it into a Narsese Task which is fed into NARS' task buffer
"""

pended_input_data_queue = []
VISION_KEYWORD = "vision:"
NARSESE_KEYWORD = "narsese:"


def get_user_input():
    userinputstr = ""

    global pended_input_data_queue
    while userinputstr != "exit":
        userinputstr = input("")
        pended_input_data_queue.append(userinputstr)


def parse_and_queue_input_string(input_string: str):
    """
        Parses any input string and queues the resultant Narsese sentences to the input buffer.

        If the input string is a command, executes the command instead.
    :param input_string:
    :return:
    """
    if is_sensory_array_input_string(input_string):
        #todo broken
        # don't split by lines, this is array input
        sentence = parse_input_line(input_string)
        pended_input_data_queue.append(sentence)
    else:
        # treat each line as a separate input
        pended_input_data_queue.append((NARSESE_KEYWORD,input_string))




def parse_input_line(input_string: str):
    """
        Parses one line of an input string and returns the resultant Narsese sentence.

        If the input string is a command, executes the command instead.
    :param input_string:
    :return:
    """
    input_string = input_string.replace(" ", "")  # remove all spaces
    try:
        NARS = Global.Global.NARS
        if input_string == "count":
            Global.Global.print_to_output(
                "Memory count (concepts in memory): " + str(len(NARS.memory)))
        elif input_string == "cycle":
            Global.Global.print_to_output("Current cycle: " + str(Global.Global.get_current_cycle_number()))
        elif input_string == "save":
            NARS.save_memory_to_disk()
        elif input_string == "load":
            NARS.load_memory_from_disk()
        elif input_string == "load_input":
            load_input()
        else:
            while Global.Global.NARS is None:
                Global.Global.print_to_output("Waiting for NARS to start up...")
                time.sleep(1.0)

            if is_sensory_array_input_string(input_string):
                # sensory array input (a matrix of RGB or brightness values)
                sentence = parse_visual_sensory_string(input_string[len(VISION_KEYWORD):])
            else:
                # regular Narsese input
                sentence = NALGrammar.Sentences.new_sentence_from_string(input_string)

            return sentence
    except AssertionError as msg:
        Global.Global.print_to_output("WARNING: INPUT REJECTED: " + str(msg))
    return None


def process_input_channel():
    """
        Processes the next pending sentence from the input buffer if one exists

        return: whether statement was processed
    """
    while len(pended_input_data_queue) > 0:
        data = pended_input_data_queue.pop()
        if data[0] == NARSESE_KEYWORD:
            input_string = data[1]
            # turn strings into sentences
            lines = input_string.splitlines(False)
            for line in lines:
                sentence = parse_input_line(line)
                # turn sentences into tasks
                process_sentence_into_task(sentence)
        elif data[0] == VISION_KEYWORD:
                img = data[1]
                img_array = np.array(img)

                # tuple holds spatial truth values
                Global.Global.NARS.vision_buffer.set_image(img_array)


def process_sentence_into_task(sentence: NALGrammar.Sentences.Sentence):
    """
        Put a sentence into a NARS task, then do something with the Task
        :param sentence:
    """
    if not Config.SILENT_MODE: Global.Global.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = NARSDataStructures.Other.Task(sentence, is_input_task=True)

    Global.Global.NARS.global_buffer.put_new(task)

def load_input(filename="input.nal"):
    """
        Load NAL input from a file
    """
    try:
        with open(filename, "r") as f:
            Global.Global.print_to_output("LOADING INPUT FILE: " + filename)
            for line in f.readlines():
                parse_and_queue_input_string(line)
            np.array()
            Global.Global.print_to_output("LOAD INPUT SUCCESS")
    except:
        Global.Global.print_to_output("LOAD INPUT FAIL")


def is_sensory_array_input_string(input_string):
    return input_string[0:len(VISION_KEYWORD)] == VISION_KEYWORD


def parse_visual_sensory_string(input_string):
    """
        Convert a 3d array of RGB or a 2d array of brightness values to Narsese.

        Also generates and assigns this visual sensation its own unique term.

        Returns a sensory percept of form: {@S} --> [t])

        input_string:

            2D (matrix of intensities):
                [f;c,...,f;c],
                [...,...,...],
                [f;c,...,f;c]

            3D (tensor of intensities):
                [
                    [f;c,...,f;c],
                    [...,...,...],
                    [f;c,...,f;c]
                ],
                ...,
                [
                    [f;c,...,f;c],
                    [...,...,...],
                    [f;c,...,f;c]
                ]


    """
    # remove line endings
    input_string = input_string.replace("\n", "")
    input_string = input_string.replace("\r", "")
    input_string = input_string[1:-1]

    array_idx_start_marker = NALSyntax.StatementSyntax.ArrayElementIndexStart.value
    array_idx_end_marker = NALSyntax.StatementSyntax.ArrayElementIndexEnd.value

    def parse_1D_array(input_string):
        # 1D array
        pixel_value_array = input_string.split(",")
        x_length = len(pixel_value_array)
        dim_lengths = (x_length,)  # how many elements in a row
        return np.array(pixel_value_array)

    def parse_2D_array(input_string):
        # 2D array
        pixel_value_array = []
        depth = 0
        piece = ""
        for i in range(len(input_string)):
            c = input_string[i]
            if depth == 0 and c == ",":
                pixel_value_array.append(parse_1D_array(piece)[0])
                piece = ""
            else:
                if c == array_idx_start_marker:
                    depth += 1
                elif c == array_idx_end_marker:
                    depth -= 1
                else:
                    piece += c

        pixel_value_array.append(parse_1D_array(piece)[0])

        x_length = len(pixel_value_array[0])  # how many elements in a row
        y_length = len(pixel_value_array)  # how many rows

        return np.array(pixel_value_array)

    def parse_3D_array(input_string):
        # 3D array
        pixel_value_array = []
        depth = 0
        piece = ""
        for i in range(len(input_string)):
            c = input_string[i]
            if depth == 0 and c == ",":
                pixel_value_array.append(parse_2D_array(piece)[0])
                piece = ""
            else:
                if c == array_idx_start_marker:
                    if depth == 1: piece += c
                    depth += 1
                elif c == array_idx_end_marker:
                    if depth == 2: piece += c
                    depth -= 1
                else:
                    piece += c

        pixel_value_array.append(parse_2D_array(piece)[0])

        return np.array(pixel_value_array)

    if input_string[0] != array_idx_start_marker:
        pixel_value_array = parse_1D_array(input_string)
    else:
        if input_string[1] != array_idx_start_marker:
            pixel_value_array = parse_2D_array(input_string)
        else:
            pixel_value_array = parse_3D_array(input_string)

    queue_visual_sensory_image_array(pixel_value_array)

def queue_visual_sensory_image_array(img_array):
    pended_input_data_queue.append((VISION_KEYWORD, img_array))