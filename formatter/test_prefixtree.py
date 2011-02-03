from prefixtree import *


def normalise(c):
    return c.lower()

def handle(n,s):
    return "{%s:%s}"%(n,s)

p = PrefixTree().populate([("badger","grrrr"),("cat","miaow"),("dog","woof"),("dogfish","woof&glug"),("fish","glug")])

s = "".join(p.search_and_replace(normalise,handle,"Dog, dogfish, badger, badgerfish, cat, catfish, another dog"))

print s
