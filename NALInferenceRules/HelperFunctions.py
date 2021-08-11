import Config
import NALGrammar
import NALSyntax
from NALInferenceRules.TruthValueFunctions import TruthFunctionOnArrayAndRevise, TruthFunctionOnArray


def get_truthvalue_from_evidence(wp, w):
    """
        Input:
            wp: positive evidence w+

            w: total evidence w
        Returns:
            frequency, confidence
    """
    if wp == w:
        f = 1.0
    else:
        f = wp / w
    c = get_confidence_from_evidence(w)
    return f, c


def get_evidence_fromfreqconf(f, c):
    """
        Input:
            f: frequency

            c: confidence
        Returns:
            w+, w, w-
    """
    wp = Config.k * f * c / (1 - c)
    w = Config.k * c / (1 - c)
    return wp, w, w - wp


def get_confidence_from_evidence(w):
    """
        Input:
            w: Total evidence
        Returns:
            confidence
    """
    return w / (w + Config.k)


def getevidentialvalues_from2sentences(j1, j2):
    """
        Input:
            j1: Sentence <f1, c1>

            j2: Sentence <f2, c2>
        Returns:
            f1, c1, f2, c2
    """
    return getevidentialvalues_fromsentence(j1), getevidentialvalues_fromsentence(j2)


def getevidentialvalues_fromsentence(j):
    """
        Input:
            j: Sentence <f, c>
        Returns:
            f, c
    """
    return j.value.frequency, j.value.confidence


def getevidence_from2sentences(j1, j2):
    """
        Input:
            j1: Sentence <f1, c1>

            j2: Sentence <f2, c2>
        Returns:
            w1+, w1, w1-, w2+, w2, w2-
    """
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    return get_evidence_fromfreqconf(f1, c1), get_evidence_fromfreqconf(f2, c2)

def create_resultant_sentence_two_premise(j1, j2, result_statement, truth_value_function):
    """
        Creates the resultant sentence between 2 premises, the resultant statement, and the truth function
    :param j1:
    :param j2:
    :param result_statement:
    :param truth_value_function:
    :return:
    """
    result_statement = NALGrammar.Terms.simplify_term(result_statement)
    result_type = premise_result_type(j1,j2)

    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal :
        # Judgment or Goal
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth_array = None
        if j1.is_array and j2.is_array:
            result_truth, result_truth_array = TruthFunctionOnArrayAndRevise(j1.truth_values,
                                                                        j2.truth_values,
                                                                        truth_value_function=truth_value_function)
        else:
            result_truth = truth_value_function(f1, c1, f2, c2)

        if result_type == NALGrammar.Sentences.Judgment:
            occurrence_time = None
            if (isinstance(result_statement, NALGrammar.Terms.StatementTerm)
                and NALSyntax.Copula.is_first_order(result_statement.get_copula())) \
                    or (not isinstance(result_statement, NALGrammar.Terms.StatementTerm)
                        and isinstance(result_statement, NALGrammar.Terms.CompoundTerm)
                        and not NALSyntax.TermConnector.is_first_order(result_statement.connector)):
                # if the result is a first-order statement,
                # or a compound statement, it may have an occurrence time
                occurrence_time = j1.stamp.occurrence_time

            result = NALGrammar.Sentences.Judgment(result_statement, (result_truth, result_truth_array),
                                                   occurrence_time=occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            result = NALGrammar.Sentences.Goal(result_statement, (result_truth, result_truth_array))
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)
    stamp_and_print_inference_rule(result, truth_value_function, [j1.get_formatted_string(),j2.get_formatted_string()])

    return result

def create_resultant_sentence_one_premise(j, result_statement, truth_value_function):
    """
        Creates the resultant sentence for 1 premise, the resultant statement, and the truth function
        if truth function is None, uses j's truth-value
    :param j:
    :param result_statement:
    :param truth_value_function:
    :return:
    """
    result_type = type(j)
    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal:
        # Get Truth Value
        result_truth_array = None
        if truth_value_function is None:
            result_truth = NALGrammar.Values.TruthValue(j.value.frequency,j.value.confidence)
        else:
            if j.is_array:
                result_truth_array = TruthFunctionOnArray(j.truth_values, None, truth_value_function)
            result_truth = truth_value_function(j.value.frequency, j.value.confidence)

        if result_type == NALGrammar.Sentences.Judgment:
            result = NALGrammar.Sentences.Judgment(result_statement, (result_truth, result_truth_array),
                                                   occurrence_time=j.stamp.occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            result = NALGrammar.Sentences.Goal(result_statement, (result_truth, result_truth_array))
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)
    result.stamp.from_one_premise_inference = True
    stamp_and_print_inference_rule(result, truth_value_function, [j.get_formatted_string()])

    return result

def stamp_and_print_inference_rule(sentence, inference_rule, parent_premises):
    sentence.stamp.derived_by = "Structural Transformation" if inference_rule is None else inference_rule.__name__
    sentence.stamp.parent_premises = parent_premises
    if Config.DEBUG: print(sentence.stamp.derived_by + " derived " + sentence.get_formatted_string())

def premise_result_type(j1,j2):
    """
        Given 2 sentence premises, determines the type of the resultant sentence
    """
    if not isinstance(j1, NALGrammar.Sentences.Judgment):
        return type(j1)
    elif not isinstance(j2, NALGrammar.Sentences.Judgment):
        return type(j2)
    else:
        return NALGrammar.Sentences.Judgment