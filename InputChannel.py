import time

import numpy as np

import Config
import NALGrammar
import Global
import NALSyntax
import NARSDataStructures
import queue

import NARSGUI

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Parses an input string and converts it into a Narsese Task which is fed into NARS' task buffer
"""

input_queue = queue.Queue()
vision_sensor_keyword = "vision:"


def get_user_input():
    userinput = ""
    while userinput != "exit":
        userinput = input("")
        add_input_string(userinput)


def add_input_string(input_string: str):
    input_string = input_string.replace(" ", "")  # remove all spaces
    try:
        NARS = Global.Global.NARS
        if input_string == "count":
            Global.Global.print_to_output(
                "Memory count (concepts in memory): " + str(len(NARS.memory)))
            Global.Global.print_to_output(
                "Buffer count (tasks in buffer): " + str(len(NARS.experience_task_buffer)))
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
                print("Waiting for NARS to start up...")
                time.sleep(1.0)

            if is_sensory_input_string(input_string):
                # sensory array input (a matrix of RGB or brightness values)
                sentence = process_visual_sensory_input(input_string[len(vision_sensor_keyword):])
            else:
                # regular Narsese input
                sentence = NALGrammar.Sentence.Sentence.new_sentence_from_string(input_string)
            add_input_sentence(sentence)
    except AssertionError as msg:
        Global.Global.print_to_output("INPUT REJECTED: " + str(msg))


def add_input_sentence(sentence: NALGrammar.Sentence.Sentence):
    """
        Pend a sentence to be processed.
        :param sentence:
    """
    input_queue.put(item=sentence)


def process_next_pending_sentence():
    """
        Processes the next pending sentence from the input buffer if one exists
    """
    while input_queue.qsize() > 0:
        sentence = input_queue.get()
        process_sentence(sentence)


def process_sentence(sentence: NALGrammar.Sentence.Sentence):
    """
        Given a Sentence, ingest it into NARS' experience buffer
        :param sentence:
    """
    Global.Global.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = NARSDataStructures.Task(sentence, is_input_task=True)

    if sentence.stamp.get_tense() is NALSyntax.Tense.Eternal:
        # eternal experience
        Global.Global.NARS.experience_task_buffer.put_new(task)
    else:
        # temporal experience
        Global.Global.NARS.event_buffer.put_new(task)


def load_input(filename="input.nal"):
    """
        Load NAL input from a file
    """
    try:
        with open(filename, "r") as f:
            Global.Global.print_to_output("LOADING INPUT FILE: " + filename)
            for line in f.readlines():
                add_input_string(line)
            Global.Global.print_to_output("LOAD INPUT SUCCESS")
    except:
        Global.Global.print_to_output("LOAD INPUT FAIL")


def is_sensory_input_string(input_string):
    return input_string[0:len(vision_sensor_keyword)] == vision_sensor_keyword


def process_visual_sensory_input(input_string):
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

    subject_str = "V" + str(Global.Global.NARS.memory.get_next_percept_id())
    predicate_term = NALGrammar.Term.from_string("[BRIGHT]")

    x_length = 1
    y_length = 1
    z_length = 1

    array_idx_start_marker = NALSyntax.StatementSyntax.ArrayElementIndexStart.value
    array_idx_end_marker = NALSyntax.StatementSyntax.ArrayElementIndexEnd.value

    pixel_value_array = []

    if input_string[0] != array_idx_start_marker:
        # 1D array
        pixel_value_array = input_string.split(",")
        x_length = len(pixel_value_array)
        dim_lengths = (x_length,)  # how many elements in a row
    else:
        if input_string[1] != array_idx_start_marker:
            # 2D array
            depth = 0
            piece = ""
            for i in range(len(input_string)):
                c = input_string[i]
                if depth == 0 and c == ",":
                    pixel_value_array.append(piece.split(","))
                    piece = ""
                else:
                    if c == array_idx_start_marker:
                        depth += 1
                    elif c == array_idx_end_marker:
                        depth -= 1
                    else:
                        piece += c

            pixel_value_array.append(piece.split(","))

            x_length = len(pixel_value_array[0])  # how many elements in a row
            y_length = len(pixel_value_array)  # how many rows

            dim_lengths = (x_length, y_length)
        else:
            # TODO
            # 3D array
            layer_strings = []
            depth = 0
            piece = ""
            for i in range(len(input_string)):
                c = input_string[i]
                if depth == 0 and c == ",":
                    layer_strings.append(piece)
                    piece = ""
                else:
                    piece += c
                    if c == array_idx_start_marker:
                        depth += 1
                    elif c == array_idx_end_marker:
                        depth -= 1
            x_length = len(layer_strings[0][0])  # how many elements in a row
            y_length = len(layer_strings[0])  # how many rows
            z_length = len(layer_strings)  # how many layers
            dim_lengths = (x_length, y_length, z_length)

    atomic_array_term = NALGrammar.ArrayTerm(name=subject_str,
                                             dimensions=dim_lengths)
    statement_array_term = NALGrammar.StatementTerm(subject_term=NALGrammar.CompoundTerm(subterms=[atomic_array_term],
                                                                                         term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                                                    predicate_term=predicate_term,
                                                    copula=NALSyntax.Copula.Inheritance)

    dims = 0
    if z_length == 1:
        if y_length == 1:
            dims = 1
        else:
            dims = 2
    else:
        dims = 3

    def create_truth_value_array(*coord_vars):
        coords = tuple([int(var) for var in coord_vars])
        if len(coords) == 1:
            pixel_value = float(pixel_value_array[coords[0]])
        elif len(coords) == 2:
            pixel_value = float(pixel_value_array[coords[1]][coords[0]])
        elif len(coords) == 3:
            pixel_value = float(pixel_value_array[coords[2]][coords[1]][coords[0]])
        coords = atomic_array_term.convert_absolute_indices_to_relative_indices(coords)
        c = 0
        for coord in coords:
            c += (1.0 - abs(coord))
        c /= dims

        f = pixel_value / 255.0
        if c >= 1:
            c = 0.99
        elif c <= 0.0:
            c = 0.0
        return NALGrammar.TruthValue(frequency=f, confidence=c)

    func_vectorized = np.vectorize(create_truth_value_array)
    truth_value_list = np.fromfunction(function=func_vectorized, shape=dim_lengths)

    default_truth_value = NALGrammar.TruthValue(frequency=Config.DEFAULT_JUDGMENT_FREQUENCY,
                                                confidence=Config.DEFAULT_JUDGMENT_CONFIDENCE)

    return NALGrammar.Judgment(statement=statement_array_term,
                               value=(default_truth_value, truth_value_list))