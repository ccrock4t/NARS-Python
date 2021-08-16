"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Specific configuration settings for NARS
"""
"""
    System Parameters
"""
k = 1 # evidential horizon
T = 0.8 # decision rule (goal decision-making) threshold

POSITIVE_THRESHOLD = 2.0/3.0 # frequency must be above this value to be considered "true"
NEGATIVE_THRESHOLD = 1.0/3.0 # frequency must be below this value to be considered "false"

MINDFULNESS = 0.80 # between 0-1, how much attention the system allocates to the present moment (overall experience buffer) [1.0] vs. pondering concepts [0.0]
MEMORY_CONCEPT_CAPACITY = 10000 # how many concepts can this NARS have?
EVENT_BUFFER_CAPACITY = 10
GLOBAL_BUFFER_CAPACITY = 250
CONCEPT_LINK_CAPACITY = 1000 # how many of each concept link can this NARS have?
NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_CONCEPT = 10 # The number of times to look for a semantically related concept to interact with
NUMBER_OF_ATTEMPTS_TO_SEARCH_FOR_SEMANTICALLY_RELATED_BELIEF = 10 # The number of times to look for a semantically related belief to interact with
PRIORITY_DECAY_MULTIPLIER = 0.95 # value in [0,1] multiplied w/ priority during priority decay
PRIORITY_STRENGTHEN_VALUE = 0.02 # priority strengthen multiplier
ACTIONS_PER_CYCLE = 5


"""
    GUI
"""
DEBUG = False # set to true for useful debug statements
ARRAY_SENTENCES_DRAW_INDIVIDUAL_ELEMENTS = False # whether or not to draw each individual element / pixel of an array sentence. Turning this to False results in GUI speedup when viewing array sentences

"""
    Inference
"""
TRUTH_PROJECTION_DECAY = 0.9

"""
    Bags
"""
BAG_DEFAULT_CAPACITY = 5000 # default for how many items can fit in a bag
BAG_NUMBER_OF_BUCKETS = 100 # how many probability buckets are there? e.g. 100 allows 100 probability values in [0%, 100%)

"""
    Tables
"""
TABLE_DEFAULT_CAPACITY = 30

"""
    Other Structures
"""
MAX_EVIDENTIAL_BASE_LENGTH = 20000 # maximum IDs to store documenting evidential base
MAX_INTERACTED_SENTENCES_LENGTH = 20000

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

DEFAULT_GOAL_FREQUENCY = 1.0
DEFAULT_GOAL_CONFIDENCE = 0.9
DEFAULT_GOAL_PRIORITY = 0.9
DEFAULT_GOAL_DURABILITY = 0.9

DEFAULT_QUEST_PRIORITY = 0.9
DEFAULT_QUEST_DURABILITY = 0.9