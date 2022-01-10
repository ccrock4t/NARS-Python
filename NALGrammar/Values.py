"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import Config
import NALSyntax
import NALInferenceRules

class EvidentialValue:
    """
        <frequency, confidence>
    """

    def __init__(self, frequency, confidence):
        if confidence >= 1.0: confidence = 0.9999
        if confidence <= 0.0: confidence = 0.0001
        assert (frequency >= 0.0 and frequency <= 1.0), "ERROR: Frequency " + str(frequency) + " must be in [0,1]"
        assert (confidence >= 0.0 and confidence < 1.0), "ERROR: Confidence must be in (0,1)"
        self.frequency = float(frequency)
        self.confidence = float(confidence)

    def get_formatted_string(self):
        assert False, "Formatted string not defined for Evidential Value base class"

    def __str__(self):
        return self.get_formatted_string()


class DesireValue(EvidentialValue):
    """
        <frequency, confidence>
        For a virtual judgement S |=> D,
        how much the associated statement S implies the overall desired state of NARS, D
    """

    def __init__(self, frequency=Config.DEFAULT_GOAL_FREQUENCY, confidence=None):
        if frequency is None: frequency = Config.DEFAULT_GOAL_FREQUENCY
        if confidence is None: confidence = NALInferenceRules.HelperFunctions.get_unit_evidence()
        if confidence > 0.99: confidence = 0.99999
        super().__init__(frequency=frequency, confidence=confidence)
        self.formatted_string = str(NALSyntax.StatementSyntax.TruthValMarker.value) \
               + "{:.2f}".format(self.frequency) \
               + str(NALSyntax.StatementSyntax.TruthValDivider.value) \
               + "{:.2f}".format(self.confidence) \
               + str(NALSyntax.StatementSyntax.TruthValMarker.value)

    def get_formatted_string(self):
        return self.formatted_string


class TruthValue(EvidentialValue):
    """
        <frequency, confidence>
        Describing the evidential basis for the associated statement to be true
    """

    def __init__(self, frequency=Config.DEFAULT_JUDGMENT_FREQUENCY, confidence=None):
        if frequency is None: frequency = Config.DEFAULT_JUDGMENT_FREQUENCY
        if confidence is None: confidence = NALInferenceRules.HelperFunctions.get_unit_evidence()
        super().__init__(frequency=frequency, confidence=confidence)
        self.formatted_string = str(NALSyntax.StatementSyntax.TruthValMarker.value) \
               + '{0:.2f}'.format(self.frequency) \
               + str(NALSyntax.StatementSyntax.TruthValDivider.value) \
               + '{0:.10f}'.format(self.confidence) \
               + str(NALSyntax.StatementSyntax.TruthValMarker.value) \

    def get_formatted_string(self):
        return self.formatted_string