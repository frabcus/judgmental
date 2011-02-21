"""
Prefix trees
  http://en.wikipedia.org/wiki/Trie

Functionality is split between PrefixMaster and PrefixTree.

There are two concepts we have invented to make the code general.

1. A "charstream" is an iter of pairs (c,n) where c is a character, and n is an integer. This is supposed to represent characters of a patched string together with their positions in the original.
   Of course, a charstream can be produced from a string using enumerate.

2. A "normalising function" takes an iter of chars and returns a charstream.
"""


from itertools import tee, islice


def compose_normalisers(g,f):
    "Composes two normalising functions"
    return (lambda l: composed_normalisers(g,f,l))


def composed_normalisers(g,f,l):
    "Composes two normalising functions and applies them to l. The problem, of course, is in renumbering"
    (fl,fl2) = tee(f(l))
    gfl = g(x for (i,x) in fl2)
    c = -1
    for (j,y) in gfl:
        for z in range(j-c):
            (i,x) = fl.next()
        c = j
        yield (i,y)


def unenumerate(l):
    "Recover a string from an enumeration"
    return "".join(c for (n,c) in l)


def limply_normalise(l):
    "Set all non-alphanumerics to a single space, set everything to lowercase."
    excited = True
    for (n,c) in enumerate(l):
        if excited and not c.isalnum():
            excited = False
            yield (n,' ')
        elif c.isalnum():
            excited = True
            yield (n,c.lower())
            

def violently_normalise(l):
    "Strip out all non-alphanumerics, set everything to lowercase."
    for (n,c) in enumerate(l):
        if c.isalnum():
            yield (n,c.lower())



def remove_excess_spaces(l):
    "Replace multiple spaces with a single space"
    hadspace = False
    for (n,c) in enumerate(l):
        if c.isspace():
            if not hadspace:
                hadspace = True
                yield (n,c)
        else:
            hadspace = False
            yield (n,c)
                



def remove_html(l):
    "Strip out tags; replace &amp; and &lt; and &gt;"

    def untag(l):
        outside = True
        for (n,c) in enumerate(l):
            if outside:
                if c == "<":
                    outside = False
                else:
                    yield (n,c)
            else:
                if c == ">":
                    outside = True

    p = PrefixTree().populate(sorted([("&amp;","&"),("&lt;","<"),("&gt;",">"),("&nbsp;"," ")]))

    def unentity(l):
        return p.search_and_replace(enumerate, lambda x,y:y, l)

    return composed_normalisers(unentity, untag, l)




class PrefixMaster:
    "Base class for prefix trees"

    def __iter__(self):
        return self.prefixiter("")

    def sortediter(self):
        return self.sortedprefixiter("")

    def __getitem__(self,k):
        t = self
        for c in k:
            t = t.child(c)
            if t is None:
                raise IndexError("No such key")
        x = t.content()
        if x is None:
            raise IndexError("No such key")
        return x

    def search_string(self,s):
        """
        Searches through a string, and yields all maximal matches.
        Yields pairs consisting of the start position and the key.
        """
        return self.search(enumerate,s)

    def search(self,p,l):
        """
        Searches through a string, normalised by p, and yields all
        maximal matches. Yields pairs consisting of the start position
        and the key.
        """
        matches = []
        for (k,c) in p(l):
            matches.append((self,k,None))
            newmatches = []
            for (n,i,x) in matches:
                n2 = n.child(c)
                x2 = n.content() or x
                if n2 is None:
                    if x2 is not None:
                        yield (i,x2)
                else:
                    newmatches.append((n2,i,x2))
            matches = newmatches

    def search_and_replace(self,p,f,l):
        """
        Yields successive characters of the input string, normalised by
        normalising function p, with matches replaced by f of the matching
        input and the key.

        As we go along, we maintain:
         - the number of input characters we've processed
         - a set of possible matches, which are tuples consisting of:
            - current prefixtree node (or None, if no further match is possible)
            - start index in input string
            - last match end index in input string (None, if no match made yet)
            - last match value (None, if no match made yet)
        """

        (inchars1,inchars2) = tee(iter(l))
        inchars = enumerate(inchars1)
        normalised = p(inchars2)
        
        count = 0
        states = []

        def advance_states(c,k,states):
            newstates = []
            for (node,start,lastend,lastval) in states:
                node2 = node.child(c)
                end2 = (node.content() and k) or lastend
                val2 = node.content() or lastval
                if node2 or val2:
                    newstates.append((node2,start,end2,val2))
            return newstates

        def finalise_states(k,states):
            newstates = []
            for (node,start,lastend,lastval) in states:
                end2 = (node.content() and k) or lastend
                val2 = node.content() or lastval
                if val2:
                    newstates.append((node,start,end2,val2))
            return newstates

        k = -1
        for (k,c) in normalised:
            states.append((self,k,None,None))
            states = advance_states(c,k,states)

            # process matches
            while len(states)>0 and states[0][0] is None and states[0][2] is not None:
                # release a replacement
                (node,start,end,val) = states[0]
                for x in f(unenumerate(islice(inchars,end-start)),val):
                    yield (start,x)
                count = end
                states = states[1:]

                # cancel work on matches which clash
                while len(states)>0 and states[0][1]<end:
                    states = states[1:]

            # release unmatchable data as unchanged
            if len(states)>0:
                newcount = states[0][1]
            else:
                newcount = k
            if newcount>count:
                for (k2,c2) in islice(inchars,newcount-count):
                    yield (k2,c2)
                count=newcount

        # deal with what's left over
        states = finalise_states(k+1,states)

        while len(states)>0:
            # release replacement
            (node,start,end,val) = states[0]
            for x in f(unenumerate(islice(inchars,start-count,end-count)),val):
                yield (start,x)
            count = end
            states = states[1:]

            # cancel clashes
            while len(states)>0 and states[0][1]<end:
                states = states[1:]

            # release free text
            if len(states)>0:
                newcount = states[0][1]
                if newcount>count:
                    for (k2,c2) in islice(inchars,newcount-count):
                        yield (k2,c2)
                    count=newcount

        # release all remaining text
        for (k2,c2) in inchars:
            yield (k2,c2)




