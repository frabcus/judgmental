"""
Prefix trees
  http://en.wikipedia.org/wiki/Trie

We have a "search" algorithm, which returns all maximal substrings which match. There is also a fast build algorithm, "populate", which requires the input keys to be sorted.
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
        matches = []
        for (k,c) in enumerate(l):
            matches.append((self,k,None))
            newmatches = []
            for (n,i,x) in matches:
                n2 = n.child(c)
                if n2 is None:
                    if x is not None:
                        yield (i,x)
                else:
                    x2 = n.content() or x
                    newmatches.append((n2,i,x2))
            matches = newmatches





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

