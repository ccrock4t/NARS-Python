# ==== ==== ==== ==== ==== ====
# ==== NAL Inference Rules ====
# ==== ==== ==== ==== ==== ====

# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Local inference) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Revision Rule
# j1 and j2 must have distinct evidential bases B1 and B2
# Inputs:
#   j1: Statement <f1,c1>
#   j2: Statement <f2,c2>
def nal_revision(j1, j2):
    return 0

# Choice Rule
# Inputs:
#   j1:
#   j2:
# Returns:
def nal_choice(j1, j2):
    return 0

# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Strong syllogism) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Deduction (Strong syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: S --> M <f2, c2>
#   :- S --> P
# Truth Val:
#   f: and(f1,f2)
#   c: and(f1,f2,c1,c2)
def nal_deduction(j1, j2):
    return 0

# Analogy (Strong syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: S <-> M <f2, c2>
#   :- S --> P
# Truth Val:
#   f: and(f1,f2)
#   c: and(f2,c1,c2)
def nal_analogy(j1, j2):
    return 0

# Resemblance (Strong syllogism)
# Inputs:
#   j1: M <-> P <f1, c1>
#   j2: S <-> M <f2, c2>
#   :- S <-> P
# Truth Val:
#   f: and(f1,f2)
#   c: and(or(f1,f2),c1,c2)
def nal_resemblance(j1, j2):
    return 0

# ++++ ++++ ++++ ++++ ++++ ++++
# ++++ (Weak syllogism) ++++
# ++++ ++++ ++++ ++++ ++++ ++++

# Abduction
# Inputs:
#   j1: P --> M <f1, c1>
#   j2: S --> M <f2, c2>
#   :- S --> P
# Truth Val:
#   w+: and(f1,f2,c1,c2)
#   w-: and(f1,c1,not(f2),c2)
#   w: and(f1,c1,c2)
def nal_abduction(j1, j2):
    return 0

# Induction (Weak syllogism)
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S --> P
# Truth Val:
#   w+: and(f1,f2,c1,c2)
#   w-: and(f2,c2,not(f1),c1)
#   w: and(f2,c1,c2)
def nal_induction(j1, j2):
    return 0

# Exemplification
# Inputs:
#   j1: P --> M <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S --> P
# Truth Val:
#   w+: and(f1,c1,f2,c2)
#   w-: 0
#   w: w+
def nal_exemplification(j1, j2):
    return 0

# Comparison
# Inputs:
#   j1: M --> P <f1, c1>
#   j2: M --> S <f2, c2>
#   :- S <-> P
# Truth Val:
#   w+: and(f1,c1,f2,c2)
#   w: and(or(f1,f2),c1,c2)
def nal_exemplification(j1, j2):
    return 0






