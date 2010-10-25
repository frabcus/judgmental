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



class SubmassageRule(Rule):
    "This is the rule which applies rules to subtags. Mostly for internal use"

    def __init__(self,parent,rules):
        self.parent = parent
        self.rules = rules

    def transform(self,element):
        done_something = None
        for c in element.getchildren():
            d = self.parent.inner_massage(c,self.rules)
            if d is not None:
                element.replace(c,d)
                done_something = element
        return done_something



class Massager():

    def rules():
        """
        The list of rules to be applied. They will be applied in the order
        given.
        """
        pass

    def preprocess(self,inf,outf):
        "Default preprocessor routine"
        for l in inf:
            outf.write(l)

    def massage(self,element):
        """
        Recursively applies all the rules in turn. Returns the element, for
        ease of chaining.
        """

        our_rules = self.rules()
        our_rules.append(SubmassageRule(self,our_rules))

        x = self.inner_massage(element,our_rules)
        if x is None:
            return element
        else:
            return x

    def inner_massage(self, element, our_rules):
        "Only returns the new element if it's changed, otherwise None"
            
        def already_massaged(element):
            try:
                return element.has_been_massaged
            except AttributeError:
                return False

        if already_massaged(element):
            return None

        done_anything = False
        stabilized = False

        while not stabilized:
            stabilized = True
        
            for r in our_rules:

                a = r.transform(element)

                if a is not None:
                    element = a
                    stabilized = False
                    done_anything = True
                    break

        element.has_been_massaged = True

        if done_anything:
            return element
        else:
            return None

    def restructure(self,element):
        pass
