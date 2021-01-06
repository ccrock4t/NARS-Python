"""
    Author: Christian Hahm
    Created: October 9, 2020
"""
"""
    System Parameters
"""
k = 1 # evidential horizon
t = 1 # decision rule (goal decision-making) threshold
MINDFULNESS = 0.5 # between 0-1, how much attention the system allocates to the present moment (overall experience buffer) vs. allocating to ruminating / pondering concepts

"""
    Bags
"""
DEFAULT_BAG_CAPACITY = 30 # how many items can fit in a bag
DEFAULT_BAG_NUMBER_OF_BUCKETS = 101 # how many probability buckets are there? e.g. 101 allows 101 probability values (between [0%, 100%])

"""
    Others
"""
TRUTH_EPSILON = 0.01 #determines the internal precision used for TruthValue calculations.

"""
    Default Input Task Values
"""
DEFAULT_CONCEPT_EXPECTATION = 0.6
DEFAULT_CONCEPT_EXPECTATION_GOAL = 0.6

DEFAULT_JUDGMENT_FREQUENCY = 1.0
DEFAULT_JUDGMENT_CONFIDENCE = 0.9
DEFAULT_JUDGMENT_PRIORITY = 0.8
DEFAULT_JUDGMENT_DURABILITY = 0.5

DEFAULT_QUESTION_PRIORITY = 0.9
DEFAULT_QUESTION_DURABILITY = 0.9

DEFAULT_GOAL_CONFIDENCE = 0.9
DEFAULT_GOAL_PRIORITY = 0.9
DEFAULT_GOAL_DURABILITY = 0.9

DEFAULT_QUEST_PRIORITY = 0.9
DEFAULT_QUEST_DURABILITY = 0.9