#!/usr/bin/python2.6

import collections
import random
import os


def remove_html(l):
    in_tag = False
    for c in l:
        if in_tag:
            if c == ">":
                in_tag = False
        else:
            if c == "<":
                in_tag = True
            else:
                yield c


def power_mod(a,n,m):
    if n==0:
        return 1
    elif n==1:
        return a%m
    else:
        (n2,r) = divmod(n,2)
        p = power_mod(a,n2,m)
        if r==0:
            return (p*p)%m
        else:
            return (a*p*p)%m


def rolling_hashes(l,modulus=10**20,base=123456789,windowlength=250):
    """
    Returns hashes of a sliding window of l.
    """

    l = remove_html(iter(l))

    window = collections.deque()
    current = 0
    bigpower = power_mod(base,windowlength,modulus)

    for (i,x) in zip(range(windowlength),l):
        window.append(x)
        current = (base*current + ord(x))%modulus

    yield current

    for x in l:
        window.append(x)
        y = window.popleft()
        current = (base*current + ord(x) - bigpower*ord(y))%modulus
        yield current


def find_likely_matches(ls,number_required=10,modulus=10**20,base=123456789,windowlength=250,save_proportion=0.002):
    """
    Identify the number_required most likely duplicates based on sliding
    window hash collisions.

    Hashes are only stored randomly, so this algorithm is probabilistic.

    It's quite sensible to shuffle the input.
    """
    winners = []
    hashes = {}

    for (i,(name,l)) in enumerate(ls):
        print "%6d. %s"%(i,name)
        clashes = {}
        for h in rolling_hashes(l,modulus=modulus,base=base,windowlength=windowlength):
            # investigate clashes
            if h in hashes:
                for x in hashes[h]:
                    clashes[x] = 1 + clashes.get(x,0)

            # maybe save it
            if random.random() < save_proportion:
                if h not in hashes:
                    hashes[h] = set()
                hashes[h].add(name)

        # report on clashes
        for (x,n) in clashes.iteritems():
            winners.append((n,x,name))

    winners = sorted(winners,reverse=True)
    return winners

            

def randomise_file_list(filenames):
    l = list(filenames)
    random.shuffle(l)
    for f in l:
        yield (os.path.basename(f),open(f,'r').read())


def find_matches_in_files(filenames):
    return find_likely_matches(randomise_file_list(filenames))


def all_html_files(root):
    "all html files in a directory, recursively"
    l = []
    for (path,dirs,files) in os.walk(root):
        for f in files:
            if f[-5:] == ".html":
                fullname = os.path.join(path,f)
                l.append(fullname)
    return l



if __name__=="__main__":
    file_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
    content_dir = os.path.join(file_dir, "../../bailii")
    fs = all_html_files(content_dir)
    print "Obtained %d files. Now shuffling..."%len(fs)
    l = find_matches_in_files(fs)
    print
    print "Top ten:"
    for (n,x,y) in l:
        print "%s --- %s (%d matching windows)"%(x,y,n)
