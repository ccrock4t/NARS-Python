import Config
import Global
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
    ++++ (Inference rule truth value operations) ++++
    ======================================
"""
def F_Revision(wp1, wn1, wp2, wn2):
    """
        :return: F_rev
    """
    # compute values of combined evidence
    wp = wp1 + wp2
    wn = wn1 + wn2
    w = wp + wn
    f_rev, c_rev = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_rev, c_rev)


def F_Negation(f,c):
    """
        f_neg = 1 - f
        c_neg = c
        :return: F_neg
    """
    return NALGrammar.TruthValue(1-f,c)


def F_Conversion(f,c):
    """
        wp = AND(f, c)
        wn = AND(NOT(f), c)
        :return: F_cnv
    """
    # compute values of combined evidence
    wp = band(f, c)
    w = wp
    f_cnv, c_cnv = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_cnv, c_cnv)

def F_Contraposition(f,c):
    """
        wp = 0
        wn = AND(NOT(f), c)
        :return: F_cnt
    """
    wp = 0
    wn = band(bnot(f), c)
    w = wn
    f_cnt, c_cnt = get_truthvalue_from_evidence(wp, w)

    return NALGrammar.TruthValue(f_cnt, c_cnt)


def F_Deduction(f1,c1,f2,c2):
    """
        f_ded: and(f1,f2)
        c_ded: and(f1,f2,c1,c2)

        :return: F_ded: Truth-Value (f,c)
    """
    f3 = band(f1, f2)
    c3 = band(f1, f2, c1, c2)
    return NALGrammar.TruthValue(f3, c3)

def F_Analogy(f1,c1,f2,c2):
    """
        f_ana: AND(f1,f2)
        c_ana: AND(f2,c1,c2)

        :return: F_ana: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_ana = band(f1, f2)
    c_ana = band(f2, c1, c2)
    return NALGrammar.TruthValue(f_ana, c_ana)

def F_Resemblance(f1,c1,f2,c2):
    """
        f_res = AND(f1,f2)
        c_res = AND(OR(f1,f2),c1,c2)

        :return: F_res
    """
    f_res = band(f1, f2)
    c_res = band(bor(f1, f2), c1, c2)

    return NALGrammar.TruthValue(f_res, c_res)

def F_Abduction(f1,c1,f2,c2):
    """
        wp = AND(f1,f2,c1,c2)
        w = AND(f1,c1,c2)

        :return: F_abd: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(f1, c1, c2)
    f_abd, c_abd = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_abd, c_abd)

def F_Induction(f1,c1,f2,c2):
    """
    :return: F_ind: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(f2, c1, c2)
    f_ind, c_ind = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_ind, c_ind)


def F_Exemplification(f1,c1,f2,c2):
    """
    :return: F_exe: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = wp
    f_exe, c_exe = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f_exe, c_exe)

def F_Comparison(f1,c1,f2,c2):
    """
        :return: F_com: Truth-Value (f,c)
    """
    # compute values of combined evidence
    wp = band(f1, f2, c1, c2)
    w = band(bor(f1, f2), c1, c2)
    f3, c3 = get_truthvalue_from_evidence(wp, w)
    return NALGrammar.TruthValue(f3, c3)

def F_Intersection(f1,c1,f2,c2):
    """
    :return: F_int: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f_int = band(f1, f2)
    c_int = band(c1, c2)
    return NALGrammar.TruthValue(f_int, c_int)


