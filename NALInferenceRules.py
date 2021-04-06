import Config
import NALGrammar
import NALSyntax

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
    ======================================
    ++++ (Binary truth value operations) ++++
    ======================================
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
    ======================================
    ++++  (Local inference rules) ++++
    ======================================
"""


def Revision(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
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
    result_truth = NALGrammar.TruthValue(f3, c3)

    result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                            j1.statement.get_predicate_term(),
                                            j1.statement.copula)
    result = NALGrammar.Judgment(result_statement, result_truth)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Choice(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
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
        e1 = Expectation(f1, c1)
        e2 = Expectation(f2, c2)
        if e1 >= e2:
            best = j1
        else:
            best = j2

    return best


def Decision(d):
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


"""
    ======================================
    ++++ (Immediate Inference Rules) ++++
    ======================================
"""


def Negation(j):
    """
         Negation

         -----------------

         Input:
           j: Sentence (Statement <f, c>)

         Returns:
    """
    NALGrammar.assert_sentence(j)
    #todo return new Sentence
    j.value.frequency = 1 - j.value.frequency
    return j



def Conversion(j: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j)
    # Statement
    result_statement = NALGrammar.Statement(j.statement.get_predicate_term(),
                                            j.statement.get_subject_term(),
                                            j.statement.copula)

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        # compute values of combined evidence
        wp = band(j.value.frequency, j.value.confidence)
        w = wp
        if w == 0:
            print(str(j))
        f2, c2 = getfreqconf_fromevidence(wp, w)
        result_truth = NALGrammar.TruthValue(f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentence's evidential base
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result


# Contrapositive
# Inputs:
#   j1:
#   j2:
# Returns:
def Contrapositive(j1, j2):
    # todo
    return 0


"""
    ======================================
    ==== (Strong Syllogistic Rules) ====
    ======================================
"""


def Deduction(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                            j1.statement.get_predicate_term(),
                                            j1.statement.copula)


    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        f3 = band(f1, f2)
        c3 = band(f1, f2, c1, c2)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Analogy(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        #j1=M-->P, j2=S<->M
        result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.copula) # S-->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M-->P, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.copula) # S-->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1=P-->M, j2=S<->M
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.copula) # P-->S
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P-->M, j2=M<->S
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                j2.statement.get_predicate_term(),
                                                j1.statement.copula) # P-->S
    else:
        assert(False), "Error: Invalid inputs to nal_analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    result = None
    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        f3 = band(f1, f2)
        c3 = band(f2, c1, c2)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Resemblance(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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

    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_predicate_term():
        # j1=M<->P, j2=S<->M
        result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.copula)  # S<->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M<->P, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.copula)  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P<->M, j2=S<->M
        result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                                j1.statement.get_subject_term(),
                                                j1.statement.copula)  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P<->M, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.copula)  # S<->P
    else:
        assert (
            False), "Error: Invalid inputs to nal_resemblance: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        f3 = band(f1, f2)
        c3 = band(bor(f1, f2), c1, c2)

        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


"""
    ======================================
    ++++ (Weak Syllogistic Rules) ++++
    ======================================
"""


def Abduction(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                            j1.statement.get_subject_term(),
                                            j1.statement.copula)

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(f1, c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Induction(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                j1.statement.get_predicate_term(), j1.statement.copula)

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(f2, c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Exemplification(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    # Statement
    result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                j1.statement.get_subject_term(), j1.statement.copula)

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = wp
        f3, c3 = getfreqconf_fromevidence(wp, w)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)
    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


def Comparison(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
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
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_subject_term() == j2.statement.get_subject_term():
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Similarity)
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                                j1.statement.get_subject_term(),
                                                NALSyntax.Copula.Similarity)
    else:
        assert(False), "Error: Invalid inputs to nal_comparison: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        wp = band(f1, f2, c1, c2)
        w = band(bor(f1, f2), c1, c2)
        f3, c3 = getfreqconf_fromevidence(wp, w)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

"""
    ======================================
    ++++ (The Composition Rules) ++++
    ======================================
