import Config
from NALGrammar import *

"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""

"""
    ++++ ++++ ++++ ++++ ++++ ++++  ++++  ++++
    ++++ (Binary truth value operations) ++++
    ++++ ++++ ++++ ++++ ++++ ++++  ++++  ++++
"""


def band(*argv):
    """
        Binary AND

        -----------------

        Input:
            argv - NAL Binary Values

        Returns:
            argv1*argv2*...*argvn
    """
    res = 1
    for arg in argv:
        res = res * arg
    return res


def bor(*argv):
    """
        Binary OR

        -----------------

        Input:
            argv - NAL Binary Values

        Returns:
             1-((1-argv1)*(1-argv2)*...*(1-argvn))
    """
    res = 1
    for arg in argv:
        res = res * (1 - arg)
    return 1 - res


def bnot(arg):
    """
        Binary Not

        -----------------

        Input:
            arg - NAL Binary Value

        Returns:
            1 - arg
    """
    return 1 - arg


"""
    ++++ ++++ ++++ ++++ ++++ ++++ ++++
    ++++  (Local inference rules) ++++
    ++++ ++++ ++++ ++++ ++++ ++++ ++++
"""


def nal_revision(j1: Sentence, j2: Sentence):
    """
        Revision Rule

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Revises two instances of the same sentence with different truth values.

        Input:
          j1: Sentence (Statement <f1, c1>)

          j2: Sentence (Statement <f2, c2>)
        Returns:
          :- Sentence (Statement <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    assert (
                j1.statement.term.get_formatted_string() == j2.statement.term.get_formatted_string() or j1.statement.term.get_formatted_string() == j2.statement.term.get_reverse_term_string()), "Cannot revise sentences for 2 different statements"

    # Get Truth Value
    (wp1, w1, wn1), (wp2, w2, wn2) = getevidence_from2sentences(j1, j2)

    # compute values of combined evidence
    wp3 = wp1 + wp2
    wn3 = wn1 + wn2
    w3 = wp3 + wn3
    f3, c3 = getfreqconf_fromevidence(wp3, w3)

    # Create the resultant sentence
    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(j1.statement.get_subject_term(), j1.statement.get_predicate_term(), j1.statement.copula)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_choice(j1, j2):
    """
         Choice Rule

         -----------------

         Choose the better answer (according to the choice rule) between 2 different sentences.
         If the statements are the same, the statement with the highest confidence is chosen.
         If they are different, the statement with the highest expectation is chosen.

         Input:
           j1: Sentence (Statement <f1, c1>)

           j2: Sentence (Statement <f2, c2>)

         Returns:
           j1 or j2, depending on which is better according to the choice rule
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    subjpred1 = j1.subject_predicate
    subjpred2 = j2.subject_predicate

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # Make the choice
    if subjpred1 == subjpred2:
        if c1 >= c2:
            best = j1
        else:
            best = j2
    else:
        e1 = nal_expectation(f1, c1)
        e2 = nal_expectation(f2, c2)
        if e1 >= e2:
            best = j1
        else:
            best = j2

    return best


def nal_decision(d):
    """
         Decision Rule

         -----------------

         Make the decision to purse a desire based on its expected desirability

         Input:
           d: Desire's desirability

         Returns:
           True or false, whether to pursue the goal
    """
    return abs(d - 0.5) > Config.t


def nal_expectation(f, c):
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


"""
    ++++ ++++ ++++ ++++ ++++ ++++
    ++++ (Immediate inference) ++++
    ++++ ++++ ++++ ++++ ++++ ++++
"""


def nal_negation(j):
    """
         Negation

         -----------------

         Input:
           j: Sentence (Statement <f, c>)

         Returns:
    """
    assert_sentence(j)
    #todo return new Sentence
    j.value.frequency = 1 - j.value.frequency
    return j



