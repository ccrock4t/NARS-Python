import time

import numpy as np

import Config
import NALGrammar.Sentences
import Global
import NALSyntax
import NARSDataStructures
import queue

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
                sentence = NALGrammar.Sentences.new_sentence_from_string(input_string)
            add_input_sentence(sentence)
    except AssertionError as msg:
        Global.Global.print_to_output("INPUT REJECTED: " + str(msg))


def add_input_sentence(sentence: NALGrammar.Sentences.Sentence):
    """
        Pend a sentence to be processed.
        :param sentence:
    """
    input_queue.put(item=sentence)


def process_pending_sentence():
    """
        Processes the next pending sentence from the input buffer if one exists
    """
    while input_queue.qsize() > 0:
        sentence = input_queue.get()
        process_sentence(sentence)
    if Config.DEBUG: Global.Global.debug_print("Input Channel Size: " + str(input_queue.qsize()))


def process_sentence(sentence: NALGrammar.Sentences.Sentence):
    """
        Given a Sentence, ingest it into NARS
        :param sentence:
    """
    Global.Global.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = NARSDataStructures.Other.Task(sentence, is_input_task=True)

    if isinstance(sentence, NALGrammar.Sentences.Judgment) and sentence.is_event():
        # put events on the temporal chain
        Global.Global.NARS.temporal_module.put_new(task)
        # process the task into NARS
        Global.Global.NARS.process_task(task)
    else:
        Global.Global.NARS.global_buffer.put_new(task)


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
    predicate_term = NALGrammar.Terms.Term.from_string("[BRIGHT]")

    x_length = 1
    y_length = 1
    z_length = 1

    array_idx_start_marker = NALSyntax.StatementSyntax.ArrayElementIndexStart.value
    array_idx_end_marker = NALSyntax.StatementSyntax.ArrayElementIndexEnd.value

    def parse_1D_array(input_string):
        # 1D array
        pixel_value_array = input_string.split(",")
        x_length = len(pixel_value_array)
        dim_lengths = (x_length,)  # how many elements in a row
        return pixel_value_array, dim_lengths

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

        dim_lengths = (x_length, y_length)
        return pixel_value_array, dim_lengths

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

        x_length = len(pixel_value_array[0][0])  # how many elements in a row
        y_length = len(pixel_value_array[0])  # how many rows
        z_length = len(pixel_value_array)  # how many layers
        dim_lengths = (x_length, y_length, z_length)

        return pixel_value_array, dim_lengths

    if input_string[0] != array_idx_start_marker:
        pixel_value_array, dim_lengths = parse_1D_array(input_string)
    else:
        if input_string[1] != array_idx_start_marker:
            pixel_value_array, dim_lengths = parse_2D_array(input_string)
        else:
            pixel_value_array, dim_lengths = parse_3D_array(input_string)

    # fast fourier transform
    f = np.fft.fft2(pixel_value_array) #todo does this work on rgb image?
    fshift = np.fft.fftshift(f)
    pixel_value_array = 20*np.log(np.abs(fshift))

    #create Narsese array

    atomic_array_term = NALGrammar.Terms.ArrayTerm(name=subject_str,
                                             dimensions=dim_lengths)
    statement_array_term = NALGrammar.Terms.StatementTerm(subject_term=NALGrammar.Terms.CompoundTerm(subterms=[atomic_array_term],
                                                                                         term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                                                    predicate_term=predicate_term,
                                                    copula=NALSyntax.Copula.Inheritance)

    max_value = np.max(pixel_value_array)

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
        c /= len(dim_lengths)

        f = pixel_value / max_value
        if c >= 1:
            c = 0.99
        elif c <= 0.0:
            c = 0.0
        return NALGrammar.Values.TruthValue(frequency=f, confidence=c)

    func_vectorized = np.vectorize(create_truth_value_array)
    truth_value_list = np.fromfunction(function=func_vectorized, shape=dim_lengths)

    default_truth_value = NALGrammar.Values.TruthValue(frequency=Config.DEFAULT_JUDGMENT_FREQUENCY,
                                                confidence=Config.DEFAULT_JUDGMENT_CONFIDENCE)

    return NALGrammar.Sentences.Judgment(statement=statement_array_term,
                               value=(default_truth_value, truth_value_list))
