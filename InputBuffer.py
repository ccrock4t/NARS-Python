from NALGrammar import *
import Globals


def add_input(input_string):
    sentence = parse_sentence(input_string)
    process_sentence(sentence)

def process_sentence(sentence):
    print("IN: " + sentence.get_formatted_string())
    Globals.memory.process_judgment(sentence)

def parse_sentence(sentence_string):
    """
    Parameter: sentence_string - String of NAL syntax <term copula term>punctuation %f;c%

    Returns: Sentence parsed from sentence_string
    """
    start_idx = sentence_string.find(StatementSyntax.Start.value)
    assert(start_idx != -1), "Statement start character " + StatementSyntax.Start.value + " not found. Exiting.."
    end_idx = sentence_string.rfind(StatementSyntax.End.value)
    assert (end_idx != -1), "Statement end character " + StatementSyntax.End.value + " not found. Exiting.."

    punctuation_idx = end_idx + 1
    punctuation_str = sentence_string[punctuation_idx]
    punctuation = Punctuation.get_punctuation(punctuation_str)
    assert (punctuation is not None), punctuation_str + " is not punctuation. Exiting.."

    copula, copulaIdx = parse_copula_and_index(sentence_string)
    assert (copulaIdx != -1), "Copula not found. Exiting.."

    subject_str = sentence_string[start_idx + 1:copulaIdx].strip()
    predicate_str = sentence_string[copulaIdx + len(copula.value):end_idx].strip()
    subject = Term(subject_str)
    predicate = Term(predicate_str)
    subj_pred = SubjectPredicate(subject, predicate)

    #Parse Truth Value, if it exists
    start_truth_val_idx = sentence_string.find(StatementSyntax.TruthValMarker.value)
    middle_truth_val_idx = sentence_string.find(StatementSyntax.TruthValDivider.value)
    end_truth_val_idx = sentence_string.rfind(StatementSyntax.TruthValMarker.value)

    if start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx:
        # No truth value, use default truth value
        truth_value = TruthValue(1.0, 0.9)
    else:
        # Parse truth value from string
        freq = sentence_string[start_truth_val_idx+1:middle_truth_val_idx]
        conf = sentence_string[middle_truth_val_idx+1:end_truth_val_idx]
        truth_value = TruthValue(freq, conf)

    statement = Statement(subj_pred, copula)
    sentence = Sentence(statement, truth_value, punctuation)

    return sentence


def parse_copula_and_index(statement_string):
    """
    Parameter: statement_string - String of NAL syntax <term copula term>

    Returns: copula, copula index
    """
    depth = 0
    for i, v in enumerate(statement_string):
        if v == "(":
            depth = depth + 1
        elif v == ")":
            depth = depth - 1
        elif i + 3 <= len(statement_string) and Copula.is_copula(statement_string[i:i + 3]):
            return Copula.get_copula(statement_string[i:i + 3]), i

    return None, -1