"""
def IntensionalIntersection(j1, j2):
    """
        Intensional Intersection (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>)
            and
            j2: Sentence (T2 --> M <f2, c2>)

            OR

            j1: Sentence (M --> T1 <f1, c1>)
            and
            j2: Sentence (M --> T2 <f2, c2>)
        Evidence:
            f: band(f1,f2)
            c: band(c1,c2)
        Returns:
            For inputs j1: (T1 --> M), j2: (T2 --> M):
                :- Sentence ((T1 | T2) --> M)
            For inputs j1: (M --> T1) , j2: (M --> T2):
                :- Sentence (M --> (T1 | T2))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1: Sentence(T1 --> M < f1, c1 >)
        #j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term()],
                                                NALSyntax.TermConnector.IntensionalIntersection)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Inheritance) # ((T1 | T2) --> M)

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

            # compute values of combined evidence
            f3 = band(f1, f2)
            c3 = band(c1, c2)
            result_truth = NALGrammar.TruthValue(f3, c3)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        #j1: Sentence(M --> T1 < f1, c1 >)
        #j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                j2.statement.get_predicate_term()],
                                                NALSyntax.TermConnector.IntensionalIntersection)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                NALSyntax.Copula.Inheritance)# (M --> (T1 | T2))

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

            # compute values of combined evidence
            f3 = bor(f1, f2)
            c3 = band(c1, c2)
            result_truth = NALGrammar.TruthValue(f3, c3)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)



    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ExtensionalIntersection(j1, j2):
    """
        Extensional Intersection (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>)
            and
            j2: Sentence (T2 --> M <f2, c2>)

            OR

            j1: Sentence (M --> T1 <f1, c1>)
            and
            j2: Sentence (M --> T2 <f2, c2>)
        Evidence:
            f: band(f1,f2)
            c: band(c1,c2)
        Returns:
            For inputs j1: (T1 --> M), j2: (T2 --> M):
                :- Sentence ((T1 & T2) --> M)
            For inputs j1: (M --> T1) , j2: (M --> T2):
                :- Sentence (M --> (T1 & T2))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1: Sentence(T1 --> M < f1, c1 >)
        #j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term()],
                                                NALSyntax.TermConnector.ExtensionalIntersection)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Inheritance) # ((T1 & T2) --> M)

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

            # compute values of combined evidence
            f3 = bor(f1, f2)
            c3 = band(c1, c2)
            result_truth = NALGrammar.TruthValue(f3, c3)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        #j1: Sentence(M --> T1 < f1, c1 >)
        #j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                j2.statement.get_predicate_term()],
                                                NALSyntax.TermConnector.ExtensionalIntersection)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                NALSyntax.Copula.Inheritance)# (M --> (T1 & T2))

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

            # compute values of combined evidence
            f3 = band(f1, f2)
            c3 = band(c1, c2)
            result_truth = NALGrammar.TruthValue(f3, c3)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def Difference(j1, j2):
    """
        Extensional or Intensional Difference (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>)
            and
            j2: Sentence (T2 --> M <f2, c2>)

            OR

            j1: Sentence (M --> T1 <f1, c1>)
            and
            j2: Sentence (M --> T2 <f2, c2>)
        Evidence:
            f: band(f1,f2)
            c: band(c1,c2)
        Returns:
            For inputs j1: (T1 --> M), j2: (T2 --> M):
                :- Sentence ((T1 ~ T2) --> M)
            For inputs j1: (M --> T1) , j2: (M --> T2):
                :- Sentence (M --> (T1 - T2))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1: Sentence(T1 --> M < f1, c1 >)
        #j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term()],
                                                NALSyntax.TermConnector.IntensionalDifference)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                NALSyntax.Copula.Inheritance) # ((T1 ~ T2) --> M)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        #j1: Sentence(M --> T1 < f1, c1 >)
        #j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                j2.statement.get_predicate_term()],
                                                NALSyntax.TermConnector.ExtensionalDifference)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                NALSyntax.Copula.Inheritance)# (M --> (T1 - T2))

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)

        # compute values of combined evidence
        f3 = band(f1, not(f2))
        c3 = band(c1, c2)
        result_truth = NALGrammar.TruthValue(f3, c3)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


"""
    ======================================
    ++++ (Helper Functions) ++++
    ======================================
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


def gettruthvalues_from2sentences(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
    """
        Input:
            j1: Statement <f1, c1>

            j2: Statement <f2, c2>
        Returns:
            f1, c1, f2, c2
    """
    return gettruthvalues_fromsentence(j1), gettruthvalues_fromsentence(j2)


def gettruthvalues_fromsentence(j: NALGrammar.Sentence):
    """
        Input:
            j: Statement <f, c>
        Returns:
            f, c
    """
    return j.value.frequency, j.value.confidence


def getevidence_from2sentences(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
    """
        Input:
            j1: Statement <f1, c1>

            j2: Statement <f2, c2>
        Returns:
            w1+, w1, w1-, w2+, w2, w2-
    """
    (f1, c1), (f2, c2) = gettruthvalues_from2sentences(j1, j2)
    return getevidence_fromfreqconf(f1, c1), getevidence_fromfreqconf(f2, c2)
