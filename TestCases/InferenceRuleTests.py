import NALGrammar
import NALInferenceRules

"""
    Author: Christian Hahm
    Created: March 23, 2021
    Purpose: Unit Testing for the Narsese Inference Rules.
        Tests if the inference rules are calculating truth values using the correct truth value functions.
"""



def revision():
    """
        Test revision
        j1: (S-->P). %1.0;0.9%
        j2: (S-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.95%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(S-->P). %1.0;0.9%")

    output = NALInferenceRules.Local.Revision(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"), value=NALInferenceRules.TruthValueFunctions.F_Revision(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success,"TEST FAILURE: Revision test failed: " + output.get_formatted_string_no_id()


def first_order_deduction():
    """
        Test first-order deduction:
        j1: (S-->M). %1.0;0.9%
        j2: (M-->P). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")

    output = NALInferenceRules.Syllogistic.Deduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"), value=NALInferenceRules.TruthValueFunctions.F_Deduction(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: First-order Deduction test failed: " + output.get_formatted_string_no_id()

def first_order_induction():
    """
        Test first-order induction:
        j1: (M-->P). %1.0;0.9%
        j2: (M-->S). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")

    output = NALInferenceRules.Syllogistic.Induction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"), value=NALInferenceRules.TruthValueFunctions.F_Induction(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: First-order Induction test failed: " + output.get_formatted_string_no_id()

def first_order_abduction():
    """
        Test first-order abduction:
        j1: (P-->M). %1.0;0.9%
        j2: (S-->M). %1.0;0.9%

        :- (S-->P). %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")

    output = NALInferenceRules.Syllogistic.Abduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"), value=NALInferenceRules.TruthValueFunctions.F_Abduction(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success,"TEST FAILURE: First-order Abduction test failed: " + output.get_formatted_string_no_id()

