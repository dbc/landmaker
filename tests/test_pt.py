import plugins.footprintcore as fc
import unittest as ut

class TestPt(ut.TestCase):
    def setUp(self):
        self.p1 = fc.Pt(fc.Dim.MM(1), fc.Dim.MM(1))
        self.p2 = fc.Pt.MM(2,3)
        self.p3 = fc.Pt.MIL(245,490)
        self.p4 = fc.Pt.INCH(1,2)
        self.p5 = fc.Pt.MM(25.4, 50.8)
        self.p6 = fc.Pt((fc.Dim.MIL(100),fc.Dim.MIL(200)))
        self.p7 = fc.Pt(fc.Dim.MM(3), fc.Dim.MM(3))
        # Need some negative operands!!

    def test_00constructors(self):
        pass

    def test_01oper_le(self):
        self.assertTrue (self.p1 <= self.p2)
        self.assertFalse (self.p2 <= self.p1)
        self.assertTrue (self.p4 <= self.p5)
        self.assertTrue (self.p5 <= self.p4)

    def test_02order(self):
        v = self.p2.order(self.p1)
        self.assertTrue(v[0] is self.p1)
        self.assertTrue(v[1] is self.p2)

    def test_03add(self):
        v = self.p1 + self.p2
        self.assertTrue(v.x == fc.Dim.MM(3))
        self.assertTrue(v.y == fc.Dim.MM(4))

    def test_04sub(self):
        pass

    def test_05halfplanecomp(self):
        self.assertTrue(self.p1.leftOf(self.p2))
        self.assertTrue(self.p2.rightOf(self.p1))
        self.assertTrue(self.p3.below(self.p4))
        self.assertTrue(self.p5.above(self.p3))

    def test_06area(self):
        self.assertTrue(self.p2.area(fc.Pt.MM(0,0)) == 6.0)

    def test_07eq(self):
        self.assertTrue(self.p4 == self.p5)
        
    def test_08reflections(self):
        self.assertTrue(self.p1.reflx == fc.Pt.MM(1,-1))
        self.assertTrue(self.p1.refly == fc.Pt.MM(-1,1))
        self.assertTrue(-self.p1 == fc.Pt.MM(-1,-1))

    def test_09ne(self):
        self.assertTrue(self.p1 != self.p2)

    def test_10pos(self):
        self.assertTrue(+self.p1 == self.p1)

    def test_11align(self):
        self.assertTrue(self.p4.alignedx(self.p5))
        self.assertTrue(self.p4.alignedy(self.p5))

    def test_12lt(self):
        self.assertTrue(self.p1 < self.p2)

    def test_13gt(self):
        self.assertTrue(self.p2 > self.p1)

    def test_14ge(self):
        self.assertTrue(self.p2 >= self.p1)
        self.assertTrue(self.p4 >= self.p5)

    def test_15mul(self):
        p = self.p1 * 3
        self.assertTrue(p == fc.Pt.MM(3,3))
        p = 3 * self.p1
        self.assertTrue(p == self.p7)

    def test_16mul(self):
        p = self.p7/3
        self.assertTrue(p == self.p1)

    def test_17dist(self):
        d = self.p1.dist(self.p7)
        self.assertTrue(d >= fc.Dim.MM(2*1.41))
        self.assertTrue(d <= fc.Dim.MM(2*1.42))

    def test_18spansOrg(self):
        self.assertFalse(self.p1.spansOrg(self.p2))
        self.assertTrue((-self.p1).spansOrg(self.p2))


if __name__ == '__main__':
    ut.main()