def F_Union(f1,c1,f2,c2):
    """
    :return: F_uni: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f3 = bor(f1, f2)
    c3 = band(c1, c2)
    return NALGrammar.TruthValue(f3, c3)


def F_Difference(f1,c1,f2,c2):
    """
    :return: F_dif: Truth-Value (f,c)
    """
    # compute values of combined evidence
    f3 = band(f1, not (f2))
    c3 = band(c1, c2)
    return NALGrammar.TruthValue(f3, c3)

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
                j1.statement.term.get_formatted_string() == j2.statement.term.get_formatted_string()), "Cannot revise sentences for 2 different statements"

    #todo handle occurrence_time
    occurrence_time = None

    # Get Truth Value
    (wp1, w1, wn1), (wp2, w2, wn2) = getevidence_from2sentences(j1, j2)
    result_truth = F_Revision(wp1=wp1,wn1=wn1,wp2=wp2,wn2=wn2)

    result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                            j1.statement.get_predicate_term(),
                                            j1.statement.get_copula())
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
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

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


def Negation(j: NALGrammar.Sentence):
    """
         Negation

         -----------------

         Input:
           j: Sentence (Statement <f, c>)

         Returns:
    """
    NALGrammar.assert_sentence(j)

    result_statement = NALGrammar.Statement(j.statement.get_subject_term(),
                                            j.statement.get_predicate_term(),
                                            j.statement.get_copula(),
                                            statement_connector=NALSyntax.TermConnector.Negation)

    occurrence_time = j.stamp.occurrence_time

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        result_truth = F_Negation(j.value.frequency, j.value.confidence)
        result = NALGrammar.Judgment(result_statement, result_truth,occurrence_time=occurrence_time)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        assert "error"

    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result



def Conversion(j: NALGrammar.Sentence):
    """
        Conversion Rule

        Reverses the subject and predicate.
        -----------------

        Input:
            j: Sentence (S --> P <f1, c1>)

            must have a frequency above zero, or else the confidence of the conclusion will be zero

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
                                            j.statement.get_copula())

    occurrence_time = j.stamp.occurrence_time

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        result_truth = F_Conversion(j.value.frequency, j.value.confidence)
        result = NALGrammar.Judgment(result_statement, result_truth, occurrence_time)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentence's evidential base
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)
    result.stamp.from_conversion = True

    return result



def Contraposition(j):
    """
    Contraposition
    Inputs:
      j: (S ==> P)

    Frequency must be below one or confidence of conclusion will be zero
    
    :param j:
    :return: ((--,P) ==> (--,S))
    """
    NALGrammar.assert_sentence(j)
    # Statement
    negated_predicate_term = NALGrammar.CompoundTerm([j.statement.get_predicate_term()], NALSyntax.TermConnector.Negation)
    negated_subject_term = NALGrammar.CompoundTerm([j.statement.get_subject_term()],
                                                     NALSyntax.TermConnector.Negation)

    result_statement = NALGrammar.Statement(negated_predicate_term,
                                            negated_subject_term,
                                            j.statement.get_copula())

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        result_truth = F_Contraposition(j.value.frequency,j.value.confidence)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentence's evidential base
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return result

def ExtensionalImage(j: NALGrammar.Sentence):
    """
    Intensional Image
    Inputs:
      j: ((*,S,P) --> R)

    :param j:
    :returns: array of
    (S --> (/,R,_,P))
    and
    (P --> (/,R,S,_))
    """
    NALGrammar.assert_sentence(j)

    # Statement
    S = j.statement.get_subject_term().subterms[0];
    P = j.statement.get_subject_term().subterms[1];
    R = j.statement.get_predicate_term()

    image_term_1 = NALGrammar.CompoundTerm([R, Global.Global.IMAGE_PLACEHOLDER_TERM, P],
                                         NALSyntax.TermConnector.ExtensionalImage)

    result_statement_1 = NALGrammar.Statement(S,
                                            image_term_1,
                                            NALSyntax.Copula.Inheritance)

    image_term_2 = NALGrammar.CompoundTerm([R, S, Global.Global.IMAGE_PLACEHOLDER_TERM],
                                         NALSyntax.TermConnector.ExtensionalImage)

    result_statement_2 = NALGrammar.Statement(P,
                                            image_term_2,
                                            NALSyntax.Copula.Inheritance)

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        result_truth = NALGrammar.TruthValue(j.value.frequency, j.value.confidence)
        result_1 = NALGrammar.Judgment(result_statement_1, result_truth)
        result_2 = NALGrammar.Judgment(result_statement_2, result_truth)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        result_1 = NALGrammar.Question(result_statement_1)
        result_2 = NALGrammar.Question(result_statement_2)

    # merge in the parent sentence's evidential base
    result_1.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)
    result_2.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return [result_1, result_2]

