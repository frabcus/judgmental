from lxml import html
from cStringIO import StringIO



class Rule():
    "A recursive tree manipulation"

    def transform(self,element):
        """
        Manipulates the element, a new element or None (if element is to be
        unchanged.
        """
        return False



class Massager():

    def rules():
        """
        The list of rules to be applied. They will be applied in the order
        given.
        """
        pass

    def read_and_restructure(self,inlocation,outlocation):
        infile = open(inlocation,'r')
        midfile = StringIO()
        self.preprocess(infile,midfile)
        midfile.seek(0)
        page = html.parse(midfile)
        page = self.restructure(page)
        s = html.tostring(page, pretty_print = True)
        outfile = open(outlocation,'w')
        outfile.write(s)

    def preprocess(self,inf,outf):
        "Default preprocessor routine"
        for l in inf:
            outf.write(l)

    def massage(self,element):
        """
        Recursively applies all the rules in turn. Returns the element, for
        ease of chaining.
        """

        def already_massaged(element):
            try:
                return element.has_been_massaged
            except AttributeError:
                return False

        def submassage(element):
            for c in element.getchildren():
                d = inner_massage(c)
                if d is not None:
                    element.replace(c,d)

        def inner_massage(element):
            "Only returns the new element if it's changed, otherwise None"
            
            if already_massaged(element):
                return None

            submassage(element)

            stabilized = False

            while not stabilized:
                stabilized = True
        
                for r in self.rules():

                    a = r.transform(element)

                    if a is not None:
                        element = a
                        stabilized = False
                        submassage(element)
                        break

            element.has_been_massaged = True

            return element

        x = inner_massage(element)
        if x is None:
            return element
        else:
            return x

    def restructure(self,element):
        pass
