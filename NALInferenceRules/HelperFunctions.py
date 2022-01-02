import math

import Config
import Global
import NALGrammar
import NALSyntax
from NALInferenceRules.TruthValueFunctions import TruthFunctionOnArrayAndRevise, TruthFunctionOnArray, F_Deduction, \
    F_Revision, F_Abduction

import NALInferenceRules.Local


def get_truthvalue_from_evidence(wp, w):
    """
        Input:
            wp: positive evidence w+

            w: total evidence w
        Returns:
            frequency, confidence
    """
    if wp == 0 and w == 0:
        # special case, 0/0
        f = 0
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




def create_resultant_sentence_two_premise(j1, j2, result_statement, truth_value_function):
    """
        Creates the resultant sentence between 2 premises, the resultant statement, and the truth function
    :param j1:
    :param j2:
    :param result_statement:
    :param truth_value_function:
    :return:
    """
    result_statement = NALGrammar.Terms.simplify(result_statement)

    result_type = premise_result_type(j1,j2)

    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal:
        # Judgment or Goal
        # Get Truth Value
        (f1, c1) = (j1.get_present_value().frequency, j1.get_present_value().confidence)
        (f2, c2) = (j2.get_present_value().frequency, j2.get_present_value().confidence)

        result_truth = truth_value_function(f1, c1, f2, c2)
        occurrence_time = None

        # if the result is a first-order statement,  or a higher-order compound statement, it may need an occurrence time
        higher_order_statement = isinstance(result_statement,
                                            NALGrammar.Terms.StatementTerm) and not result_statement.is_first_order()
        if (j1.is_event() or j2.is_event()) and not higher_order_statement:
            occurrence_time = Global.Global.get_current_cycle_number()

        if result_type == NALGrammar.Sentences.Judgment:
            result = NALGrammar.Sentences.Judgment(result_statement, result_truth,
                                                   occurrence_time=occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            result = NALGrammar.Sentences.Goal(result_statement, result_truth, occurrence_time=occurrence_time)
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)


    if not result.is_event():
        # merge in the parent sentences' evidential bases
        result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
        result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)
    else:
        # event evidential bases expire too quickly to track
        pass


    stamp_and_print_inference_rule(result, truth_value_function, [j1,j2])

    return result

def create_resultant_sentence_one_premise(j, result_statement, truth_value_function, result_truth=None):
    """
        Creates the resultant sentence for 1 premise, the resultant statement, and the truth function
        if truth function is None, uses j's truth-value
    :param j:
    :param result_statement:
    :param truth_value_function:
    :param result_truth: Optional truth result
    :return:
    """
    result_statement = NALGrammar.Terms.simplify(result_statement)
    result_type = type(j)
    if result_type == NALGrammar.Sentences.Judgment or result_type == NALGrammar.Sentences.Goal:
        # Get Truth Value
        result_truth_array = None
        if result_truth is None:
            if truth_value_function is None:
                result_truth = j.value #NALGrammar.Values.TruthValue(j.value.frequency,j.value.confidence)
            else:
                result_truth = truth_value_function(j.value.frequency, j.value.confidence)


        if result_type == NALGrammar.Sentences.Judgment:
            result = NALGrammar.Sentences.Judgment(result_statement, result_truth,
                                                   occurrence_time=j.stamp.occurrence_time)
        elif result_type == NALGrammar.Sentences.Goal:
            result = NALGrammar.Sentences.Goal(result_statement, result_truth,
                                               occurrence_time=j.stamp.occurrence_time)
    elif result_type == NALGrammar.Sentences.Question:
        result = NALGrammar.Sentences.Question(result_statement)


    if truth_value_function is None:
        stamp_and_print_inference_rule(result, truth_value_function, j.stamp.parent_premises)
    else:
        stamp_and_print_inference_rule(result, truth_value_function, [j])

    return result

def stamp_and_print_inference_rule(sentence, inference_rule, parent_sentences):
    sentence.stamp.derived_by = "Structural Transformation" if inference_rule is None else inference_rule.__name__

    sentence.stamp.parent_premises = []

    if isinstance(sentence.statement, NALGrammar.Terms.StatementTerm) \
            and not sentence.statement.is_first_order():
        x=1
        #todo remove

    parent_strings = []
    for parent in parent_sentences:
        sentence.stamp.parent_premises.append(parent)
        parent_strings.append(str(parent))


    # if inference_rule is F_Deduction or inference_rule is F_Abduction:
    #     Global.Global.debug_print(sentence.stamp.derived_by
    #                           + " derived " + sentence.__class__.__name__ + sentence.get_formatted_string()
    #                           + " by parents " + str(parent_strings))

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

def convert_to_interval(working_cycles):
    """
        return interval from working cycles
    """
    #round(Config.INTERVAL_SCALE*math.sqrt(working_cycles))
    return working_cycles#round(math.log(Config.INTERVAL_SCALE * working_cycles)) + 1 #round(math.log(working_cycles)) + 1 ##round(5*math.log(0.05*(working_cycles + 9))+4)

def convert_from_interval(interval):
    """
        return working cycles from interval
    """
    #round((interval/Config.INTERVAL_SCALE) ** 2)
    return interval#round(math.exp(interval) / Config.INTERVAL_SCALE) #round(math.exp(interval))  # round(math.exp((interval-4)/5)/0.05 - 9)

def interval_weighted_average(interval1, interval2, weight1, weight2):
    return round((interval1*weight1 + interval2*weight2)/(weight1 + weight2))

def get_unit_evidence():
    return 1 / (1 + Config.k)