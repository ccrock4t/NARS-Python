import queue

from NALGrammar import *
from Global import GlobalGUI
import Config
from NARSDataStructures import Task

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Parses an input string and converts it into a Narsese Task which is fed into NARS
"""

input_queue = queue.Queue()

def add_input(input_string: str):
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
            sentence = parse_sentence(input_string)
            input_queue.put(item=sentence)
    except AssertionError as msg:
        GlobalGUI.print_to_output("INPUT REJECTED: " + str(msg))
        return


def process_next_pending_sentence():
    """
    Processes the next pending sentence if it exists
    :return:
    """
    if input_queue.qsize() > 0:
        sentence = input_queue.get()
        process_sentence(sentence)


def process_sentence(sentence: Sentence):
    GlobalGUI.print_to_output("IN: " + sentence.get_formatted_string())
    # create new task
    task = Task(sentence, is_input_task=True)
    Global.NARS.overall_experience_buffer.put_new_item(task)


def parse_sentence(sentence_string: str):
    """
    Parameter: sentence_string - String of NAL syntax <term copula term>punctuation %frequency;confidence%

    Returns: Sentence parsed from sentence_string
    """
    # Find statement start and statement end
    start_idx = sentence_string.find(StatementSyntax.Start.value)
    assert (start_idx != -1), "Statement start character " + StatementSyntax.Start.value + " not found."

    end_idx = sentence_string.rfind(StatementSyntax.End.value)
    assert (end_idx != -1), "Statement end character " + StatementSyntax.End.value + " not found."

    # Find sentence punctuation
    punctuation_idx = end_idx + 1
    assert (punctuation_idx < len(sentence_string)), "No punctuation found."
    punctuation_str = sentence_string[punctuation_idx]
    punctuation = Punctuation.get_punctuation(punctuation_str)
    assert (punctuation is not None), punctuation_str + " is not punctuation."

    # todo add support for goals
    assert (
                punctuation == Punctuation.Judgment or punctuation == Punctuation.Question), " Currently only accepting Judgments and Questions."

    # Find statement copula, subject string, and predicate string
    subject, predicate, copula, copula_idx = parse_subject_predicate_copula_and_copula_index(
        sentence_string[start_idx:end_idx + 1])

    statement = Statement(subject, predicate, copula)

    # Find Tense, if it exists
    tense = None
    for t in Tense:
        tense_idx = sentence_string.find(t.value)
        if tense_idx != -1:  # found a tense
            tense = Tense.get_tense_from_string(sentence_string[tense_idx: tense_idx + len(t.value)])

    # Find Truth Value, if it exists
    start_truth_val_idx = sentence_string.find(StatementSyntax.TruthValMarker.value)
    middle_truth_val_idx = sentence_string.find(StatementSyntax.TruthValDivider.value)
    end_truth_val_idx = sentence_string.rfind(StatementSyntax.TruthValMarker.value)

    no_truth_value_found = start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx
    if no_truth_value_found:
        # No truth value, use default truth value
        truth_value = TruthValue(Config.DEFAULT_JUDGMENT_FREQUENCY, Config.DEFAULT_JUDGMENT_CONFIDENCE, tense)
    else:
        # Parse truth value from string
        freq = float(sentence_string[start_truth_val_idx + 1:middle_truth_val_idx])
        conf = float(sentence_string[middle_truth_val_idx + 1:end_truth_val_idx])
        truth_value = TruthValue(freq, conf, tense)

    if punctuation == Punctuation.Judgment:
        sentence = Judgment(statement, truth_value)
    elif punctuation == Punctuation.Question:
        sentence = Question(statement)

    return sentence
