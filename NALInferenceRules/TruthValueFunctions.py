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
import numpy as np

def F_Revision(f1,c1,f2,c2):
    """
        :return: F_rev: Truth-Value (f,c)
    """
    wp1, w1, _ = NALInferenceRules.HelperFunctions.get_evidence_fromfreqconf(f1,c1)
    wp2, w2, _ = NALInferenceRules.HelperFunctions.get_evidence_fromfreqconf(f2,c2)
    # compute values of combined evidence
    wp = wp1 + wp2
    w = w1 + w2
    f_rev, c_rev = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.Values.TruthValue(f_rev, c_rev)


def F_Negation(f, c):
    """
        f_neg = 1 - f
        c_neg = c
        :return: F_neg: Truth-Value (f,c)
    """
    return NALGrammar.Values.TruthValue(1 - f, c)


def F_Conversion(f, c):
    """
        f_cnv = 1
        c_cnv = (f*c)/(f*c+k)
        :return: F_cnv: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_cnv = 1.0
    c_cnv = (f*c)/(f*c+Config.k)
    return NALGrammar.Values.TruthValue(f_cnv, c_cnv)


def F_Contraposition(f, c):
    """
        wp = 0
        wn = AND(NOT(f), c)
        :return: F_cnt: Truth-Value (f,c)
    """
    #todo
    return NALGrammar.Values.TruthValue(f, ExtendedBooleanOperators.band(f, c))


def F_Deduction(f1, c1, f2, c2):
    """
        f_ded: and(f1,f2)
        c_ded: and(f1,f2,c1,c2)

        :return: F_ded: Truth-Value (f,c)
    """
    f3 = ExtendedBooleanOperators.band(f1, f2)
    c3 = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    return NALGrammar.Values.TruthValue(f3, c3)




def F_Analogy(f1, c1, f2, c2):
    """
        f_ana: AND(f1,f2)
        c_ana: AND(f2,c1,c2)

        :return: F_ana: Truth-Value (f,c)
    """
    f_ana = ExtendedBooleanOperators.band(f1, f2)
    c_ana = ExtendedBooleanOperators.band(f2, c1, c2)
    return NALGrammar.Values.TruthValue(f_ana, c_ana)


def F_Resemblance(f1, c1, f2, c2):
    """
        f_res = AND(f1,f2)
        c_res = AND(OR(f1,f2),c1,c2)

        :return: F_res: Truth-Value (f,c)
    """
    f_res = ExtendedBooleanOperators.band(f1, f2)
    c_res = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bor(f1, f2), c1, c2)

    return NALGrammar.Values.TruthValue(f_res, c_res)


def F_Abduction(f1, c1, f2, c2):
    """
        wp = AND(f1,f2,c1,c2)
        w = AND(f1,c1,c2)

        :return: F_abd: Truth-Value (f,c)
    """
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(f1, c1, c2)
    f_abd, c_abd = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.Values.TruthValue(f_abd, c_abd)


def F_Induction(f1, c1, f2, c2):
    """
    :return: F_ind: Truth-Value (f,c)
    """
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(f2, c1, c2)
    f_ind, c_ind = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.Values.TruthValue(f_ind, c_ind)


def F_Exemplification(f1, c1, f2, c2):
    """
    :return: F_exe: Truth-Value (f,c)
    """
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = wp
    f_exe, c_exe = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.Values.TruthValue(f_exe, c_exe)


def F_Comparison(f1, c1, f2, c2):
    """
        :return: F_com: Truth-Value (f,c)
    """
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bor(f1, f2), c1, c2)
    f3, c3 = NALInferenceRules.HelperFunctions.get_truthvalue_from_evidence(wp, w)
    return NALGrammar.Values.TruthValue(f3, c3)

def F_Array_Element_Comparison(f1, c1, f2, c2):
    """
        :return: F_array_com: Truth-Value (f,c)
    """
    f3 = ExtendedBooleanOperators.bnot(abs(f1-f2))
    c3 = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.Values.TruthValue(f3, c3)

def F_Intersection(f1, c1, f2, c2):
    """
    :return: F_int: Truth-Value (f,c)
    """
    f_int = ExtendedBooleanOperators.band(f1, f2)
    c_int = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.Values.TruthValue(f_int, c_int)


def F_Union(f1, c1, f2, c2):
    """
    :return: F_uni: Truth-Value (f,c)
    """
    f3 = ExtendedBooleanOperators.bor(f1, f2)
    c3 = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.Values.TruthValue(f3, c3)


def F_Difference(f1, c1, f2, c2):
    """
    :return: F_dif: Truth-Value (f,c)
    """
    f3 = ExtendedBooleanOperators.band(f1, ExtendedBooleanOperators.bnot(f2))
    c3 = ExtendedBooleanOperators.band(c1, c2)
    return NALGrammar.Values.TruthValue(f3, c3)


def F_Projection(frequency, confidence, t_B, t_T, decay):
    """
        Time Projection

        Project the occurrence time of a belief (t_B)
        to another occurrence time (t_T).

        Same frequency, but lower confidence depending on when it occurred.
    """
    if t_B == t_T: return NALGrammar.Values.TruthValue(frequency, confidence)
    interval = abs(t_B - t_T)
    projected_confidence = confidence * (decay ** interval)
    return NALGrammar.Values.TruthValue(frequency, projected_confidence)


def F_Eternalization(temporal_frequency, temporal_confidence):
    eternal_confidence = temporal_confidence/ (Config.k + temporal_confidence)
    return NALGrammar.Values.TruthValue(temporal_frequency, eternal_confidence)

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
    if truth_value_array_1 is not None and truth_value_array_2 is not None: assert truth_value_array_1.shape == truth_value_array_2.shape,"ERROR: Truth value arrays must be the same shape"

    def function(*indices):
        coords = tuple([int(var) for var in indices])
        truth_value_1 = truth_value_array_1[coords]
        if truth_value_array_2 is None:
            # single truth value
            truth_value = truth_value_function(truth_value_1.frequency,
                                                        truth_value_1.confidence)
        else:
            truth_value_2 = truth_value_array_2[coords]
            truth_value = truth_value_function(truth_value_1.frequency,
                                                        truth_value_1.confidence,
                                                        truth_value_2.frequency,
                                                        truth_value_2.confidence)
        return truth_value

    func_vectorized = np.vectorize(function)
    return np.fromfunction(function=func_vectorized,shape=truth_value_array_1.shape)



def ReviseArray(truth_value_array):
    """
         Revises a truth value array into a single truth-value
    """
    final_truth_value = None
    for (coords), element in np.ndenumerate(truth_value_array):
        if final_truth_value is None:
            final_truth_value = element
        else:
            final_truth_value = F_Revision(final_truth_value.frequency,final_truth_value.confidence,element.frequency,element.confidence)
    return final_truth_value

def TruthFunctionOnArrayAndRevise(truth_value_array_1, truth_value_array_2, truth_value_function):
    """
         Performs a truth value function element-wise on 1 or 2 arrays
         and simultaneously revises it into a single truth-value.

         Returns the single truth-value
    """
    final_truth_value = None
    final_truth_value_array = np.empty(shape=truth_value_array_1.shape,dtype=NALGrammar.Values.TruthValue)
    for (coords), element in np.ndenumerate(truth_value_array_1):
        truth_value_1 = truth_value_array_1[coords]
        if truth_value_array_2 is None:
            # single truth value
            truth_value = truth_value_function(truth_value_1.frequency,
                                                        truth_value_1.confidence)
        else:
            truth_value_2 = truth_value_array_2[coords]
            truth_value = truth_value_function(truth_value_1.frequency,
                                                        truth_value_1.confidence,
                                                        truth_value_2.frequency,
                                                        truth_value_2.confidence)
        final_truth_value_array[coords] = truth_value
        if final_truth_value is None:
            final_truth_value = truth_value
        else:
            final_truth_value = F_Revision(final_truth_value.frequency,
                                           final_truth_value.confidence,
                                           truth_value.frequency,
                                           truth_value.confidence)

    return final_truth_value,final_truth_value_array