def nal_conversion(j):
    """
        Conversion Rule

        Reverses the subject and predicate
        -----------------

        Input:
            j1: Sentence (S --> P <f1, c1>)
        Truth Val:
            w+: and(f1,c1)
            w-: 0
        Returns:
            :- Sentence (P --> S <f2, c2>)
    """
    assert_sentence(j)
    # Statement
    resultStatement = Statement(j.statement.get_predicate_term(),
                                j.statement.get_subject_term(), Copula.Inheritance)

    punctuation = None
    resulttruth = None
    if j.punctuation == Punctuation.Judgment:
        # compute values of combined evidence
        wp = band(j.value.frequency, j.value.confidence)
        w = wp
        f2, c2 = getfreqconf_fromevidence(wp, w)
        resulttruth = TruthValue(f2, c2)
        punctuation = Punctuation.Judgment
    elif j.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentence's evidential base
    result.stamp.evidential_base.merge_evidential_base_into_self(j.stamp.evidential_base)

    return result


# Contrapositive
# Inputs:
#   j1:
#   j2:
# Returns:
def nal_contrapositive(j1, j2):
    # todo
    return 0


"""
    ++++ ++++ ++++ ++++ ++++ ++++
    ++++ (Strong syllogism) ++++
    ++++ ++++ ++++ ++++ ++++ ++++
"""


def nal_deduction(j1: Sentence, j2: Sentence):
    """
        Deduction (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)

            j2: Sentence (S --> M <f2, c2>)
        Truth Val:
            f3: and(f1,f2)

            c3: and(f1,f2,c1,c2)
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.get_subject_term(),
                                j1.statement.get_predicate_term(), Copula.Inheritance)

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        f3 = band(f1, f2)
        c3 = band(f1, f2, c1, c2)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_analogy(j1: Sentence, j2: Sentence):
    """
        Analogy (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)
                or
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (S <-> M <f2, c2>)
                or
            j2: Sentence (M <-> S <f2, c2>)
        Truth Val:
            f: and(f1,f2)

            c: and(f2,c1,c2)
        Returns: (depending on j1)
            :- Sentence (S --> P <f3, c3>)
                or
            :- Sentence (P --> S <f3, c3>)

    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        #j1=M-->P, j2=S<->M
        resultStatement = Statement(j2.statement.get_subject_term(), j1.statement.get_predicate_term(),
                                    Copula.Inheritance) # S-->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M-->P, j2=M<->S
        resultStatement = Statement(j2.statement.get_predicate_term(), j1.statement.get_predicate_term(),
                                    Copula.Inheritance) # S-->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1=P-->M, j2=S<->M
        resultStatement = Statement(j1.statement.get_subject_term(), j2.statement.get_subject_term(),
                                    Copula.Inheritance) # P-->S
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P-->M, j2=M<->S
        resultStatement = Statement(j1.statement.get_subject_term(), j2.statement.get_predicate_term(),
                                    Copula.Inheritance) # P-->S
    else:
        assert(False), "Error: Invalid inputs to nal_analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        f3 = band(f1, f2)
        c3 = band(f2, c1, c2)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_resemblance(j1: Sentence, j2: Sentence):
    """
        Resemblance (Strong syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M <-> P <f1, c1>)
                or
            j1: Sentence (P <-> M <f1, c1>)

            j2: Sentence (S <-> M <f2, c2>)
                or
            j2: Sentence (M <-> S <f2, c2>)
        Truth Val:
            f: and(f1,f2)

            c: and(or(f1,f2),c1,c2)
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M<->P, j2=S<->M
        resultStatement = Statement(j2.statement.get_subject_term(), j1.statement.get_predicate_term(),
                                    Copula.Inheritance)  # S<->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M<->P, j2=M<->S
        resultStatement = Statement(j2.statement.get_predicate_term(), j1.statement.get_predicate_term(),
                                    Copula.Inheritance)  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P<->M, j2=S<->M
        resultStatement = Statement(j2.statement.get_subject_term(), j1.statement.get_subject_term(),
                                    Copula.Inheritance)  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P<->M, j2=M<->S
        resultStatement = Statement(j2.statement.get_predicate_term(), j2.statement.get_subject_term(),
                                    Copula.Inheritance)  # S<->P
    else:
        assert (
            False), "Error: Invalid inputs to nal_resemblance: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        f3 = band(f1, f2)
        c3 = band(bor(f1, f2), c1, c2)

        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


"""
    ++++ ++++ ++++ ++++ ++++ ++++
    ++++ (Weak syllogism) ++++
    ++++ ++++ ++++ ++++ ++++ ++++
