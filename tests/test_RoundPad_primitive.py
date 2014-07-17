import landmaker.footprintcore as fc
import unittest as ut

class TestRoundPadPrimitives(ut.TestCase):
    def setUp(self):
        self.p1 = fc.RoundPad('55mil','8mil','4mil')
        self.p2 = fc.RoundPad('12mm','5 mm','2mm')

    def test_00constructors(self):
        self.assertEqual(self.p1.dia,fc.Dim.MIL(55))
        self.assertEqual(self.p1.clearance,fc.Dim.MIL(8))
        self.assertEqual(self.p1.maskRelief,fc.Dim.MIL(4))

    def test_01repr(self):
        self.assertEqual(repr(self.p1),"RoundPad(Dim(1.397,'mil'),Dim(0.2032,'mil'),Dim(0.1016,'mil'))")

    def test_02eq(self):
        self.assertTrue(self.p1 == fc.RoundPad(fc.Dim.MIL(55),fc.Dim.MIL(8),fc.Dim.MIL(4)))
        self.assertFalse(self.p1 == fc.RoundPad('45mil','10mil','5 mil'))

    def test_03extents(self):
        self.assertEqual(self.p2.extents(), [
            fc.Pt(fc.Dim(6.0,'mm'),fc.Dim(0.0,'mm')),
            fc.Pt(fc.Dim(-6.0,'mm'),fc.Dim(0.0,'mm')),
            fc.Pt(fc.Dim(0.0,'mm'),fc.Dim(6.0,'mm')),
            fc.Pt(fc.Dim(0.0,'mm'),fc.Dim(-6.0,'mm')),
            fc.Pt(fc.Dim(4.242,'mm'),fc.Dim(4.242,'mm')),
            fc.Pt(fc.Dim(4.242,'mm'),fc.Dim(-4.242,'mm')),
            fc.Pt(fc.Dim(-4.242,'mm'),fc.Dim(4.242,'mm')),
            fc.Pt(fc.Dim(-4.242,'mm'),fc.Dim(-4.242,'mm'))])
    def test_04covers(self):
        self.assertTrue(self.p1.covers(fc.RoundPad('45 mil','8mil','4mil')))
    
    def test_05annulus(self):
        self.assertEqual(self.p1.annulus(fc.Dim('35mil')),fc.Dim.MIL(10))
    
    def test_06validAnnulus(self):
        r = fc.RulesDictionary({'minannulus':fc.Dim('10mil')})
        self.assertTrue(self.p1.validAnnulus(fc.Dim('35mil'),r))
        self.assertFalse(self.p1.validAnnulus(fc.Dim('36mil'),r))
    
    

if __name__ == '__main__':
    ut.main()
