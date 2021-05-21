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
import Global
import NALGrammar
from NALInferenceRules import HelperFunctions, ExtendedBooleanOperators
from NALInferenceRules.HelperFunctions import get_truthvalue_from_evidence


def F_Revision(wp1, wn1, wp2, wn2):
    """
        :return: F_rev: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = wp1 + wp2
    wn = wn1 + wn2
    w = wp + wn
    f_rev, c_rev = HelperFunctions.get_truthvalue_from_evidence(wp, w)
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
        wp = AND(f, c)
        wn = AND(NOT(f), c)
        :return: F_cnv: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f, c)
    w = wp
    f_cnv, c_cnv = get_truthvalue_from_evidence(wp, w)
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
    f_cnt, c_cnt = get_truthvalue_from_evidence(wp, w)

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
    f_abd, c_abd = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_abd, c_abd)


def F_Induction(f1, c1, f2, c2):
    """
    :return: F_ind: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(f2, c1, c2)
    f_ind, c_ind = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_ind, c_ind)


def F_Exemplification(f1, c1, f2, c2):
    """
    :return: F_exe: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = wp
    f_exe, c_exe = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_exe, c_exe)


def F_Comparison(f1, c1, f2, c2):
    """
        :return: F_com: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = ExtendedBooleanOperators.band(f1, f2, c1, c2)
    w = ExtendedBooleanOperators.band(ExtendedBooleanOperators.bor(f1, f2), c1, c2)
    f3, c3 = get_truthvalue_from_evidence(wp, w)
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