"""


def nal_abduction(j1: Sentence, j2: Sentence):
    """
        Abduction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (S --> M <f2, c2>)
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f1,c1,not(f2),c2)

            w: and(f1,c1,c2)
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    resultStatement = Statement(j2.statement.get_subject_term(), j1.statement.get_subject_term(), Copula.Inheritance)

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(f1, c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_induction(j1: Sentence, j2: Sentence):
    """
        Induction (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.get_predicate_term(),
                                j1.statement.get_predicate_term(), Copula.Inheritance)

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(f2, c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_exemplification(j1: Sentence, j2: Sentence):
    """
        Exemplification (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (P --> M <f1, c1>)

            j2: Sentence (M --> S <f2, c2>)
        Evidence:
            w+: and(f1,c1,f2,c2)

            w-: 0

            w: w+
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.get_predicate_term(),
                                j1.statement.get_subject_term(), Copula.Inheritance)

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = wp
        f3, c3 = getfreqconf_fromevidence(wp, w)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


def nal_comparison(j1: Sentence, j2: Sentence):
    """
        Comparison (Weak syllogism)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (M --> P <f1, c1>)
            j2: Sentence (M --> S <f2, c2>)

            or

            j1: Sentence (P --> M <f1, c1>)
            j2: Sentence (S --> M <f2, c2>)
        Evidence:
            w+: and(f1,c1,f2,c2)

            w: and(or(f1,f2),c1,c2)
        Returns:
            :- Sentence (S <-> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_subject_term():
        resultStatement = Statement(j2.statement.get_predicate_term(), j1.statement.get_predicate_term(), Copula.Similarity)
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        resultStatement = Statement(j2.statement.get_subject_term(), j1.statement.get_subject_term(), Copula.Similarity)
    else:
        assert(False), "Error: Invalid inputs to nal_comparison: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    punctuation = None
    resulttruth = None
    if j1.punctuation == Punctuation.Judgment and j2.punctuation == Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(bor(f1, f2), c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        resulttruth = TruthValue(f3, c3)
        punctuation = Punctuation.Judgment
    elif j1.punctuation == Punctuation.Question or j2.punctuation == Punctuation.Question:
        punctuation = Punctuation.Question

    result = Sentence(resultStatement, resulttruth, punctuation)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_evidential_base_into_self(j1.stamp.evidential_base)
    result.stamp.evidential_base.merge_evidential_base_into_self(j2.stamp.evidential_base)

    return result


"""
    ++++ ++++ ++++ ++++ ++++ ++++
    ++++ (Helper function) ++++
    ++++ ++++ ++++ ++++ ++++ ++++
"""


def getfreqconf_fromevidence(wp, w):
    """
        Input:
            wp: positive evidence w+

            w: total evidence w
        Returns:
            frequency, confidence
    """
    f = wp / w
    c = w / (w + Config.k)
    return f, c


def getevidence_fromfreqconf(f, c):
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


def gettruthvalues_from2sentences(j1: Sentence, j2: Sentence):
    """
        Input:
            j1: Statement <f1, c1>

            j2: Statement <f2, c2>
        Returns:
            f1, c1, f2, c2
    """
    return gettruthvalues_fromsentence(j1), gettruthvalues_fromsentence(j2)


def gettruthvalues_fromsentence(j: Sentence):
    """
        Input:
            j: Statement <f, c>
        Returns:
            f, c
    """
    return j.value.frequency, j.value.confidence


def getevidence_from2sentences(j1: Sentence, j2: Sentence):
    """
        Input:
            j1: Statement <f1, c1>

            j2: Statement <f2, c2>
        Returns:
            w1+, w1, w1-, w2+, w2, w2-
    """
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)
    return getevidence_fromfreqconf(f1, c1), getevidence_fromfreqconf(f2, c2)
