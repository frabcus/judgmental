from lxml import html
from cStringIO import StringIO



class Rule():
    "A recursive tree manipulation"

    def transform(self,element):
        "Manipulates the element, returns whether a change has been made"
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

    def submassage(self,element):
        for c in element.getchildren():
            self.massage(c)

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
        
        if already_massaged(element):
            return element

        self.submassage(element)

        stabilized = False

        while not stabilized:
            stabilized = True
        
            for r in self.rules():

                # NB this test is done for side effect
                if r.transform(element):
                    stabilized = False
                    self.submassage(element)
                    break

        self.has_been_massaged = True

        return element

    def restructure(self,element):
        pass