def first_order_analogy():
    """
        Test first-order analogy:
        j1: (S-->M). %1.0;0.9%
        j2: (P<->M). %1.0;0.9%

        :- (S-->P). %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(P<->M). %1.0;0.9%")

    output = NALInferenceRules.Syllogistic.Analogy(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"), value=NALInferenceRules.TruthValueFunctions.F_Analogy(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: First-order Analogy test failed: " + output.get_formatted_string_no_id()

def first_order_intensional_composition():
    """
        Test Intensional Composition rules:
        j1: (M --> S). %1.0;0.9%
        j2: (M --> P). %1.0;0.9%

        :- (M --> (S | P)).
        :- (M --> (S & P)).
        :- (M --> (S - P)).
        :- (M --> (P - S)).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->P). %1.0;0.9%")

    """
        Extensional intersection
    """
    output = NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(M-->(&,S,P))"), value=NALInferenceRules.TruthValueFunctions.F_Intersection(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))


    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition - Extensional intersection test failed: " + output.get_formatted_string_no_id()
    """
        Intensional intersection
    """
    output = NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(M-->(|,S,P))"), value=NALInferenceRules.TruthValueFunctions.F_Union(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition - Intensional intersection test failed: " + output.get_formatted_string_no_id()

    """
        Extensional difference
    """
    output = NALInferenceRules.Composition.ExtensionalDifference(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(M-->(-,S,P))"), value=NALInferenceRules.TruthValueFunctions.F_Difference(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition Extensional difference test failed: " + output.get_formatted_string_no_id()

    """
        Swapped Extensional difference
    """
    output = NALInferenceRules.Composition.ExtensionalDifference(j2, j1)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(M-->(-,P,S))"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Difference(
                                                         j2.value.frequency,
                                                         j2.value.confidence,
                                                         j1.value.frequency,
                                                         j1.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: Intensional Composition Swapped Extensional difference test failed: " + output.get_formatted_string_no_id()

def first_order_extensional_composition():
    """
        Test Extensional Composition rules:
        j1: (S-->M). %1.0;0.9%
        j2: (P-->M). %1.0;0.9%

        :- ((S | P) --> M).
        :- ((S & P) --> M).
        :- ((S ~ P) --> M).
        :- ((P ~ S) --> M).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(S-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")

    """
        Extensional intersection
    """
    output = NALInferenceRules.Composition.ConjunctionOrExtensionalIntersection(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("((&,S,P)-->M)"), value=NALInferenceRules.TruthValueFunctions.F_Union(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))


    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition - Extensional intersection test failed: " + output.get_formatted_string_no_id()
    """
        Intensional intersection
    """
    output = NALInferenceRules.Composition.DisjunctionOrIntensionalIntersection(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("((|,S,P)-->M)"), value=NALInferenceRules.TruthValueFunctions.F_Intersection(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition - Intensional intersection test failed: " + output.get_formatted_string_no_id()

    """
        Intensional difference
    """
    output = NALInferenceRules.Composition.IntensionalDifference(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("((~,S,P)-->M)"), value=NALInferenceRules.TruthValueFunctions.F_Difference(j1.value.frequency,
                                                                                                                                                                       j1.value.confidence,
                                                                                                                                                                       j2.value.frequency,
                                                                                                                                                                       j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success, "TEST FAILURE: Intensional Composition Intensional difference test failed: " + output.get_formatted_string_no_id()

    """
        Swapped Intensional difference
    """
    output = NALInferenceRules.Composition.IntensionalDifference(j2, j1)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("((~,P,S)-->M)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Difference(
                                                         j2.value.frequency,
                                                         j2.value.confidence,
                                                         j1.value.frequency,
                                                         j1.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: Intensional Composition Swapped Intensional difference test failed: " + output.get_formatted_string_no_id()

def first_order_exemplification():
    """
        Test Extensional Composition rules:
        j1: (P-->M). %1.0;0.9%
        j2: (M-->S). %1.0;0.9%

        :- (S --> P).
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(P-->M). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(M-->S). %1.0;0.9%")

    output = NALInferenceRules.Syllogistic.Exemplification(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(S-->P)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Exemplification(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: Exemplification test failed: " + output.get_formatted_string_no_id()


def extensional_image():
    """
        Test Extensional Image rule:
        j: ((*,S,P)-->R). %1.0;0.9%

        :- j: (S-->(/,R,_,P)). %1.0;0.9%
        :- j: (P-->(/,R,S,_)). %1.0;0.9%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((*,S,P)-->R). %1.0;0.9%")

    outputs = NALInferenceRules.Immediate.ExtensionalImage(j1)

    for output in outputs:
        assert output.value.frequency == j1.value.frequency and output.value.confidence == j1.value.confidence,"TEST FAILURE: Extensional Image test failed: " + output.get_formatted_string_no_id()



def conditional_analogy():
    """
        Test Conditional Analogy rule:
        j1: S<=>P %1.0;0.9%
        j2: S %1.0;0.9%

        :- P %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("(a-->b). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)<=>(c-->d)). %1.0;0.9%")


    output = NALInferenceRules.Conditional.ConditionalAnalogy(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(c-->d)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Analogy(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success,"TEST FAILURE: Conditional Analogy test failed: " + output.get_formatted_string_no_id()

def conditional_deduction():
    """
        Test Conditional Deduction rule:
        j1: S==>P %1.0;0.9%
        j2: S %1.0;0.9%

        :- P %1.0;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)==>(c-->d)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(a-->b). %1.0;0.9%")

    output = NALInferenceRules.Conditional.ConditionalJudgmentDeduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(c-->d)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Deduction(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()
    assert success,"TEST FAILURE: Conditional Deduction test failed: " + output.get_formatted_string_no_id()

def conditional_abduction():
    """
        Test Conditional Abduction rule:
        j1: S==>P %1.0;0.9%
        j2: P %1.0;0.9%

        :- S %0.81;0.81%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((a-->b)==>(c-->d)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(c-->d). %1.0;0.9%")

    output = NALInferenceRules.Conditional.ConditionalJudgmentAbduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(a-->b)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Abduction(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success,"TEST FAILURE: Conditional Abduction test failed: " + output.get_formatted_string_no_id()

def conditional_conjunctional_deduction():
    """
        Test Conditional Conjunctional Deduction rule:
        j1: (C1 && C2 && ... CN && S) ==> P %1.0;0.9%
        j2: S %1.0;0.9%

        :- (C1 && C2 && ... CN) ==> P %1.0;0.81%
    """

    # test removal of second element
    j1 = NALGrammar.Sentences.new_sentence_from_string("((&&,(a-->b),(c-->d))==>(e-->f)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("(c-->d). %1.0;0.9%")

    output = NALInferenceRules.Conditional.ConditionalConjunctionalDeduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("((a-->b)==>(e-->f))"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Deduction(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success, "TEST FAILURE: Conditional Conjunctional Deduction test failed: " + output.get_formatted_string_no_id()

def conditional_conjunctional_abduction():
    """
        Test Conditional Conjunctional Deduction rule:
        j1: (C1 && C2 && ... CN && S) ==> P %1.0;0.9%
        j2: (C1 && C2 && ... CN) ==> P %1.0;0.9%

        :- S %1.0;0.45%
    """
    j1 = NALGrammar.Sentences.new_sentence_from_string("((&&,(a-->b),(c-->d))==>(e-->f)). %1.0;0.9%")
    j2 = NALGrammar.Sentences.new_sentence_from_string("((c-->d)==>(e-->f)). %1.0;0.9%")

    output = NALInferenceRules.Conditional.ConditionalConjunctionalAbduction(j1, j2)

    success_criteria = NALGrammar.Sentences.Judgment(NALGrammar.Terms.StatementTerm.from_string("(a-->b)"),
                                                     value=NALInferenceRules.TruthValueFunctions.F_Abduction(
                                                         j1.value.frequency,
                                                         j1.value.confidence,
                                                         j2.value.frequency,
                                                         j2.value.confidence))

    success = output.get_formatted_string_no_id() == success_criteria.get_formatted_string_no_id()

    assert success, "TEST FAILURE: Conditional Conjunctional Abduction test failed: " + output.get_formatted_string_no_id()

def main():
    revision()

    """
        First-Order syllogism tests
    """
    first_order_abduction()
    first_order_analogy()
    first_order_deduction()
    first_order_induction()
    first_order_exemplification()

    """
        Composition
    """
    first_order_extensional_composition()
    first_order_intensional_composition()

    """
        Conditional Syllogism
    """
    conditional_abduction()
    conditional_analogy()
    conditional_deduction()
    conditional_conjunctional_deduction()
    conditional_conjunctional_abduction()

    print("All Inference Rule Tests successfully passed.")

if __name__ == "__main__":
    main()