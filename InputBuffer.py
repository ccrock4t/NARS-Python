from NALGrammar import *


def add_input(sentence_string, memory):
    sentence = parse_input_sentence_string(sentence_string)
    process_input_sentence(sentence, memory)


# Input syntax:
#   <term copula term>punctuation %f;c%
# Returns:
#   Sentence
def process_input_sentence(sentence, memory):
    print("IN: " + str(sentence))
    memory.add_sentence_to_memory(sentence)

# Input syntax:
#   <term copula term>punctuation %f;c%
# Returns:
#   Sentence
def parse_input_sentence_string(sentence_string):
    # Parse Statement
    start_idx = sentence_string.find(StatementSyntax.Start.value)
    assert(start_idx != -1), "Statement start character " + StatementSyntax.Start.value + " not found. Exiting.."
    end_idx = sentence_string.rfind(StatementSyntax.End.value)
    assert (end_idx != -1), "Statement end character " + StatementSyntax.End.value + " not found. Exiting.."

    punctuation_idx = end_idx + 1
    punctuation_str = sentence_string[punctuation_idx]
    punctuation = Punctuation.get_punctuation(punctuation_str)
    assert (punctuation is not None), punctuation_str + " is not punctuation. Exiting.."

    copula, copulaIdx = get_main_copula_and_index(sentence_string)
    assert (copulaIdx != -1), "Copula not found. Exiting.."

    subject_str = sentence_string[start_idx + 1:copulaIdx].strip()
    predicate_str = sentence_string[copulaIdx + len(copula.value):end_idx].strip()
    subject = Term(subject_str)
    predicate = Term(predicate_str)
    subj_pred = SubjectPredicate(subject, predicate)

    #Parse Truth Value, if it exists
    start_truth_val_idx = sentence_string.find(StatementSyntax.TruthValMarker.value)
    end_truth_val_idx = sentence_string.rfind(StatementSyntax.TruthValMarker.value)

    if start_truth_val_idx == -1 or end_truth_val_idx == -1 or start_truth_val_idx == end_truth_val_idx:
        # default truth value
        truth_value = TruthValue(1.0, 0.9)
    else:
        # parse truth value
        truth_value = TruthValue(1.0, 0.9)

    statement = Statement(subj_pred, copula)
    sentence = Sentence(statement, truth_value, punctuation)
    return sentence


def get_main_copula_and_index(statement_string):
    depth = 0
    for i, v in enumerate(statement_string):
        if v == "(":
            depth = depth + 1
        elif v == ")":
            depth = depth - 1
        elif i + 3 <= len(statement_string) and Copula.is_copula(statement_string[i:i + 3]):
            return Copula.get_copula(statement_string[i:i + 3]), i
    return None, -1