def IntensionalImage(j: NALGrammar.Sentence):
    """
    Intensional Image
    Inputs:
      j: (R --> (*,S,P))

    :param j:
    :returns: array of
    ((/,R,_,P) --> S)
    and
    ((/,R,S,_) --> P)
    """
    NALGrammar.assert_sentence(j)

    # Statement
    S = j.statement.get_predicate_term().subterms[0];
    P = j.statement.get_predicate_term().subterms[1];
    R = j.statement.get_subject_term()

    image_term_1 = NALGrammar.CompoundTerm([R, Global.Global.IMAGE_PLACEHOLDER_TERM, P],
                                         NALSyntax.TermConnector.IntensionalImage)

    result_statement_1 = NALGrammar.Statement(image_term_1,
                                              S,
                                            NALSyntax.Copula.Inheritance)

    image_term_2 = NALGrammar.CompoundTerm([R, S, Global.Global.IMAGE_PLACEHOLDER_TERM],
                                         NALSyntax.TermConnector.IntensionalImage)

    result_statement_2 = NALGrammar.Statement(image_term_2,
                                              P,
                                            NALSyntax.Copula.Inheritance)

    if j.punctuation == NALSyntax.Punctuation.Judgment:
        result_truth = NALGrammar.TruthValue(j.value.frequency, j.value.confidence)
        result_1 = NALGrammar.Judgment(result_statement_1, result_truth)
        result_2 = NALGrammar.Judgment(result_statement_2, result_truth)
    elif j.punctuation == NALSyntax.Punctuation.Question:
        result_1 = NALGrammar.Question(result_statement_1)
        result_2 = NALGrammar.Question(result_statement_2)

    # merge in the parent sentence's evidential base
    result_1.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)
    result_2.stamp.evidential_base.merge_sentence_evidential_base_into_self(j)

    return [result_1, result_2]

