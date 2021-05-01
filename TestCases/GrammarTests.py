import NARSDataStructures
import NALGrammar
import NALSyntax
import NARS
import NARSMemory

"""
    Author: Christian Hahm
    Created: March 11, 2021
    Purpose: Unit Testing for NARS grammar
"""

def calculate_syntactic_complexity_test():
    atomic_term = NALGrammar.Term.from_string("A")
    atomic_term_complexity = 1

    singleton_set_compound_term = NALGrammar.Term.from_string("[A]")
    singleton_set_compound_term_complexity = 2

    extensional_set_compound_term = NALGrammar.Term.from_string("{A,B}")
    # becomes an intensional intersection of sets, (|,{A},{B})
    extensional_set_compound_term_complexity = 5

    singleton_set_internal_compound_term = NALGrammar.Term.from_string("[(*,A,B)]")
    singleton_set_internal_compound_term_complexity = 4

    statement_term = NALGrammar.Term.from_string("(A-->B)")
    statement_term_complexity = 3

    assert atomic_term._calculate_syntactic_complexity() == atomic_term_complexity
    assert singleton_set_compound_term._calculate_syntactic_complexity() == singleton_set_compound_term_complexity
    assert extensional_set_compound_term._calculate_syntactic_complexity() == extensional_set_compound_term_complexity
    assert singleton_set_internal_compound_term._calculate_syntactic_complexity() == singleton_set_internal_compound_term_complexity
    assert statement_term._calculate_syntactic_complexity() == statement_term_complexity

def main():
    """
        Term Tests
    """
    calculate_syntactic_complexity_test()

    print("All Grammar Tests successfully passed.")

if __name__ == "__main__":
    main()