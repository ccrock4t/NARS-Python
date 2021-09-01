"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Specific configuration settings for NARS
"""
import json

import os
import sys

try:
    try:
        user_config = json.load(open("Config.json"))
    except:
        user_config = json.load(open("../Config.json"))

    """
        System Parameters
    """
    k = user_config["k"]  # evidential horizon
    T = user_config["T"]  # decision rule (goal decision-making) threshold
    MINDFULNESS = user_config["MINDFULNESS"]

    WORKING_CYCLE_TIME = user_config["WORKING_CYCLE_DURATION"]  # time in milliseconds per working cycle

    POSITIVE_THRESHOLD = user_config["POSITIVE_THRESHOLD"]
    NEGATIVE_THRESHOLD = user_config["NEGATIVE_THRESHOLD"]

    MEMORY_CONCEPT_CAPACITY = user_config["MEMORY_CONCEPT_CAPACITY"]  # how many concepts can this NARS have?
    EVENT_BUFFER_CAPACITY = user_config["EVENT_BUFFER_CAPACITY"]
    GLOBAL_BUFFER_CAPACITY = user_config["GLOBAL_BUFFER_CAPACITY"]
    CONCEPT_LINK_CAPACITY = user_config["CONCEPT_LINK_CAPACITY"]  # how many of each concept link can this NARS have?
    NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT = user_config[
        "NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT"]  # The number of times to look for a semantically related concept to interact with
    NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF = user_config[
        "NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF"]  # The number of times to look for a semantically related belief to interact with
    PRIORITY_DECAY_MULTIPLIER = user_config[
        "PRIORITY_DECAY_MULTIPLIER"]  # value in [0,1] multiplied w/ priority during priority decay
    PRIORITY_STRENGTHEN_VALUE = user_config[
        "PRIORITY_STRENGTHEN_VALUE"]  # priority strengthen bor multiplier when concept is activated

    TASKS_PER_CYCLE = user_config["TASKS_PER_CYCLE"]

    """
        GUI
    """
    GUI_USE_INTERFACE = user_config["GUI_USE_INTERFACE"]
    DEBUG = user_config["DEBUG"]  # set to true for useful debug statements
    ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS = user_config[
        "ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS"]  # whether or not to draw each individual element / pixel of an array sentence. Turning this to False results in GUI speedup when viewing array sentences

    """
        Inference
    """
    DESIRE_PROJECTION_DECAY = user_config["DESIRE_PROJECTION_DECAY"]
    EVENT_TRUTH_PROJECTION_DECAY = user_config["EVENT_TRUTH_PROJECTION_DECAY"]
    INTERVAL_SCALE = user_config["INTERVAL_SCALE"]  # higher scale is more granular

    """
        Bags
    """
    BAG_DEFAULT_CAPACITY = user_config["BAG_DEFAULT_CAPACITY"]  # default for how many items can fit in a bag

    """
        Tables
    """
    TABLE_DEFAULT_CAPACITY = user_config["TABLE_DEFAULT_CAPACITY"]

    """
        Other Structures
    """
    MAX_EVIDENTIAL_BASE_LENGTH = user_config[
        "MAX_EVIDENTIAL_BASE_LENGTH"]  # maximum IDs to store documenting evidential base

    """
        Default Input Task Values
    """
    DEFAULT_JUDGMENT_FREQUENCY = user_config["DEFAULT_JUDGMENT_FREQUENCY"]
    DEFAULT_JUDGMENT_CONFIDENCE = user_config["DEFAULT_JUDGMENT_CONFIDENCE"]
    DEFAULT_DISAPPOINT_CONFIDENCE = user_config["DEFAULT_DISAPPOINT_CONFIDENCE"]

    DEFAULT_GOAL_CONFIDENCE = user_config["DEFAULT_GOAL_CONFIDENCE"]

    DEFAULT_JUDGMENT_PRIORITY = user_config["DEFAULT_JUDGMENT_PRIORITY"]
    DEFAULT_QUESTION_PRIORITY = user_config["DEFAULT_QUESTION_PRIORITY"]
    DEFAULT_GOAL_PRIORITY = user_config["DEFAULT_GOAL_PRIORITY"]
    DEFAULT_QUEST_PRIORITY = user_config["DEFAULT_QUEST_PRIORITY"]

    DEFAULT_GOAL_FREQUENCY = user_config["DEFAULT_GOAL_FREQUENCY"]

except:
    assert  False,"Config could not be loaded."



