
def levenshtein(a,b,insertion_cost=1,deletion_cost=1,substitution_cost=1):
    """
    Computes a weighted levenshtein "metric". You can assign penalties to insertion, deletion and substitutions of characters, and it calculates the least possible cost of converting one to the other.

    In case insertion_cost = deletion_cost, it actually is a metric.

    Uses storage O(length of shortest string), time O(product of lengths of strings), and doesn't create garbage mid-execution.
    """
    m = len(a)+1
    n = len(b)+1

    # want the strings one way around to minimise storage
    if m>n:
        (m,n,a,b,insertion_cost,deletion_cost) = (n,m,b,a,deletion_cost,insertion_cost)

    old = [0]*m
    new = list(deletion_cost*i for i in range(m))
    
    for j in range(1,n):
        (old,new) = (new,old)
        new[0] = j*insertion_cost
        for i in range(1,m):
            icost = old[i] + insertion_cost
            dcost = new[i-1] + deletion_cost
            if a[i-1] == b[j-1]:
                scost = old[i-1]
            else:
                scost = old[i-1] + substitution_cost
            new[i] = min(icost,dcost,scost)
    
    return new[m-1]





def test():
    assert 0 == levenshtein("tiger","tiger")
    assert 1 == levenshtein("tiger","tier")
    assert 1 == levenshtein("tiger","tigger")
    assert 1 == levenshtein("tiger","tiler")
    assert 6 == levenshtein("tigger","pooh")
    assert 60 == levenshtein("ergro","underground",insertion_cost=10)
    assert 60 == levenshtein("underground","ergro",deletion_cost=10)

