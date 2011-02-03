"""
Prefix trees
  http://en.wikipedia.org/wiki/Trie

Functionality is split between PrefixMaster and PrefixTree.
"""


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

    def search(self,l):
        """
        Searches through a string, and yields all maximal matches.
        Yields pairs consisting of the start position and the key.
        """
        return normalising_search(lambda x:x,l)

    def normalising_search(self,p,l):
        """
        Calls p on every character; p returns a string (well,
        maybe just an iterable of characters). It is this string
        that is used for the prefix tree. Otherwise like search.
        """
        matches = []
        for (k,c1) in enumerate(l):
            for c in p(c1):
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
        Yields successive characters of the input, appropriately normalised,
        with matches replaced by f of the matching input and the key.

        As we go through, we maintain:
         - a list of input characters we're not sure about
         - the start position in that document of those characters
         - a set of possible matches, which are tuples consisting of:
            - current prefixtree node (or None, if no further match is possible)
            - start index in input string
            - last match end index in input string (None, if no match made yet)
            - last match value (None, if no match made yet)
        """
        unprocessed = []
        shift = 0
        matches = []

        def advance_match_states(c,k,l):
            newl = []
            for (node,start,lastend,lastval) in matches:
                node2 = node.child(c)
                end2 = (node.content() and k) or lastend
                val2 = node.content() or lastval
                if node2 or val2:
                    newl.append((node2,start,end2,val2))
            return newl

        def finalise_match_states(k,l):
            newl = []
            for (node,start,lastend,lastval) in matches:
                end2 = (node.content() and k) or lastend
                val2 = node.content() or lastval
                if val2:
                    newl.append((node,start,end2,val2))
            return newl

        for (k,c1) in enumerate(l):
            unprocessed.append(c1)
            for c in p(c1):
                matches.append((self,k,None,None))
                matches = advance_match_states(c,k,matches)

                # process matches
                while len(matches)>0 and matches[0][0] is None and matches[0][2] is not None:
                    # release replacement
                    (node,start,end,val) = matches[0]
                    matchstr = "".join(unprocessed[(start-shift):(end-shift)])
                    for x in f(matchstr,val):
                        yield x
                    matches = matches[1:]

                    # cancel work on matches which clash
                    while len(matches)>0 and matches[0][1]<end:
                        matches = matches[1:]

                    # flush matched text
                    unprocessed = unprocessed[(end-shift):]
                    shift = end

            # release unmatchable data as unchanged
            if len(matches)>0:
                newshift=matches[0][1]
            else:
                newshift=k
            if newshift>shift:
                for x in unprocessed[:(newshift-shift)]:
                    yield x
                unprocessed = unprocessed[(newshift-shift):]
                shift=newshift

        # deal with what's left: go through remaining matches
        matches = finalise_match_states(k+1,matches)

        while len(matches)>0:
            # release replacement
            (node,start,end,val) = matches[0]
            matchstr = "".join(unprocessed[(start-shift):(end-shift)])
            for x in f(matchstr,val):
                yield x
            matches = matches[1:]

            # cancel work on matches which clash
            while len(matches)>0 and matches[0][1]<end:
                matches = matches[1:]

            # flush matched text
            unprocessed = unprocessed[(end-shift):]
            shift = end

        # release unmatchable data as unchanged
        for x in unprocessed:
            yield x




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

