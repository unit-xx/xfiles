class A:
    def __init__(self):
        self.a=1

class B(A):
    def __init__(self):
        A()
class C:
    def c1(self):
        print "c1"

    def c2(self):
        print "c2"

    cc = c1

c = C()
c.cc()
