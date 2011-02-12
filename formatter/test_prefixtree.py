from prefixtree import *


def handle(n,s):
    return "{%s:%s}"%(n,s)

p = PrefixTree().populate([("badger","grrrr"),("cat","miaow"),("dog","woof"),("dogfish","woof&glug"),("fish","glug")])

print unenumerate(p.search_and_replace(limply_normalise,handle,"Dog, dogfish, badger, badgerfish, cat, catfish, and that'll do"))



print



print unenumerate(remove_html('<p>This is a paragraph containing a <a href="link.html">link</a> and some <strong>strongly worded</strong> parts, but I hope &amp; pray that the formatting won\'t survive, except for some &lt;relics&gt;.</p>'))



print



def taggify(n,_):
    return "<em>%s</em>"%n

p = PrefixTree().populate(sorted([("Flopsy",True),("Mopsy",True),("Cotton-tail",True),("Peter",True)]))

s = """<p>Once upon a time there were four little Rabbits, &amp; their names were &mdash;</p>
<ol>
  <li>Flopsy,</li>
  <li>Mopsy,</li>
  <li>Cotton-tail, and</li>
  <li>Peter.</li>
</ol>"""

print unenumerate(p.search_and_replace(remove_html,taggify,s))