"""
    ======================================
    ==== (First-order and Higher-order Syllogism) ====
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
            F_ded
        Returns:
            :- Sentence (S --> P <f3, c3>)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    # Statement
    result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                            j1.statement.get_predicate_term(),
                                            j1.statement.get_copula())

    result_truth= None
    if j1.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = F_Deduction(f1,c1,f2,c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question:
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
                                                j1.statement.get_copula()) # S-->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M-->P, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula()) # S-->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1=P-->M, j2=S<->M
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.get_copula()) # P-->S
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P-->M, j2=M<->S
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                j2.statement.get_predicate_term(),
                                                j1.statement.get_copula()) # P-->S
    else:
        assert(False), "Error: Invalid inputs to nal_analogy: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    result = None
    if j1.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = F_Analogy(f1, c1, f2, c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question:
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
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        # j1=M<->P, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j1.statement.get_predicate_term(),
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        # j1=P<->M, j2=S<->M
        result_statement = NALGrammar.Statement(j2.statement.get_subject_term(),
                                                j1.statement.get_subject_term(),
                                                j1.statement.get_copula())  # S<->P
    elif j1.statement.get_predicate_term() == j2.statement.get_subject_term():
        # j1=P<->M, j2=M<->S
        result_statement = NALGrammar.Statement(j2.statement.get_predicate_term(),
                                                j2.statement.get_subject_term(),
                                                j1.statement.get_copula())  # S<->P
    else:
        assert (
            False), "Error: Invalid inputs to nal_resemblance: " + j1.get_formatted_string() + " and " + j2.get_formatted_string()

    if j1.punctuation == NALSyntax.Punctuation.Judgment:
        # Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

        result_truth = F_Resemblance(f1,c1,f2,c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

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
                                            j1.statement.get_copula())

    if j1.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

        result_truth = F_Abduction(f1,c1,f2,c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question:
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
                                            j1.statement.get_predicate_term(), j1.statement.get_copula())

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

        result_truth = F_Induction(f1,c1,f2,c2)
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
                                            j1.statement.get_subject_term(), j1.statement.get_copula())

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = F_Exemplification(f1,c1,f2,c2)
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
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

        result_truth = F_Comparison(f1,c1,f2,c2)
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
def IntensionalIntersectionOrDisjunction(j1, j2):
    """
        First Order: Intensional Intersection (Strong Inference)
        Higher Order: Disjunction

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>) (Sentence (T1 ==> M <f1, c1>))
            and
            j2: Sentence (T2 --> M <f2, c2>) (Sentence (T2 ==> M <f2, c2>))

            OR

            j1: Sentence (M --> T1 <f1, c1>) (Sentence (M ==> T1 <f1, c1>))
            and
            j2: Sentence (M --> T2 <f2, c2>) (Sentence (M ==> T2 <f2, c2>))
        Evidence:
            F_int

            OR

            F_uni
        Returns:
            :- Sentence ((T1 | T2) --> M) (Sentence ((T1 || T2) --> M))
            OR
            :- Sentence (M --> (T1 | T2)) (Sentence (M --> (T1 || T2)))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()
    # Statement
    connector = None
    copula = None
    if NALSyntax.Copula.is_first_order(j1_copula) and NALSyntax.Copula.is_first_order(j2_copula):
        connector = NALSyntax.TermConnector.IntensionalIntersection
        copula = NALSyntax.Copula.Inheritance
    else:
        #higher-order, could be temporal
        #todo temporal disjunction
        connector = NALSyntax.TermConnector.Disjunction
        copula = NALSyntax.Copula.Implication
    # Statement
    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1: Sentence(T1 --> M < f1, c1 >)
        #j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                 j2.statement.get_subject_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                copula) # ((T1 | T2) --> M)

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

            result_truth = F_Intersection(f1,c1,f2,c2)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        #j1: Sentence(M --> T1 < f1, c1 >)
        #j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                 j2.statement.get_predicate_term()],
                                                term_connector=connector)  # (T1 & T2)

        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                copula)# (M --> (T1 | T2))

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)

            result_truth = F_Union(f1,c1,f2,c2)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)



    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ExtensionalIntersectionOrConjunction(j1, j2):
    """
        First-Order: Extensional Intersection (Strong Inference)
        Higher-Order: Conjunction

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>) (Sentence (T1 ==> M <f1, c1>))
            and
            j2: Sentence (T2 --> M <f2, c2>) (Sentence (T2 ==> M <f2, c2>))

            OR

            j1: Sentence (M --> T1 <f1, c1>) (Sentence (M ==> T1 <f1, c1>))
            and
            j2: Sentence (M --> T2 <f2, c2>) (Sentence (M ==> T2 <f2, c2>))
        Evidence:
            F_uni

            OR

            F_int
        Returns:
            :- Sentence ((T1 & T2) --> M) (Sentence ((T1 && T2) ==> M))
            OR
            :- Sentence (M --> (T1 & T2)) (Sentence (M ==> (T1 && T2)))
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)

    j1_copula = j1.statement.get_copula()
    j2_copula = j2.statement.get_copula()
    # Statement
    connector = None
    copula = None
    if NALSyntax.Copula.is_first_order(j1_copula) and NALSyntax.Copula.is_first_order(j2_copula):
        connector = NALSyntax.TermConnector.ExtensionalIntersection
        copula = NALSyntax.Copula.Inheritance
    else:
        #higher-order, could be temporal
        #todo temporal conjunction
        connector = NALSyntax.TermConnector.Conjunction
        copula = NALSyntax.Copula.Implication

    if j1.statement.get_predicate_term() == j2.statement.get_predicate_term():
        #j1: Sentence(T1 --> M < f1, c1 >)
        #j2: Sentence(T2 --> M < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_subject_term(),
                                                 j2.statement.get_subject_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(compound_term,
                                                j1.statement.get_predicate_term(),
                                                copula) # ((T1 & T2) --> M)

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = F_Union(f1,c1,f2,c2)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    elif j1.statement.get_subject_term() == j2.statement.get_subject_term():
        #j1: Sentence(M --> T1 < f1, c1 >)
        #j2: Sentence(M --> T2 < f2, c2 >)
        compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                                 j2.statement.get_predicate_term()],
                                                term_connector=connector)  # (T1 & T2)
        result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                                compound_term,
                                                copula)# (M --> (T1 & T2))

        if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
            # Get Truth Value
            (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
            result_truth = F_Intersection(f1,c1,f2,c2)
            result = NALGrammar.Judgment(result_statement, result_truth)
        elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
            result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def IntensionalDifference(j1, j2):
    """
        Intensional Difference (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------

        Input:
            j1: Sentence (T1 --> M <f1, c1>)
            and
            j2: Sentence (T2 --> M <f2, c2>)
        Evidence:
            f: band(f1,f2)
            c: band(c1,c2)
        Returns:
            :- Sentence ((T1 ~ T2) --> M)
    """
    NALGrammar.assert_sentence(j1)
    NALGrammar.assert_sentence(j2)
    assert j1.statement.get_predicate_term() == j2.statement.get_predicate_term()

    compound_term = NALGrammar.CompoundTerm([j1.statement.get_predicate_term(),
                                            j2.statement.get_predicate_term()],
                                            NALSyntax.TermConnector.ExtensionalDifference) # (T1 - T2)
    result_statement = NALGrammar.Statement(j1.statement.get_subject_term(),
                                            compound_term,
                                            NALSyntax.Copula.Inheritance)# (M --> (T1 - T2))

    if j1.punctuation == NALSyntax.Punctuation.Judgment and j2.punctuation == NALSyntax.Punctuation.Judgment:
        # Get Truth Value
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = F_Difference(f1,c1,f2,c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def ExtensionalDifference(j1, j2):
    """
        Extensional Difference (Strong Inference)

        Assumes: j1 and j2 do not have evidential overlap
        -----------------
        Input:
            j1: Sentence (M --> T1 <f1, c1>)
            and
            j2: Sentence (M --> T2 <f2, c2>)
        Evidence:
            f: band(f1,f2)
            c: band(c1,c2)
        Returns:
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
        (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
        result_truth = F_Difference(f1,c1,f2,c2)
        result = NALGrammar.Judgment(result_statement, result_truth)
    elif j1.punctuation == NALSyntax.Punctuation.Question or j2.punctuation == NALSyntax.Punctuation.Question:
        result = NALGrammar.Question(result_statement)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result


"""
    ======================================
    ++++ (The Temporal Inference Rules) ++++
    ======================================
"""
def Temporal_Induction(j1: NALGrammar.Judgment, j2: NALGrammar.Judgment):
    """
        Temporal Induction

        Input:
            j1: Event <f1, c1> {tense}

            j2: Event <f2, c2> {tense}
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S =|> P <f3, c3>)
            :- or Sentence (S =/> P <f3, c3>)
            :- or Sentence (P =/> S <f3, c3>)
    """
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    j1_statement_term = j1.statement.term
    j2_statement_term = j2.statement.term

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # j1 =|> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term, NALSyntax.Copula.ConcurrentImplication)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 =/> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term, NALSyntax.Copula.PredictiveImplication)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 =/> j1
        result_statement = NALGrammar.Statement(j2_statement_term, j1_statement_term, NALSyntax.Copula.PredictiveImplication)

    # calculate induction truth value
    result_truth = F_Induction(f1, c1, f2, c2)
    result = NALGrammar.Judgment(result_statement, result_truth)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

def Temporal_Comparison(j1: NALGrammar.Judgment, j2: NALGrammar.Judgment):
    """
        Temporal Induction

        Input:
            A: Event <f1, c1> {tense}

            B: Event <f2, c2> {tense}
        Evidence:
            w+: and(f1,f2,c1,c2)

            w-: and(f2,c2,not(f1),c1)

            w: and(f2,c1,c2)
        Returns:
            :- Sentence (S <|> P <f3, c3>)
            :- or Sentence (S </> P <f3, c3>)
            :- or Sentence (P </> S <f3, c3>)
    """
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    j1_statement_term = j1.statement.term
    j2_statement_term = j2.statement.term

    if j1.stamp.occurrence_time == j2.stamp.occurrence_time:
        # <|>
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term, NALSyntax.Copula.ConcurrentEquivalence)
    elif j1.stamp.occurrence_time < j2.stamp.occurrence_time:
        # j1 </> j2
        result_statement = NALGrammar.Statement(j1_statement_term, j2_statement_term, NALSyntax.Copula.PredictiveEquivalence)
    elif j2.stamp.occurrence_time < j1.stamp.occurrence_time:
        # j2 </> j1
        result_statement = NALGrammar.Statement(j2_statement_term, j1_statement_term, NALSyntax.Copula.PredictiveEquivalence)

    # calculate induction truth value
    result_truth = F_Comparison(f1,c1,f2,c2)
    result = NALGrammar.Judgment(result_statement, result_truth)

    # merge in the parent sentences' evidential bases
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j1)
    result.stamp.evidential_base.merge_sentence_evidential_base_into_self(j2)

    return result

"""
    ======================================
    ++++ (Helper Functions) ++++
    ======================================
"""

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

def getevidentialvalues_from2sentences(j1: NALGrammar.Sentence, j2: NALGrammar.Sentence):
    """
        Input:
            j1: Statement <f1, c1>

            j2: Statement <f2, c2>
        Returns:
            f1, c1, f2, c2
    """
    return getevidentialvalues_fromsentence(j1), getevidentialvalues_fromsentence(j2)


def getevidentialvalues_fromsentence(j: NALGrammar.Sentence):
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
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    return get_evidence_fromfreqconf(f1, c1), get_evidence_fromfreqconf(f2, c2)
