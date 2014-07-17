import landmaker.footprintcore as fc
import unittest as ut

class TestPadPrimitives(ut.TestCase):
    def setUp(self):
        self.p1 = fc.Pad(fc.Dim.MIL(10),fc.Dim.MIL(8))
        self.p2 = fc.Pad(fc.Dim.MM(.1),fc.Dim.MM(.1))

    def test_00constructors(self):
        self.assertTrue(self.p1.clearance == fc.Dim.MIL(10))
        self.assertTrue(self.p1.maskRelief == fc.Dim.MIL(8))

    def test_01repr(self):
        self.assertEqual(repr(self.p1),"Pad(Dim(0.254,'mil'),Dim(0.2032,'mil'))")

    def test_02eq(self):
        p = fc.Pad(fc.Dim.MM(.1), fc.Dim.MM(.1))
        self.assertTrue(self.p2 == p)
        self.assertTrue(self.p1 != self.p2)
    
if __name__ == '__main__':
    ut.main()
