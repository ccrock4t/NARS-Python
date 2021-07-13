"""
    Author: Christian Hahm
    Created: October 9, 2020
    Purpose: Enforces Narsese grammar that is used throughout the project
"""
import Config
import NALSyntax


class EvidentialValue:
    """
        <frequency, confidence>
    """

    def __init__(self, frequency, confidence):
        assert (isinstance(frequency, float) and frequency >= 0.0 and frequency <= 1.0), "ERROR: Frequency must be a float in [0,1]"
        assert (isinstance(confidence, float) and confidence >= 0.0 and confidence < 1.0), "ERROR: Confidence must be a float [0,1)"
        self.frequency = frequency
        self.confidence = confidence

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

    def __init__(self, frequency, confidence):
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

    def __init__(self, frequency=Config.DEFAULT_JUDGMENT_FREQUENCY, confidence=Config.DEFAULT_JUDGMENT_CONFIDENCE):
        super().__init__(frequency=frequency, confidence=confidence)
        self.formatted_string = str(NALSyntax.StatementSyntax.TruthValMarker.value) \
               + str(self.frequency) \
               + str(NALSyntax.StatementSyntax.TruthValDivider.value) \
               + str(self.confidence) \
               + str(NALSyntax.StatementSyntax.TruthValMarker.value)

    def get_formatted_string(self):
        return self.formatted_string