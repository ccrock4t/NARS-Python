import enum
import Config
import Global
import NALInferenceRules
import NALSyntax
import numpy as np

"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""

class Array():
    def __init__(self, dim_lengths, truth_values = None, occurrence_time=None):
        """
        :param parent: Name of the array term
        :param dim_lengths: the number of elements in each dimensional axis (x,y,z);
            provides a granularity = 2.0/(dim_length - 1)
        """
        self.is_array = True
        self.dimensions = dim_lengths
        self.num_of_dimensions = len(dim_lengths)
        assert self.num_of_dimensions <= 3, "ERROR: Does not support more than 3 dimensions"
        assert self.num_of_dimensions > 0, "ERROR: Use Atomic Term instead of zero-dimensional array"

        if self.num_of_dimensions == 1:
            dim_lengths = (dim_lengths[0], 1, 1)
        elif self.num_of_dimensions == 2:
            dim_lengths = (dim_lengths[0], dim_lengths[1], 1)

        self.dim_lengths = dim_lengths
        self.offsets = []
        for i in range(self.num_of_dimensions):
            self.offsets.append((dim_lengths[i] - 1) / 2.0)

        if isinstance(self, Judgment) or isinstance(self, Goal):
            self.image_array = [] # image_array is used to visualize an array of judgments/goals activations
        else:
            self.image_array = None

        z_array = []
        z_image_array = []
        for z in np.linspace(-1.0, 1.0, num=dim_lengths[2]):
            y_array = []
            y_image_array = []
            for y in np.linspace(-1.0, 1.0, num=dim_lengths[1]):
                x_array = []
                x_image_array = []
                for x in np.linspace(-1.0, 1.0, num=dim_lengths[0]):
                    if self.num_of_dimensions == 1:
                        formatted_indices = [x]
                    elif self.num_of_dimensions == 2:
                        formatted_indices = [x, y]
                    elif self.num_of_dimensions == 3:
                        formatted_indices = [x, y, z]

                    if isinstance(self, StatementTerm):
                        array_term: ArrayTerm = self.get_subject_term().subterms[0]
                        atomic_element = array_term[formatted_indices] # get atomic array element
                        element = StatementTerm(subject_term=CompoundTerm(subterms=[atomic_element],
                                                                    term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                                                predicate_term=self.get_predicate_term(),
                                                copula=NALSyntax.Copula.Inheritance)
                    elif isinstance(self, Judgment):
                        truth_value: TruthValue = truth_values[len(z_array)][len(y_array)][len(x_array)]
                        statement_element: StatementTerm = self.statement[formatted_indices] # get atomic array element
                        element = Judgment(statement=statement_element,
                                           value=truth_value,
                                           occurrence_time=occurrence_time)
                        x_image_array.append(truth_value.frequency * 255)
                    else:
                        element = AtomicArrayElementTerm(array_term=self, indices=formatted_indices)

                    x_array.append(element)
                y_array.append(np.array(x_array))
                if self.image_array is not None: y_image_array.append(x_image_array)
            z_array.append(np.array(y_array))
            if self.image_array is not None: z_image_array.append(y_image_array)
        if self.image_array is not None:
            if len(self.image_array ) == 1: z_image_array = z_image_array[0]
            self.image_array = np.array(z_image_array).astype(np.uint8)
            while len(self.image_array) == 1:
                self.image_array = self.image_array[0]

        self.array = np.array(z_array)

    def __getitem__(self, indices):
        """
            Define the indexing operator [], to get array elements.
            Pass the indices as an indexible item

            The values in the tuple can be either absolute values e.g. (0,1,2...N) or
            relative indices e.g. (0.5, 0.75), but must be of the same type for the whole tuple.
        :param indices: a tuple of the indices to get
        :return: Array element term at index
        """
        assert len(indices)<=self.num_of_dimensions,"Error: Number of indices must match number of dimensions"
        if isinstance(indices[0],float): indices = self._convert_relative_indices_to_array_indices(indices)

        if self.num_of_dimensions == 1:
            indices = (indices[0], 0, 0)
        elif self.num_of_dimensions == 2:
            indices = (indices[0], indices[1], 0)

        return self.array[indices[2]][indices[1]][indices[0]]

    def _convert_relative_indices_to_array_indices(self, indices):
        assert len(indices) == self.num_of_dimensions, "Error: Number of indices must match number of dimensions"
        # un-offset and un-regularize
        new_indices = []
        for i in range(self.num_of_dimensions):
            new_indices.append(int(indices[i] * self.offsets[i] + self.offsets[i]))
        return tuple(new_indices)

    def _convert_array_indices_to_relative_indices(self, indices):
        assert len(indices) == self.num_of_dimensions, "Error: Number of indices must match number of dimensions"
        # offset then regularize
        new_indices = []
        for i in range(self.num_of_dimensions):
            new_indices.append((indices[i] - self.offsets[i]) // self.offsets[i])
        return tuple(new_indices)

    def get_dimensions(self):
        return self.dimensions

class Sentence(Array):
    """
        sentence ::= <statement><punctuation> <tense> %<value>%
    """

    def __init__(self, statement, value, punctuation, occurrence_time=None):
        """

        :param statement:
        :param value: Pass as a tuple for array sentences (overall_truth, list_of_element_truth_values)
        :param punctuation:
        :param occurrence_time:
        :param array_truth_values:
        """
        assert_punctuation(punctuation)
        assert isinstance(statement,StatementTerm),"ERROR: Judgment needs a statement"
        self.is_array = False
        self.statement = statement
        self.punctuation: NALSyntax.Punctuation = punctuation
        self.stamp = Stamp(self_sentence=self,occurrence_time=occurrence_time)

        if statement.is_array:
            Array.__init__(self,statement.get_dimensions(),truth_values=value[1])
            self.value = value[0]
        else:
            self.value = value  # truth-value (for Judgment) or desire-value (for Goal) or None (for Question)

    def __str__(self):
        return self.get_formatted_string()

    def __hash__(self):
        """
            A Sentence is identified by its ID

            :return: Sentence ID
        """
        return self.stamp.id

    def is_event(self):
        return self.stamp.get_tense() != NALSyntax.Tense.Eternal

    def get_formatted_string(self):
        string = self.get_formatted_string_no_id()
        string = Global.Global.MARKER_SENTENCE_ID + str(self.stamp.id) + Global.Global.MARKER_ID_END + string
        return string

    def get_formatted_string_no_id(self):
        string = self.statement.get_formatted_string() + str(self.punctuation.value)
        if self.stamp.get_tense() != NALSyntax.Tense.Eternal: string = string + " " + self.stamp.get_tense().value
        if self.value is not None: string = string + " " + self.value.get_formatted_string()
        return string

    def __getitem__(self, indices):
        """
            Define the indexing operator [], to get array elements.
            Pass the indices as a tuple.
        """
        assert isinstance(self.statement, ArrayTerm),"ERROR: Cannot index non-array"
        return self.statement[indices], self.array[indices]

    @classmethod
    def new_sentence_from_string(cls, sentence_string: str):
        """
            :param sentence_string - String of NAL syntax <term copula term>punctuation %frequency;confidence%

            :returns Sentence parsed from sentence_string
        """
        sentence_string = sentence_string.replace(" ", "") # remove all spaces

        # Find statement start and statement end
        start_idx = sentence_string.find(NALSyntax.StatementSyntax.Start.value)
        assert (start_idx != -1), "Statement start character " + NALSyntax.StatementSyntax.Start.value + " not found."

        end_idx = sentence_string.rfind(NALSyntax.StatementSyntax.End.value)
        assert (end_idx != -1), "Statement end character " + NALSyntax.StatementSyntax.End.value + " not found."

        # Find sentence punctuation
        punctuation_idx = end_idx + 1
        assert (punctuation_idx < len(sentence_string)), "No punctuation found."
        punctuation_str = sentence_string[punctuation_idx]
        punctuation = NALSyntax.Punctuation.get_punctuation(punctuation_str)
        assert (punctuation is not None), punctuation_str + " is not punctuation."

        # Find Truth Value, if it exists
        start_truth_val_idx = sentence_string.find(NALSyntax.StatementSyntax.TruthValMarker.value, punctuation_idx)
        middle_truth_val_idx = sentence_string.find(NALSyntax.StatementSyntax.TruthValDivider.value, punctuation_idx)
        end_truth_val_idx = sentence_string.rfind(NALSyntax.StatementSyntax.TruthValMarker.value, punctuation_idx)

        truth_value_found = not (start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx)
        freq = None
        conf = None
        if truth_value_found:
            # Parse truth value from string
            freq = float(sentence_string[start_truth_val_idx + 1:middle_truth_val_idx])
            conf = float(sentence_string[middle_truth_val_idx + 1:end_truth_val_idx])

        # create the statement
        statement_string = sentence_string[start_idx:end_idx + 1]

        if sentence_string[2] == NALSyntax.TermConnector.Array.value:
            if freq is None:
                # No truth value, use default truth value
                freq = Config.DEFAULT_JUDGMENT_FREQUENCY
                conf = Config.DEFAULT_JUDGMENT_CONFIDENCE
            sentence = Sentence.new_percept_from_string(statement_string, TruthValue(freq, conf))
        else:
            # create standard statement from string
            statement = StatementTerm.from_string(statement_string)

            if punctuation == NALSyntax.Punctuation.Judgment:
                if freq is None:
                    # No truth value, use default truth value
                    freq = Config.DEFAULT_JUDGMENT_FREQUENCY
                    conf = Config.DEFAULT_JUDGMENT_CONFIDENCE
                sentence = Judgment(statement, TruthValue(freq, conf))
            elif punctuation == NALSyntax.Punctuation.Question:
                sentence = Question(statement)
            elif punctuation == NALSyntax.Punctuation.Goal:
                if freq is None:
                    # No truth value, use default truth value
                    freq = Config.DEFAULT_GOAL_FREQUENCY
                    conf = Config.DEFAULT_GOAL_CONFIDENCE
                sentence = Goal(statement, DesireValue(freq,conf))
            else:
                assert False,"Error: No Punctuation!"

        # Find Tense, if it exists
        # otherwise mark it as eternal
        tense = NALSyntax.Tense.Eternal
        for t in NALSyntax.Tense:
            if t != NALSyntax.Tense.Eternal:
                tense_idx = sentence_string.find(t.value)
                if tense_idx != -1:  # found a tense
                    tense = NALSyntax.Tense.get_tense_from_string(sentence_string[tense_idx: tense_idx + len(t.value)])
                    break

        if tense == NALSyntax.Tense.Present:
            #Mark present tense event as happening right now!
            sentence.stamp.occurrence_time = Global.Global.get_current_cycle_number()

        return sentence

    @classmethod
    def new_percept_from_string(cls, percept_sentence_string, truth_value, occurrence_time=None):
        """
            :param: percept_sentence_string - String of NAL syntax ({@S([...])} --> [t])
            :param: truth_value - Truth-value of the overall sentence

            Where @S is an array term followed by element-level truth-values separated by brackets and commas.
            1D (sequence):
             @S(f;c,...,f;c)"

             2D (matrix):
             @S(
                [f;c,...,f;c],
                [...,...,...],
                [f;c,...,f;c]
                )"

            3D (tensor):
            @S(
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
                )"

            Returns: Percept
        """
        # this input is a sensory percept
        copula, copula_idx = get_top_level_copula(percept_sentence_string)
        assert (copula is not None), "ERROR: Copula not found. Exiting.."

        subject_str = percept_sentence_string[1:copula_idx]  # get subject string {@S([])}
        predicate_str = percept_sentence_string[copula_idx + len(copula.value):-1]  # get predicate string [t]
        predicate_term = Term.from_string(predicate_str)
        assert predicate_term.is_intensional_set(), "ERROR: Predicate term must be an intensional set"

        array_start_bracket_idx = subject_str.find(NALSyntax.StatementSyntax.ArrayElementTruthValuesStart.value)
        array_end_bracket_idx = subject_str.rfind(NALSyntax.StatementSyntax.ArrayElementTruthValuesEnd.value)

        #get only the truth values, e.g. [...],[...],[...]
        truth_value_array_str = subject_str[array_start_bracket_idx + 1:array_end_bracket_idx]
        assert len(truth_value_array_str) > 0, "Percept should contain at least one truth value"

        array_term_name = subject_str[2:array_start_bracket_idx]

        x_length = 1
        y_length = 1
        z_length = 1

        array_idx_start_marker = NALSyntax.StatementSyntax.ArrayElementIndexStart.value
        array_idx_end_marker = NALSyntax.StatementSyntax.ArrayElementIndexEnd.value

        truth_value_str_array = []

        if truth_value_array_str[0] != array_idx_start_marker:
            # 1D array
            truth_value_str_array = truth_value_array_str.split(",")
            x_length = len(truth_value_str_array)
            dim_lengths = (x_length,) # how many elements in a row
        else:
            if truth_value_array_str[1] != array_idx_start_marker:
                #2D array
                depth = 0
                piece = ""
                for i in range(len(truth_value_array_str)):
                    c = truth_value_array_str[i]
                    if depth == 0 and c == ",":
                        truth_value_str_array.append(piece.split(","))
                        piece = ""
                    else:
                        if c == array_idx_start_marker:
                            depth +=1
                        elif c == array_idx_end_marker:
                            depth -= 1
                        else:
                            piece += c

                truth_value_str_array.append(piece.split(","))

                x_length = len(truth_value_str_array[0]) # how many elements in a row
                y_length = len(truth_value_str_array) # how many rows

                dim_lengths = (x_length, y_length)
            else:
                #TODO
                # 3D array
                layer_strings = []
                depth = 0
                piece = ""
                for i in range(len(truth_value_array_str)):
                    c = truth_value_array_str[i]
                    if depth == 0 and c == ",":
                        layer_strings.append(piece)
                        piece = ""
                    else:
                        piece += c
                        if c == array_idx_start_marker:
                            depth +=1
                        elif c == array_idx_end_marker:
                            depth -= 1
                x_length = len(layer_strings[0][0])  # how many elements in a row
                y_length = len(layer_strings[0])  # how many rows
                z_length = len(layer_strings) # how many layers
                dim_lengths = (x_length, y_length, z_length)

        atomic_array_term = ArrayTerm(name=array_term_name,
                                      dim_lengths=dim_lengths)
        statement_array_term = StatementTerm(subject_term=CompoundTerm(subterms=[atomic_array_term],
                                              term_connector=NALSyntax.TermConnector.ExtensionalSetStart),
                                              predicate_term=predicate_term,
                                              copula=copula)

        z_truth_value_elements = []
        # iterate over every element / truth-value
        for z in range(z_length):
            y_truth_value_elements = []
            for y in range(y_length):
                x_truth_value_elements = []
                for x in range(x_length):
                    if y_length == 1 and z_length == 1:
                        truth_value_str_parts = truth_value_str_array[x].split(";")
                    elif z_length == 1:
                        truth_value_str_parts = truth_value_str_array[y][x].split(";")
                    else:
                        truth_value_str_parts = truth_value_str_array[z][y][x].split(";")

                    assert len(truth_value_str_parts) == 2, "ERROR: Truth value should only consist of 2 values"
                    element_truth_value = TruthValue(float(truth_value_str_parts[0]),float(truth_value_str_parts[1]))
                    x_truth_value_elements.append(element_truth_value)
                y_truth_value_elements.append(x_truth_value_elements)
            z_truth_value_elements.append(y_truth_value_elements)

        truth_value_list = z_truth_value_elements

        percept = Judgment(statement=statement_array_term,
                 value=(truth_value, truth_value_list))

        return percept

    @classmethod
    def may_interact(cls,j1,j2):
        """
            2 Sentences may interact if:
                #1. Neither is "None"
                #2. They are not the same Sentence
                #3. They have not interacted previously
                #4. One is not in the other's evidential base
                #5. They do not have overlapping evidential base
        :param j1:
        :param j2:
        :return: Are the sentence allowed to interact for inference
        """
        if j1 is None or j2 is None: return False
        if j1.stamp.id == j2.stamp.id: return False
        if j1 in j2.stamp.interacted_sentences: return False # don't need to check the inverse, since they are added mutually
        if j1 in j2.stamp.evidential_base or j2 in j1.stamp.evidential_base: return False
        if j1.stamp.evidential_base.has_evidential_overlap(j2.stamp.evidential_base): return False
        return True


class Judgment(Sentence):
    """
        judgment ::= <statement>. %<truth-value>%
    """

    def __init__(self, statement, value,occurrence_time=None):
        Sentence.__init__(self,statement, value, NALSyntax.Punctuation.Judgment,occurrence_time=occurrence_time)

    def is_positive(self):
        """
            :returns: Is this statement True? (does it have more positive evidence than negative evidence?)
        """
        return NALInferenceRules.TruthValueFunctions.Expectation(self.value.frequency, self.value.confidence) >= Config.POSITIVE_THRESHOLD

    def is_negative(self):
        """
            :returns: Is this statement False? (does it have more negative evidence than positive evidence?)
        """
        return NALInferenceRules.TruthValueFunctions.Expectation(self.value.frequency, self.value.confidence) < Config.NEGATIVE_THRESHOLD


class Question(Sentence):
    """
        question ::= <statement>? %<truth-value>%
    """

    def __init__(self, statement):
        assert_statement_term(statement)
        Sentence.__init__(self,statement, None, NALSyntax.Punctuation.Question)


class Goal(Sentence):
    """
        goal ::= <statement>! %<desire-value>%
    """

    def __init__(self, statement, value):
        assert_statement_term(statement)
        Sentence.__init__(self,statement, value, NALSyntax.Punctuation.Goal)

class EvidentialValue:
    """
        <frequency, confidence>
    """

    def __init__(self, frequency, confidence):
        assert (isinstance(frequency, float) and frequency >= 0.0 and frequency <= 1.0), "ERROR: Frequency must be a float in [0,1]"
        assert (isinstance(confidence, float) and confidence > 0.0 and confidence < 1.0), "ERROR: Confidence must be a float (0,1)"
        self.frequency = frequency
        self.confidence = confidence

    def get_formatted_string(self):
        assert False, "Formatted string not defined for Evidential Value base class"


class DesireValue(EvidentialValue):
    """
        <frequency, confidence>
        For a virtual judgement S |=> D,
        how much the associated statement S implies the overall desired state of NARS, D
    """

    def __init__(self, frequency, confidence):
        super().__init__(frequency=frequency, confidence=confidence)

    def get_formatted_string(self):
        return str(NALSyntax.StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(NALSyntax.StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(NALSyntax.StatementSyntax.TruthValMarker.value)


class TruthValue(EvidentialValue):
    """
        <frequency, confidence>
        Describing the evidential basis for the associated statement to be true
    """

    def __init__(self, frequency=Config.DEFAULT_JUDGMENT_FREQUENCY, confidence=Config.DEFAULT_JUDGMENT_CONFIDENCE):
        super().__init__(frequency=frequency, confidence=confidence)

    def get_formatted_string(self):
        return str(NALSyntax.StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(NALSyntax.StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(NALSyntax.StatementSyntax.TruthValMarker.value)

class Stamp:
    """
        Defines the metadata of a sentence, including
        when it was created, its occurrence time (when is its truth value valid),
        evidential base, etc.
    """
    def __init__(self, self_sentence, occurrence_time=None):
        self.id = Global.Global.NARS.memory.get_next_stamp_id()
        self.creation_time = Global.Global.get_current_cycle_number()  # when was this stamp created (in inference cycles)?
        self.occurrence_time = occurrence_time
        self.sentence = self_sentence
        self.evidential_base = EvidentialBase(self_sentence=self_sentence)
        self.interacted_sentences = []  # list of sentence this sentence has already interacted with
        self.from_one_premise_inference = False # is this sentence derived from one-premise inference?

    def get_tense(self):
        if self.occurrence_time is None:
            return NALSyntax.Tense.Eternal

        current_cycle = Global.Global.get_current_cycle_number()
        if self.occurrence_time < current_cycle:
            return NALSyntax.Tense.Past
        elif self.occurrence_time == current_cycle:
            return NALSyntax.Tense.Present
        elif self.occurrence_time > current_cycle:
            return NALSyntax.Tense.Future

    def mutually_add_to_interacted_sentences(self, other_sentence):
        self.interacted_sentences.append(other_sentence)
        if len(self.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
            self.interacted_sentences.pop(0)

        other_sentence.stamp.interacted_sentences.append(self.sentence)
        if len(other_sentence.stamp.interacted_sentences) > Config.MAX_INTERACTED_SENTENCES_LENGTH:
            other_sentence.stamp.interacted_sentences.pop(0)



class EvidentialBase:
    """
        Stores history of how the sentence was derived
    """
    def __init__(self,self_sentence):
        """
        :param id: Sentence ID
        """
        self.base = [self_sentence]  # array of sentences

    def __iter__(self):
        return iter(self.base)

    def __contains__(self, object):
        return object in self.base

    def merge_sentence_evidential_base_into_self(self, sentence):
        """
            Merge a Sentence's evidential base into self, including the Sentence itself.
            This function assumes the base to merge does not have evidential overlap with this base
            #todo figure out good way to store evidential bases such that older evidence is purged on overflow
        """
        for sentence in sentence.stamp.evidential_base:
            self.base.append(sentence)

        while len(self.base) > Config.MAX_EVIDENTIAL_BASE_LENGTH:
            self.base.pop(0)

    def has_evidential_overlap(self, other_base):
        """
            Check does other base has overlapping evidence with self?
            O(M + N)
            https://stackoverflow.com/questions/3170055/test-if-lists-share-any-items-in-python
        """
        return not set(self.base).isdisjoint(other_base.base)


class Term:
    """
        Base class for all terms.
    """

    def __init__(self, term_string):
        assert isinstance(term_string, str), term_string + " must be a str"
        self.string = term_string
        self.syntactic_complexity = self._calculate_syntactic_complexity()

    def get_formatted_string(self):
        return self.string

    def __eq__(self, other):
        """
            Terms are equal if their strings are the same
        """
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return self.get_formatted_string()

    def _calculate_syntactic_complexity(self):
        assert False, "Complexity not defined for Term base class"

    def is_operation(self):
        return False

    def contains_variable(self):
        return VariableTerm.VARIABLE_SYM in str(self) \
                or VariableTerm.QUERY_SYM in str(self)

    @classmethod
    def from_string(cls, term_string):
        """
            Determine if it is an atomic term (e.g. "A") or a statement/compound term (e.g. (&&,A,B,..) or (A --> B))
            or variable term and creates the corresponding Term.

            :param term_string - String from which to construct the term
            :returns Term constructed using the string
        """
        is_set_term = NALSyntax.TermConnector.is_set_bracket_start(term_string[0])

        if term_string[0] == NALSyntax.StatementSyntax.Start.value:
            """
                Compound or Statement Term
            """
            assert (term_string[-1] == NALSyntax.StatementSyntax.End.value), "Compound/Statement term must have ending parenthesis: " + term_string

            copula, copula_idx = get_top_level_copula(term_string)
            if copula is None:
                # compound term
                term = CompoundTerm.from_string(term_string)
            else:
                term = StatementTerm.from_string(term_string)
        elif is_set_term:
            term = CompoundTerm.from_string(term_string)
        elif term_string[0] == VariableTerm.VARIABLE_SYM or term_string[0] == VariableTerm.QUERY_SYM:
            # variable term
            dependency_list_start_idx = term_string.find("(")
            if dependency_list_start_idx == -1:
                variable_name = term_string[1:]
                dependency_list_string = ""
            else:
                variable_name = term_string[1:dependency_list_start_idx]
                dependency_list_string = term_string[term_string.find("(") + 1:term_string.find(")")]

            term = VariableTerm.from_string(variable_name=variable_name,
                                            variable_type_symbol=term_string[0],
                                            dependency_list_string=dependency_list_string)
        else:
            term = AtomicTerm(term_string)

        return term

    @classmethod
    def simplify(cls, term):
        if isinstance(term,AtomicTerm):
            return term
        elif isinstance(term, StatementTerm):
            simplified_subject_term = Term.simplify(term.get_subject_term())
            simplified_predicate_term = Term.simplify(term.get_predicate_term())
            return StatementTerm(subject_term=simplified_subject_term, predicate_term=simplified_predicate_term, copula=term.copula)
        elif isinstance(term, CompoundTerm):
            if term.connector is NALSyntax.TermConnector.Negation:
                if len(term.subterms) == 1:
                    pass
            elif term.connector is NALSyntax.TermConnector.ExtensionalDifference:pass
            elif term.connector is NALSyntax.TermConnector.IntensionalDifference:pass
            elif term.connector is NALSyntax.TermConnector.ExtensionalImage:pass
            elif term.connector is NALSyntax.TermConnector.IntensionalImage:pass
            return term

class VariableTerm(Term):
    class Type(enum.Enum):
        Independent = 1
        Dependent = 2
        Query = 3

    VARIABLE_SYM = "#"
    QUERY_SYM = "?"

    def __init__(self, variable_name: str, variable_type: Type, dependency_list=None):
        """

        :param variable_string: variable name
        :param variable_type: type of variable
        :param dependency_list: array of independent variables this variable depends on
        """
        # todo parse variable terms from input strings
        self.variable_name = variable_name
        self.variable_type = variable_type
        self.variable_symbol = VariableTerm.QUERY_SYM if variable_type == VariableTerm.Type.Query else VariableTerm.VARIABLE_SYM
        self.dependency_list = dependency_list
        super().__init__(self.get_formatted_string())

    def get_formatted_string(self):
        dependency_string = ""
        if self.dependency_list is not None:
            dependency_string = "("
            for dependency in self.dependency_list:
                dependency_string = dependency_string + str(dependency) + NALSyntax.StatementSyntax.TermDivider.value

            dependency_string = dependency_string[0:-1] + ")"

        return self.variable_symbol + self.variable_name + dependency_string

    @classmethod
    def from_string(cls, variable_name: str, variable_type_symbol: str, dependency_list_string: str):
        # parse dependency list
        dependency_list = None

        if len(dependency_list_string) > 0:
            dependency_list = []

        type = None
        if variable_type_symbol == VariableTerm.QUERY_SYM:
            type = VariableTerm.Type.Query
        elif variable_type_symbol == VariableTerm.VARIABLE_SYM:
            if dependency_list is None:
                type = VariableTerm.Type.Independent
            else:
                type = VariableTerm.Type.Dependent

        assert type is not None, "Error: Variable type symbol invalid"
        return cls(variable_name, type, dependency_list)

    def _calculate_syntactic_complexity(self):
        if self.dependency_list is None:
            return 1
        else:
            return 1 + len(self.dependency_list)


class AtomicTerm(Term):
    """
        An atomic term, named by a valid word.
    """

    def __init__(self, term_string):
        """
        Input:
            term_string = name of the term
        """
        assert (AtomicTerm.is_valid_term(term_string)), term_string + " is not a valid Atomic Term name."
        super().__init__(term_string)

    def _calculate_syntactic_complexity(self):
        return 1

    @classmethod
    def is_valid_term(cls, term_string):
        for char in term_string:
            if char not in NALSyntax.valid_term_chars: return False
        return True

class CompoundTerm(Term):
    """
        A term that contains multiple atomic subterms connected by a connector (including copula).

        (Connector T1, T2, ..., Tn)
    """

    def __init__(self, subterms: [Term], term_connector: NALSyntax.TermConnector = None):
        """
        Input:
            subterms: array of immediate subterms

            connector: subterm connector
        """
        self.connector = term_connector  # sets are represented by the opening bracket as the connector, { or [

        if term_connector is not None:
            if len(subterms) > 1 \
                    and NALSyntax.TermConnector.is_order_invariant(term_connector):
                # order doesn't matter, alphabetize so the system can recognize the same term
                subterms.sort(key=lambda t: str(t))

            is_extensional_set = (term_connector.value == NALSyntax.TermConnector.ExtensionalSetStart.value)
            is_intensional_set = (term_connector.value == NALSyntax.TermConnector.IntensionalSetStart.value)

            is_set = is_extensional_set or is_intensional_set

            if is_set and len(subterms) > 1:
                # multi_component_set
                # todo handle multi-component sets better
                singleton_set_subterms = []

                for subterm in subterms:
                    # decompose the set into an intersection of singleton sets
                    singleton_set_subterm = CompoundTerm.from_string(self.connector.value + str(subterm) + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value)
                    singleton_set_subterms.append(singleton_set_subterm)

                subterms = singleton_set_subterms

                # set new term connector as intersection
                if is_extensional_set:
                    self.connector = NALSyntax.TermConnector.IntensionalIntersection
                elif is_intensional_set:
                    self.connector = NALSyntax.TermConnector.ExtensionalIntersection

        self.subterms: [Term] = subterms

        Term.__init__(self,term_string=self.get_formatted_string())

    def is_intensional_set(self):
        return self.connector == NALSyntax.TermConnector.IntensionalSetStart

    def is_extensional_set(self):
        return self.connector == NALSyntax.TermConnector.ExtensionalSetStart

    def is_set(self):
        return self.is_intensional_set() or self.is_extensional_set()

    def get_formatted_string(self):
        if self.is_set():
            string = self.connector.value
        else:
            string = self.connector.value + NALSyntax.StatementSyntax.TermDivider.value

        for subterm in self.subterms:
            string = string + subterm.get_formatted_string() + NALSyntax.StatementSyntax.TermDivider.value

        string = string[:-1] # remove the final term divider

        if self.is_set():
            return string + NALSyntax.TermConnector.get_set_end_connector_from_set_start_connector(self.connector).value
        else:
            return NALSyntax.StatementSyntax.Start.value + string + NALSyntax.StatementSyntax.End.value

    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        count = 0
        if self.connector is not None:
            count = 1 # the term connector
        for subterm in self.subterms:
            count = count + subterm._calculate_syntactic_complexity()
        return count


    @classmethod
    def from_string(cls, compound_term_string):
        """
            Create a compound term from a string representing a compound term
        """
        subterms, connector = cls.parse_toplevel_subterms_and_connector(compound_term_string)
        return cls(subterms, connector)

    @classmethod
    def parse_toplevel_subterms_and_connector(cls, compound_term_string):
        """
            Parse out all top-level subterms from a string representing a compound term

            compound_term_string - a string representing a compound term
        """
        compound_term_string = compound_term_string.replace(" ","")
        subterms = []
        internal_string = compound_term_string[1:-1] # string with no outer parentheses () or set brackets [], {}

        # check for intensional/extensional set [a,b], {a,b}
        connector = NALSyntax.TermConnector.get_term_connector_from_string(compound_term_string[0])
        if connector is None:
            # otherwise check for regular Term/Statement connectors
            if internal_string[1] == NALSyntax.StatementSyntax.TermDivider.value:
                connector_string = internal_string[0] # Term connector
            else:
                connector_string = internal_string[0:2] # Statement connector
            connector = NALSyntax.TermConnector.get_term_connector_from_string(connector_string)

            assert (internal_string[
                        len(
                            connector.value)] == NALSyntax.StatementSyntax.TermDivider.value), "Connector not followed by comma in CompoundTerm string " + compound_term_string
            internal_string = internal_string[len(connector.value) + 1:]

        assert (connector is not None), "Connector could not be parsed from CompoundTerm string."

        depth = 0
        subterm_string = ""
        for i, c in enumerate(internal_string):
            if c == NALSyntax.StatementSyntax.Start.value or NALSyntax.TermConnector.is_set_bracket_start(c):
                depth += 1
            elif c == NALSyntax.StatementSyntax.End.value or NALSyntax.TermConnector.is_set_bracket_end(c):
                depth -= 1

            if c == NALSyntax.StatementSyntax.TermDivider.value and depth == 0:
                subterm = Term.from_string(subterm_string)
                subterms.append(subterm)
                subterm_string = ""
            else:
                subterm_string += c

        subterm = Term.from_string(subterm_string)
        subterms.append(subterm)

        return subterms, connector



class StatementTerm(CompoundTerm,Array):
    """
        <subject><copula><predicate>

        A special kind of compound term with a subject, predicate, and copula.
        Statement connector is `None` for regular statements

        (P --> Q)

        May also represent a single-statement compound, like negation (--,(P-->Q))
        in which case the non-negated statement is stored in subject and predicate is None.
    """

    def __init__(self, subject_term: Term, predicate_term = None, copula=None, statement_connector = None):
        self.is_array = False
        assert_term(subject_term)
        subterms = [subject_term]
        if predicate_term is not None:
            subterms.append(predicate_term)

        self.copula = None
        if copula is not None:
            self.copula = copula
            if NALSyntax.Copula.is_symmetric(copula):
                subterms.sort(key=lambda t: str(t))  # sort alphabetically

        CompoundTerm.__init__(self,subterms, statement_connector)

        is_perceptual_term = isinstance(subject_term, CompoundTerm) \
                             and subject_term.is_extensional_set() \
                             and isinstance(subject_term.subterms[0], Array) \
                             and subject_term.subterms[0].is_array \
                             and isinstance(predicate_term, CompoundTerm) \
                             and predicate_term.is_intensional_set()
        if is_perceptual_term:
            Array.__init__(self, dim_lengths=subject_term.subterms[0].get_dimensions())

    @classmethod
    def from_string(cls, statement_string):
        """
            Parameter: statement_string - String of NAL syntax "(term copula term)"

            Returns: top-level subject term, predicate term, copula, copula index
        """
        statement_connector = None

        if NALSyntax.TermConnector.get_term_connector_from_string(
                statement_string[1:3]) == NALSyntax.TermConnector.Negation:
            # found a negation statement connector
            statement_connector = NALSyntax.TermConnector.Negation
            statement_string = statement_string[4:-1]

        # get copula
        copula, copula_idx = get_top_level_copula(statement_string)
        assert (copula is not None), "Copula not found. Exiting.."

        subject_str = statement_string[1:copula_idx]  # get subject string
        predicate_str = statement_string[
                        copula_idx + len(copula.value):len(statement_string) - 1]  # get predicate string

        return StatementTerm(subject_term=Term.from_string(subject_str), predicate_term=Term.from_string(predicate_str),
                              copula=copula, statement_connector=statement_connector)



    def _calculate_syntactic_complexity(self):
        """
            Recursively calculate the syntactic complexity of
            the compound term. The connector adds 1 complexity,
            and the subterms syntactic complexities are summed as well.
        """
        count = 1  # the copula
        if self.connector is not None:
            count += 1
        for subterm in self.subterms:
            count = count + subterm._calculate_syntactic_complexity()

        return count

    def get_subject_term(self) -> Term:
        return self.subterms[0]

    def get_predicate_term(self) -> Term:
        return self.subterms[1]

    def get_copula(self):
        return self.copula

    def get_statement_connector(self):
        return self.connector

    def get_copula_string(self):
        return str(self.get_copula().value)

    def get_formatted_string(self):
        """
            returns: (Subject copula Predicate)
        """
        if len(self.subterms) > 1:
            string = NALSyntax.StatementSyntax.Start.value + \
               self.get_subject_term().get_formatted_string() + \
               " " + self.get_copula_string() + " " + \
               self.get_predicate_term().get_formatted_string() \
               + NALSyntax.StatementSyntax.End.value
        else:
            string = CompoundTerm.get_formatted_string(self)

        return string

    def is_operation(self):
        return isinstance(self.get_subject_term(), CompoundTerm) \
            and self.get_subject_term().connector == NALSyntax.TermConnector.Product \
            and self.get_subject_term().subterms[0] == Global.Global.TERM_SELF # product and first term is self means this is an operation


class ArrayTerm(CompoundTerm,Array):
    """
        A N-dimensional array term that can be indexed (e.g. T).
        or a array element term (e.g. T[0.0,0.0])

        (N between 1 and 3)

        Note that no values are stored in the array. The term only represents an array of terms.
    """
    def __init__(self, name, dim_lengths):
        """
        :param name: Name of the array term
        :param dim_lengths: the number of elements in each dimensional axis (x,y,z);
            provides a granularity = 2.0/(dim_length - 1)
        """
        self.is_array = False
        self.name = name
        Array.__init__(self,dim_lengths)
        CompoundTerm.__init__(self, subterms=self.array.flatten(), term_connector=NALSyntax.TermConnector.Array)

    def get_formatted_string(self):
        return NALSyntax.TermConnector.Array.value + self.name


class AtomicArrayElementTerm(AtomicTerm):
    """
        A term that is an element of an atomic array term.
        It is simply the atomic array term with attached indices

        e.g. @A[x,y,z]
    """
    def __init__(self, array_term, indices):
        self.array_term = array_term # the array term of which this is an element
        self.indices = indices

    def get_formatted_string(self):
        return self.array_term.get_formatted_string() + str(self.indices)

def get_top_level_copula(string):
    """
        Searches for top-level copula in the string.

        :returns copula and index if it exists,
        :returns none and -1 otherwise
    """
    copula = None
    copula_idx = -1

    depth = 0
    for i, v in enumerate(string):
        if v == NALSyntax.StatementSyntax.Start.value:
            depth += 1
        elif v == NALSyntax.StatementSyntax.End.value:
            depth -= 1
        elif depth == 1 and i + 3 <= len(string) and NALSyntax.Copula.is_string_a_copula(string[i:i + 3]):
            copula, copula_idx = NALSyntax.Copula.get_copula_from_string(string[i:i + 3]), i

    return copula, copula_idx


def assert_term(t):
    assert (isinstance(t, Term)), str(t) + " must be a Term"


def assert_statement_term(t):
    assert (isinstance(t, StatementTerm)), str(t) + " must be a Statement Term"


def assert_sentence(j):
    assert (isinstance(j, Sentence)), str(j) + " must be a Sentence"


def assert_truth_value(j):
    assert (isinstance(j, TruthValue)), str(j) + " must be a TruthValue"


def assert_punctuation(j):
    assert (isinstance(j, NALSyntax.Punctuation)), str(j) + " must be a Punctuation"


def assert_copula(j):
    assert (isinstance(j, NALSyntax.Copula)), str(j) + " must be a Copula"
