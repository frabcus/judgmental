class PrefixTree():

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

    def __iter__(self):
        return self.prefixiter("")

    def sortediter(self):
        return self.sortedprefixiter("")

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

    def search(self,s,unambiguous=False):
        """
        Find all occurrences of words in self in string s, together with the
        start position of their occurrence.
        If unambiguous=True, only returns unambiguous matches.
        """
        if unambiguous:
            partials = []
            for (i,c) in enumerate(s):
                partials.append(("",i,self,None,None))
                newpartials = []
                for (p,k,m,b,v) in partials:
                    if c in m.children:
                        mc = m.children[c]
                        if mc.contains is not None:
                            newpartials.append((p+c,k,m.children[c],p+c,mc.contains))
                        else:
                            newpartials.append((p+c,k,m.children[c],b,v))
                    else:
                        if b:
                            yield (b,k,v)
                partials = newpartials
                            
        else:
            partials = []
            for (i,c) in enumerate(s):
                partials.append(("",i,self))
                partials = [(p+c,k,m.children[c]) for (p,k,m) in partials if c in m.children]
                for (p,k,m) in partials:
                    if m.contains is not None:
                        yield (p,k,m.contains)

    def populate(self,l):
        """
        Takes a sorted list of input strings, fills the prefix tree.
        """

        assert len(self)==0, "Prefix tree must be empty."
        i = iter(l)

        def agreement(w1,w2):
            "How far do these two strings agree?"
            n = min([len(w1),len(w2)])
            for i in range(n):
                if w1[i] != w2[i]:
                    return i
            return n

        def add(tree,item,val,depth,length):
            "Well, Python doesn't have fast builtin linked lists. But it does have one builtin linked list: the call stack. :-)"
            if length == depth:
                tree.contains = val
                (nitem,nval) = i.next()
                agree = agreement(item,nitem)
                item = nitem
                val = nval
            else:
                newtree = PrefixTree()
                tree.children[item[depth]] = newtree
                (item,val,agree) = add(newtree,item,val,depth+1,length)
            while True:
                if agree < depth:
                    return (item,val,agree)
                newtree = PrefixTree()
                tree.children[item[depth]] = newtree
                (item,val,agree) = add(newtree,item,val,depth+1,len(item))

        (x,v) = i.next()
        try:
            add(self,x,v,0,len(x))
        except StopIteration:
            pass

