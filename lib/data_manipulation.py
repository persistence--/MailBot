# Returns True if a string is just numbers and a single dot.
def isfloat(s):
    dots = len(s.split(".")) - 1
    s = s.replace(".", "")
    
    if dots <= 1 and s.isdigit(): return True
    else: return False

# Lowercases all strings in a list.
def lower(l):
    new_list = []
    for item in l:
        new_list.append(str(item).lower())
    return new_list