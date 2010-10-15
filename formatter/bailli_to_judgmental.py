from massager import *
from lxml.etree import Element


class EmptyParagraphsToBreaks(Rule):
    "<p /> --> <br />"
    
    def transform(self,element):
        done_something = False
        for e in element.findall("p"):
            if e.getchildren() == [] and (e.text or "").strip() == "":
                element.replace(e, Element("br"))
                done_something = True
        return done_something



class EntityThirteenSucks(Rule):
    "kill &#13;"

    def transform(self,element):
        
        done_something = False
        if (element.text is not None) and "\n\r" in element.text:
            element.text = element.text.replace("\n\r","\n")
            done_something = True
        if (element.tail is not None) and "\n\r" in element.tail:
            element.tail = element.tail.replace("\n\r","\n")
            done_something = True
        if done_something:
            print "Removing entity 13"
        return done_something
        



class BtoJ(Massager):

    def rules(self):
        l = [EmptyParagraphsToBreaks()]
        
        return l
        
                
