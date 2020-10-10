import Config
from NALGrammar import *


# ==== ==== ==== ==== ==== ====
# ==== NAL Inference Rules ====
# ==== ==== ==== ==== ==== ====

# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Binary truth value operations) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Binary AND
def band(*argv):
    res = 1
    for arg in argv:
        res = res * arg
    return res


# Binary OR
def bor(*argv):
    res = 1
    for arg in argv:
        res = res * (1 - arg)
    return 1 - res


def bnot(arg):
    return 1 - arg


# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Local inference) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Revision Rule
# Revises the same sentence with different truth values.
# j1 and j2 must have distinct evidential bases B1 and B2: B1 ⋂ B2 = Ø
# Inputs:
#   j1: Statement <f1,c1>
#   j2: Statement <f2,c2>
#   :- Statement <f3, c3>
def nal_revision(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = j1.subjectPredicate

    # Truth Value
    (wp1, w1, wn1), (wp2, w2, wn2) = getevidence_from2sentences(j1, j2)

    wp3 = wp1 + wp2
    wn3 = wn1 + wn2
    w3 = wp3 + wn3

    f3, c3 = getfreqconf_fromevidence(wp3, w3)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Expectation
# Choose the best statement to answer a task
# candidate or goal. If the statements are the same,
# the statement with the highest confidence is chosen.
# If they are different, the statement with the highest
# expectation is chosen.
# Inputs:
#   j1: Statement <f1,c1>
#   j2: Statement <f2,c2>
# Returns:
#   j1 or j2, depending on which is better
def nal_choice(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    subjpred1 = j1.subjectPredicate
    subjpred2 = j2.subjectPredicate

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

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


# Decision Rule
# Make the decision to accept a goal as an active goal
# Inputs:
#   p: plausability
#   d: decision
# Returns:
#   True or false, whether to make a goal active
def nal_decision(p, d):
    return p * (d - 0.5) > Config.t


# Expectation
# Inputs:
#   f: frequency
#   c: confidence
# Returns:
def nal_expectation(f, c):
    return c * (f - 0.5) + 0.5


# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Immediate inference) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Negation
# Inputs:
#   j: Statement <f,c>
def nal_negation(j):
    assert_sentence(j)
    # Truth Value
    f1, c1 = gettruthvalues_fromsentence(j)
    _, w1, w1n = getevidence_fromfreqconf(f1, c1)

    wp = w1n
    w = w1

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
    return 0


# Contrapositive
# Inputs:
#   j1:
#   j2:
# Returns:
def nal_contrapositive(j1, j2):
    return 0


# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Strong syllogism) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Deduction (Strong syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: S --> M <f2, c2>
#   :- S --> P <f3, c3>
# Truth Val:
#   f: and(f1,f2)
#   c: and(f1,f2,c1,c2)
def nal_deduction(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.subject, j1.statement.subjectPredicate.predicate)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    f3 = band(f1, f2)
    c3 = band(f1, f2, c1, c2)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Analogy (Strong syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: S <-> M <f2, c2>
#   :- S --> P <f3, c3>
# Truth Val:
#   f: and(f1,f2)
#   c: and(f2,c1,c2)
def nal_analogy(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.subject, j1.statement.subjectPredicate.predicate)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    f3 = band(f1, f2)
    c3 = band(f2, c1, c2)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Resemblance (Strong syllogism)
# Inputs:
#   j1: M <-> P <f1, c1>
#   j2: S <-> M <f2, c2>
#   :- S <-> P <f3, c3>
# Truth Val:
#   f: and(f1,f2)
#   c: and(or(f1,f2),c1,c2)
def nal_resemblance(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.subject, j1.statement.subjectPredicate.predicate)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    f3 = band(f1, f2)
    c3 = band(bor(f1, f2), c1, c2)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Similarity)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Weak syllogism) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Abduction
# Inputs:
#   j1: P --> M <f1, c1>
#   j2: S --> M <f2, c2>
#   :- S --> P <f3, c3>
# Truth Val:
#   w+: and(f1,f2,c1,c2)
#   w-: and(f1,c1,not(f2),c2)
#   w: and(f1,c1,c2)
def nal_abduction(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.subject, j1.statement.subjectPredicate.subject)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    wp = band(f1, f2, c1, c2)
    w = band(f1, c1, c2)

    f3, c3 = getfreqconf_fromevidence(wp, w)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Induction (Weak syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S --> P <f3, c3>
# Truth Val:
#   w+: and(f1,f2,c1,c2)
#   w-: and(f2,c2,not(f1),c1)
#   w: and(f2,c1,c2)
def nal_induction(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.predicate, j1.statement.subjectPredicate.predicate)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    wp = band(f1, f2, c1, c2)
    w = band(f2, c1, c2)

    f3, c3 = getfreqconf_fromevidence(wp, w)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Exemplification
# Inputs:
#   j1: P --> M <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S --> P <f3, c3>
# Truth Val:
#   w+: and(f1,c1,f2,c2)
#   w-: 0
#   w: w+
def nal_exemplification(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)
    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.predicate, j1.statement.subjectPredicate.subject)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    wp = band(f1, f2, c1, c2)
    w = wp

    f3, c3 = getfreqconf_fromevidence(wp, w)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Inheritance)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# Comparison
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S <-> P <f3, c3>
# Truth Val:
#   w+: and(f1,c1,f2,c2)
#   w: and(or(f1,f2),c1,c2)
def nal_comparison(j1, j2):
    assert_sentence(j1)
    assert_sentence(j2)

    # Subject Predicate
    resultsubjpred = SubjectPredicate(j2.statement.subjectPredicate.predicate, j1.statement.subjectPredicate.predicate)

    # Truth Value
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

    wp = band(f1, f2, c1, c2)
    w = band(bor(f1, f2), c1, c2)

    f3, c3 = getfreqconf_fromevidence(wp, w)

    resulttruth = TruthValue(f3, c3)

    resultStatement = Statement(resultsubjpred, Copula.Similarity)
    result = Sentence(resultStatement, resulttruth, Punctuation.Judgment)
    return result


# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Helper function) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Inputs:
#   wp: positive evidence w+
#   w: total evidence w
# Returns:
#   frequency, confidence
def getfreqconf_fromevidence(wp, w):
    f = wp / w
    c = w / (w + Config.k)
    return f, c


# Inputs:
#   f: frequency
#   c: confidence
# Returns:
#   w+, w, w-
def getevidence_fromfreqconf(f, c):
    wp = Config.k * f * c / (1 - c)
    w = Config.k * c / (1 - c)
    return wp, w, w - wp


# Inputs:
#   j1: Statement <f1, c1>
#   j2: Statement <f2, c2>
# Returns:
#   f1, c1, f2, c2
def gettruthvalues_from2sentences(j1, j2):
    return gettruthvalues_fromsentence(j1), gettruthvalues_fromsentence(j2)

# Inputs:
#   j: Statement <f1, c1>
# Returns:
#   f, c
def gettruthvalues_fromsentence(j):
    return j.truthValue.frequency, j.truthValue.confidence


# Inputs:
#   j1: Statement <f1, c1>
#   j2: Statement <f2, c2>
# Returns:
#   w1+, w1, w1-, w2+, w2, w2-
def getevidence_from2sentences(j1, j2):
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)
    return getevidence_fromfreqconf(f1, c1), getevidence_fromfreqconf(f2, c2)