class PrefixTree(PrefixMaster):
    "The standard prefix tree; the only one that should be created by the user."

    def __init__(self, contains=None, children=None):
        self.contains = contains
        if children:
            self.children = children
        else:
            self.children = {}

    def __len__(self):
        a = sum(len(v) for v in self.children.itervalues())
        if self.contains is not None:
            return a+1
        else:
            return a

    def prefixiter(self,p):
        if self.contains is not None:
            yield (p,self.contains)
        for (k,v) in self.children.iteritems():
            for (a,x) in v.prefixiter(p+k):
                yield (a,x)

    def sortedprefixiter(self,p):
        if self.contains is not None:
            yield (p,self.contains)
        for k in sorted(self.children.iterkeys()):
            for (a,x) in self.children[k].prefixiter(p+k):
                yield (a,x)

    def child(self,c):
        if c in self.children:
            return self.children[c]
        else:
            return None

    def content(self):
        return self.contains

    def populate(self,l):
        """
        Takes a sorted list of key/value pairs and fills the prefix tree.
        """

        def agreement(depth,i,j,c):
            for k in range(i+1,j):
                if l[k][0][depth] != c:
                    return k
            return j

        def subtree_contents(depth,i,j):
            if len(l[i][0])==depth:
                val = l[i][1]
                i = i+1
            else:
                val = None
            d = {}
            while i<j:
                c = l[i][0][depth]
                k = agreement(depth,i,j,c)
                d[c] = make_subtree(depth+1,i,k)
                i = k
            return (val,d)

        def make_subtree(depth,i,j):
            (val,d) = subtree_contents(depth,i,j)
            if val is None and len(d)==1:
                (c,v) = d.popitem()
                return PrefixStalk(c,v)
            else:
                return PrefixTree(val,d)

        (val,d)=subtree_contents(0,0,len(l))
        self.contains = val
        self.children = d
        return self
        
        
            



class PrefixStalk(PrefixMaster):
    """
    A prefix tree with only one descendant. assumed not to contain at the root.
    Not actually necessary, but an optimising touch.
    This cannot be the root of the tree.
    """

    def __init__(self, char, child):
        self.char = char
        self.sprog = child

    def __len__(self):
        return len(self.sprog)

    def prefixiter(self,p):
        return self.sprog.prefixiter(p+self.char)

    def sortedprefixiter(self,p):
        return self.sprog.sortedprefixiter(p+self.char)

    def child(self,c):
        if c == self.char:
            return self.sprog
        else:
            return None

    def content(self):
        return None

