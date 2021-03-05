from NALGrammar import *
import Global
import Config
from NARSDataStructures import Task
import tkinter as tk
"""
    Author: Christian Hahm
    Created: October 9, 2020
"""
def add_input(input_string):
    try:
        if input_string == "count":
            print("Memory count: " + str(Global.NARS.memory.get_number_of_concepts()))
            print("Buffer count: " + str(Global.NARS.overall_experience_buffer.count))
        else:
            sentence = parse_sentence(input_string)
    except AssertionError as msg:
        print("INPUT REJECTED: " + str(msg))
        return
    process_sentence(sentence)

def process_sentence(sentence):
    print("IN: " + sentence.get_formatted_string())
    # create new task
    task = Task(sentence, is_input_task=True)
    Global.NARS.overall_experience_buffer.put_new_item(task)

def parse_sentence(sentence_string):
    """
    Parameter: sentence_string - String of NAL syntax <term copula term>punctuation %frequency;confidence%

    Returns: Sentence parsed from sentence_string
    """
    # Find statement start and statement end
    start_idx = sentence_string.find(StatementSyntax.Start.value)
    assert(start_idx != -1), "Statement start character " + StatementSyntax.Start.value + " not found."

    end_idx = sentence_string.rfind(StatementSyntax.End.value)
    assert (end_idx != -1), "Statement end character " + StatementSyntax.End.value + " not found."

    # Find sentence punctuation
    punctuation_idx = end_idx + 1
    assert(punctuation_idx < len(sentence_string)), "No punctuation found."
    punctuation_str = sentence_string[punctuation_idx]
    punctuation = Punctuation.get_punctuation(punctuation_str)
    assert (punctuation is not None), punctuation_str + " is not punctuation."

    # todo add support for goals
    assert (punctuation == Punctuation.Judgment or punctuation == Punctuation.Question), " Currently only accepting Judgments and Questions."

    # Find statement copula, subject string, and predicate string
    subject, predicate, copula, copula_idx = parse_subject_predicate_copula_and_copula_index(sentence_string[start_idx:end_idx+1])

    statement = Statement(subject, predicate, copula)

    # Find Tense, if it exists
    tense = None
    for t in Tense:
        tense_idx = sentence_string.find(str(t))
        if tense_idx != -1: # found a tense
            tense = sentence_string[tense_idx: tense_idx + len(t)]

    # Find Truth Value, if it exists
    start_truth_val_idx = sentence_string.find(StatementSyntax.TruthValMarker.value)
    middle_truth_val_idx = sentence_string.find(StatementSyntax.TruthValDivider.value)
    end_truth_val_idx = sentence_string.rfind(StatementSyntax.TruthValMarker.value)

    if start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx:
        # No truth value, use default truth value
        truth_value = TruthValue(Config.DEFAULT_JUDGMENT_FREQUENCY, Config.DEFAULT_JUDGMENT_CONFIDENCE)
    else:
        # Parse truth value from string
        freq = float(sentence_string[start_truth_val_idx+1:middle_truth_val_idx])
        conf = float(sentence_string[middle_truth_val_idx+1:end_truth_val_idx])
        truth_value = TruthValue(freq, conf)

    if punctuation == Punctuation.Judgment:
        sentence = Judgment(statement, truth_value)
    elif punctuation == Punctuation.Question:
        sentence = Question(statement)

    return sentence


