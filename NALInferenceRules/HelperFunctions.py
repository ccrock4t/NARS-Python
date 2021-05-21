import Config


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


def getevidentialvalues_from2sentences(j1, j2):
    """
        Input:
            j1: Sentence <f1, c1>

            j2: Sentence <f2, c2>
        Returns:
            f1, c1, f2, c2
    """
    return getevidentialvalues_fromsentence(j1), getevidentialvalues_fromsentence(j2)


def getevidentialvalues_fromsentence(j):
    """
        Input:
            j: Sentence <f, c>
        Returns:
            f, c
    """
    return j.value.frequency, j.value.confidence


def getevidence_from2sentences(j1, j2):
    """
        Input:
            j1: Sentence <f1, c1>

            j2: Sentence <f2, c2>
        Returns:
            w1+, w1, w1-, w2+, w2, w2-
    """
    (f1, c1), (f2, c2) = getevidentialvalues_from2sentences(j1, j2)
    return get_evidence_fromfreqconf(f1, c1), get_evidence_fromfreqconf(f2, c2)
