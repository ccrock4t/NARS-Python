"""
==== ==== ==== ==== ==== ====
==== NAL Inference Rules - Extended Boolean Operators ====
==== ==== ==== ==== ==== ====

    Author: Christian Hahm
    Created: October 8, 2020
    Purpose: Defines the NAL inference rules
            Assumes the given sentences do not have evidential overlap.
            Does combine evidential bases in the Resultant Sentence.
"""

def band(*argv):
    """
        Boolean AND

        -----------------

        Input:
            argv: NAL Boolean Values

        Returns:
            argv1*argv2*...*argvn
    """
    res = 1
    for arg in argv:
        res = res * arg
    return res

def band_average(*argv):
    """
        Boolean AND, with an exponent inversely proportional to the number of terms being ANDed.

        -----------------

        Input:
            argv: NAL Boolean Values

        Returns:
            (argv1*argv2*...*argvn)^(1/n)
    """
    res = 1
    for arg in argv:
        res = res * arg
    exp = 1 / len(argv)
    return res ** exp



def bor(*argv):
    """
        Boolean OR

        -----------------

        Input:
            argv: NAL Boolean Values

        Returns:
             1-((1-argv1)*(1-argv2)*...*(1-argvn))
    """
    res = 1
    for arg in argv:
        res = res * (1 - arg)
    return 1 - res


def bnot(arg):
    """
        Boolean Not

        -----------------

        Input:
            arg: NAL Boolean Value

        Returns:
            1 minus arg
    """
    return 1 - arg
