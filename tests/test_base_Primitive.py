import landmaker.footprintcore as fc
import unittest as ut

class TestPrimitive(ut.TestCase):
    def setUp(self):
        self.p1 = fc.Primitive(fc.Pt.MM(1,1))

    def test_00prim_constructors(self):
        self.assertEqual(self.p1.loc.x,1)
        self.assertEqual(self.p1.loc.y,1)

    def test_01prim_repr(self):
        self.assertTrue(repr(self.p1)=="Primitive(Pt(Dim(1.0,'mm'),Dim(1.0,'mm')))")

if __name__ == '__main__':
    ut.main()
