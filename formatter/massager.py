from lxml import html


class Rule():
    "A rule for doing a tree manipulation"

    def transform(self,element):
        "Manipulates the element, returns whether a change has been made"
        return False


def already_massaged(element):
    try:
        return element.has_been_massaged
    except AttributeError:
        return False


class Massager():

    def rules():
        """
        The list of rules to be applied. They will be applied in the order
        given.
        """
        pass

    def massage_page(self,location):
        "takes page at 'location', massages, and returns element tree."
        page = html.parse(location)
        self.massage(page.getroot())
        self.post_process(page.getroot())
        return page

    def massage_page_to_file(self,inlocation,outlocation):
        "Takes page at 'inlocation', massages, saves to 'outlocation'."
        page = html.parse(inlocation)
        self.massage(page.getroot())
        self.post_process(page.getroot())
        s = html.tostring(page, pretty_print = True)
        outlocation.write(s)

    def post_process(self,element):
        pass

    def submassage(self,element):
        for c in element.getchildren():
            self.massage(c)

    def massage(self,element):
        """
        Recursively applies all the rules in turn.
        """
        
        if already_massaged(element):
            return False

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


