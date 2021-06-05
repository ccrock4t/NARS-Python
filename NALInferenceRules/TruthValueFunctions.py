"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Truth Value Functions ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""
import Config
import Global
import NALGrammar
import NALInferenceRules
from NALInferenceRules import ExtendedBooleanOperators


def F_Revision(wp1, wn1, wp2, wn2):
    """
        :return: F_rev: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = wp1 + wp2
    wn = wn1 + wn2
    w = wp + wn
    f_rev, c_rev = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_rev, c_rev)


def F_Negation(f, c):
    """
        f_neg = 1 - f
        c_neg = c
        :return: F_neg: Truth-Value (f,c)
    """
    return NALGrammar.TruthValue(1 - f, c)


def F_Conversion(f, c):
    """
        f_cnv = 1
        c_cnv = (f*c)/(f*c+k)
        :return: F_cnv: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_cnv = 1.0
    c_cnv = (f*c)/(f*c+Config.k)
    return NALGrammar.TruthValue(f_cnv, c_cnv)


def F_Contraposition(f, c):
    """
        wp = 0
        wn = AND(NOT(f), c)
        :return: F_cnt: Truth-Value (f,c)
    """
    wp = 0
    wn = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bnot(f), c)
    w = wn
    f_cnt, c_cnt = NALInferenceRules.Helperfunctions.get_truthvalue_from_evidence(wp, w)

    return NALGrammar.TruthValue(f_cnt, c_cnt)


def F_Deduction(f1, c1, f2, c2):
    """
        f_ded: and(f1,f2)
        c_ded: and(f1,f2,c1,c2)

        :return: F_ded: Truth-Value (f,c)
    """
    f3 = ExtendedBooleanOperators.band(f1, f2)
    c3 = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    return NALGrammar.TruthValue(f3, c3)


def F_Analogy(f1, c1, f2, c2):
    """
        f_ana: AND(f1,f2)
        c_ana: AND(f2,c1,c2)

        :return: F_ana: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_ana = ExtendedBooleanOperators.band(f1, f2)
    c_ana = ExtendedBooleanOperators.band(f2, c1, c2)
    return NALGrammar.TruthValue(f_ana, c_ana)


def F_Resemblance(f1, c1, f2, c2):
    """
        f_res = AND(f1,f2)
        c_res = AND(OR(f1,f2),c1,c2)

        :return: F_res: Truth-Value (f,c)
    """
    f_res = ExtendedBooleanOperators.band(f1, f2)
    c_res = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bor(f1, f2), c1, c2)

    return NALGrammar.TruthValue(f_res, c_res)


def F_Abduction(f1, c1, f2, c2):
    """
        wp = AND(f1,f2,c1,c2)
        w = AND(f1,c1,c2)

        :return: F_abd: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(f1, c1, c2)
    f_abd, c_abd = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_abd, c_abd)


def F_Induction(f1, c1, f2, c2):
    """
    :return: F_ind: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(f2, c1, c2)
    f_ind, c_ind = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_ind, c_ind)


def F_Exemplification(f1, c1, f2, c2):
    """
    :return: F_exe: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = wp
    f_exe, c_exe = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_exe, c_exe)


def F_Comparison(f1, c1, f2, c2):
    """
        :return: F_com: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bor(f1, f2), c1, c2)
    f3, c3 = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f3, c3)


def F_Intersection(f1, c1, f2, c2):
    """
    :return: F_int: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_int = ExtendedBooleanOperators.band(f1, f2)
    c_int = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.TruthValue(f_int, c_int)


def F_Union(f1, c1, f2, c2):
    """
    :return: F_uni: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f3 = ExtendedBooleanOperators.bor(f1, f2)
    c3 = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.TruthValue(f3, c3)


def F_Difference(f1, c1, f2, c2):
    """
    :return: F_dif: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f3 = ExtendedBooleanOperators.band(f1, ExtendedBooleanOperators.bnot(f2))
    c3 = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.TruthValue(f3, c3)


def F_Projection(frequency, confidence, t_B, t_T):
    """
        Time Projection

        Project the occurrence time of a belief (t_B)
        to another occurrence time (t_T)
    """
    T_c = Global.Global.get_current_cycle_number()
    k_c = abs(t_B - t_T) / (abs(t_B - T_c) + abs(t_T - T_c))
    projected_confidence = (1 - k_c) * confidence
    return NALGrammar.TruthValue(frequency,projected_confidence)


def F_Eternalization(temporal_frequency, temporal_confidence):
    eternal_confidence = 1.0 / (Config.k + temporal_confidence)
    return NALGrammar.TruthValue(temporal_frequency, eternal_confidence)

def Expectation(f, c):
    """
        Expectation

        -----------------

         Input:
            f: frequency

            c: confidence

         Returns:
            expectation value
    """
    return c * (f - 0.5) + 0.5

def TruthFunctionOnArray(truth_value_array_1, truth_value_array_2, truth_value_function):
    """
        Performs a truth value function element-wise on the array
    :param truth_value_array_1:
    :param truth_value_array_2:
    :param truth_value_function:
    :return:
    """
    if truth_value_array_1 is None and truth_value_array_2 is None: return None
    truth_values = []
    for z, layer in enumerate(truth_value_array_1):
        truth_values_layer = []
        for y, row in enumerate(layer):
            truth_values_row = []
            for x, value in enumerate(row):
                if truth_value_array_2 is None:
                    # single truth value
                    truth_values_row.append(truth_value_function(value.frequency, value.confidence))
                else:
                    truth_values_row.append(truth_value_function(value.frequency, value.confidence,truth_value_array_2[z][y][x].frequency, truth_value_array_2[z][y][x].confidence))
            truth_values_layer.append(truth_values_row)
        truth_values.append(truth_values_layer)
    return truth_values


def ReviseArray(array_to_iterate):
    """
         Performs a truth value function element-wise on the array
         and revises it into a single truth-value
    """
    final_truth_value = None

    for z, layer in enumerate(array_to_iterate):
        for y, row in enumerate(layer):
            for x, value in enumerate(row):
                if final_truth_value is None:
                    final_truth_value = value
                else:
                    wp1, w1, wn1 = NALInferenceRules.HelperFunctions.get_evidence_fromfreqconf(final_truth_value.frequency, final_truth_value.confidence)
                    wp2, w2, wn2 = NALInferenceRules.HelperFunctions.get_evidence_fromfreqconf(value.frequency, value.confidence)
                    final_truth_value = F_Revision(wp1,wn1,wp2,wn2)
    return final_truth_value