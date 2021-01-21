import Config
from NALGrammar import *
"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
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

    Output:
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

    Output:
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

    Output:
        1 - arg
    """
    return 1 - arg


"""
    ++++ ++++ ++++ ++++ ++++ ++++ ++++
    ++++  (Local inference rules) ++++
    ++++ ++++ ++++ ++++ ++++ ++++ ++++
"""

def nal_revision(j1, j2):
    """
    Revision Rule

    -----------------

    Revises two instances of the same sentence with different truth values.

    j1 and j2 must have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø

    Input:
      j1: Sentence (Statement <f1, c1>)

      j2: Sentence (Statement <f2, c2>)
    Output:
      :- Sentence (Statement <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = j1.subject_predicate

    # Get Truth Value
    (wp1, w1, wn1), (wp2, w2, wn2) = getevidence_from2sentences(j1, j2)

    # compute values of combined evidence
    wp3 = wp1 + wp2
    wn3 = wn1 + wn2
    w3 = wp3 + wn3
    f3, c3 = getfreqconf_fromevidence(wp3, w3)
    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
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

     Output:
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

     Output:
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

     Output:
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
    """
    assert_sentence(j)
    # Truth Value
    f1, c1 = gettruthvalues_fromsentence(j)
    _, w, w1n = getevidence_fromfreqconf(f1, c1)

    # negate evidence
    wp = w1n

    # get negated frequency and confidence
    f, c = getfreqconf_fromevidence(wp, w)

    resulttruth = TruthValue(f, c)

    resultStatement = Statement(j.s, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)

    return result


# Conversion
# Inputs:
#   j1:
#   j2:
# Returns:
def nal_conversion(j1, j2):
    # todo
    return 0


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

def nal_deduction(j1, j2):
    """
    Deduction (Strong syllogism)

    -----------------

    Input:
        j1: Sentence (M --> P <f1, c1>)

        j2: Sentence (S --> M <f2, c2>)
    Truth Val:
        f3: and(f1,f2)

        c3: and(f1,f2,c1,c2)
    Output:
        :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.subject_term,
                                j1.statement.predicate_term, Copula.Inheritance)
    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    f3 = band(f1, f2)
    c3 = band(f1, f2, c1, c2)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result

def nal_analogy(j1, j2):
    """
    Analogy (Strong syllogism)

    -----------------

    Input:
        j1: Sentence (M --> P <f1, c1>)

        j2: Sentence (S <-> M <f2, c2>)
    Truth Val:
        f: and(f1,f2)

        c: and(f2,c1,c2)
    Output:
        :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    resultStatement = Statement(j2.statement.subject_term, j1.statement.predicate_term, Copula.Inheritance)

    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    f3 = band(f1, f2)
    c3 = band(f2, c1, c2)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


def nal_resemblance(j1, j2):
    """
    Resemblance (Strong syllogism)

    -----------------

    Input:
        j1: Sentence (M <-> P <f1, c1>)

        j2: Sentence (S <-> M <f2, c2>)
    Truth Val:
        f: and(f1,f2)

        c: and(or(f1,f2),c1,c2)
    Output:
        :- Sentence (S <-> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.subject_term, j1.statement.predicate_term, Copula.Similarity)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    f3 = band(f1, f2)
    c3 = band(bor(f1, f2), c1, c2)

    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result



"""
    ++++ ++++ ++++ ++++ ++++ ++++
    ++++ (Weak syllogism) ++++
    ++++ ++++ ++++ ++++ ++++ ++++
"""

def nal_abduction(j1, j2):
    """
    Abduction (Weak syllogism)

    -----------------

    Input:
        j1: Sentence (P --> M <f1, c1>)

        j2: Sentence (S --> M <f2, c2>)
    Evidence:
        w+: and(f1,f2,c1,c2)

        w-: and(f1,c1,not(f2),c2)

        w: and(f1,c1,c2)
    Output:
        :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    resultStatement = Statement(j2.statement.subject_term, j1.statement.subject_term, Copula.Inheritance)

    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(f1, c1, c2)
    f3, c3 = getfreqconf_fromevidence(wp, w)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result



def nal_induction(j1, j2):
    """
    Induction (Weak syllogism)

    -----------------

    Input:
        j1: Sentence (M --> P <f1, c1>)

        j2: Sentence (M --> S <f2, c2>)
    Evidence:
        w+: and(f1,f2,c1,c2)

        w-: and(f2,c2,not(f1),c1)

        w: and(f2,c1,c2)
    Output:
        :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.predicate_term,
                                j1.statement.predicate_term, Copula.Inheritance)

    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(f2, c1, c2)
    f3, c3 = getfreqconf_fromevidence(wp, w)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result

def nal_exemplification(j1, j2):
    """
    Exemplification (Weak syllogism)

    -----------------

    Input:
        j1: Sentence (P --> M <f1, c1>)

        j2: Sentence (M --> S <f2, c2>)
    Evidence:
        w+: and(f1,c1,f2,c2)

        w-: 0

        w: w+
    Output:
        :- Sentence (S --> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)
    # Statement
    resultStatement = Statement(j2.statement.predicate_term,
                                j1.statement.subject_term, Copula.Inheritance)

    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = wp
    f3, c3 = getfreqconf_fromevidence(wp, w)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result

def nal_comparison(j1, j2):
    """
    Comparison (Weak syllogism)

    -----------------

    Input:
        j1: Sentence (M --> P <f1, c1>)

        j2: Sentence (M --> S <f2, c2>)
    Evidence:
        w+: and(f1,c1,f2,c2)

        w: and(or(f1,f2),c1,c2)
    Output:
        :- Sentence (S <-> P <f3, c3>)
    """
    assert_sentence(j1)
    assert_sentence(j2)

    # Statement
    resultStatement = Statement(j2.statement.predicate_term, j1.statement.predicate_term, Copula.Similarity)

    # Get Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(bor(f1, f2), c1, c2)
    f3, c3 = getfreqconf_fromevidence(wp, w)
    resulttruth = TruthValue(f3, c3)

    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
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
    Output:
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
    Output:
        w+, w, w-
    """
    wp = Config.k * f * c / (1 - c)
    w = Config.k * c / (1 - c)
    return wp, w, w - wp

def gettruthvalues_from2sentences(j1, j2):
    """
    Input:
        j1: Statement <f1, c1>

        j2: Statement <f2, c2>
    Output:
        f1, c1, f2, c2
    """
    return gettruthvalues_fromsentence(j1), gettruthvalues_fromsentence(j2)

def gettruthvalues_fromsentence(j):
    """
    Input:
        j: Statement <f, c>
    Output:
        f, c
    """
    return j.value.frequency, j.value.confidence

def getevidence_from2sentences(j1, j2):
    """
    Input:
        j1: Statement <f1, c1>

        j2: Statement <f2, c2>
    Output:
        w1+, w1, w1-, w2+, w2, w2-
    """
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)
    return getevidence_fromfreqconf(f1, c1), getevidence_fromfreqconf(f2, c2)
