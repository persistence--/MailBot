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

# Reads a file into a list, stripping \r's and \n's along the way.
def file2list(filename):
    f = open(filename, 'r')
    l = f.readlines()

    for n in range(len(l)):
        l[n] = l[n].rstrip()

    return l

# Store a list as a file with one item per line.
def list2file(my_list, filename):
    try:
        f = open(filename, 'w')
        for item in my_list:
            f.write("%s\n" % item)
        f.close()

        return True
    except:
        return False