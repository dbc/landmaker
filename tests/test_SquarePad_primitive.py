import landmaker.footprintcore as fc
import unittest as ut

class TestRoundPadPrimitives(ut.TestCase):
    def setUp(self):
        self.p1 = fc.SquarePad('50mil','10mil','5mil')
    
    def test_00constructors(self):
        self.assertEqual(self.p1.width, fc.Dim.MIL(50))
        self.assertEqual(self.p1.dia, fc.Dim('50mil'))

    def test_01repr(self):
        self.assertEqual(repr(self.p1),"SquarePad(Dim(1.27,'mil'),Dim(0.254,'mil'),Dim(0.127,'mil'))")

    def test_02widthProp(self):
        self.p1.width = fc.Dim.MIL(40)
        self.assertEqual(self.p1.width,fc.Dim('40mil'))
        self.assertEqual(self.p1.dia,fc.Dim('40mil'))

    def test_03eq(self):
        self.assertTrue(self.p1 == fc.SquarePad(fc.Dim.MIL(50),fc.Dim.MIL(10), fc.Dim.MIL(5)))
        self.assertTrue(self.p1 != fc.SquarePad('50mil','10mil','8mil'))
        self.assertTrue(self.p1 != fc.SquarePad('50mil','8mil','5mil'))
        self.assertTrue(self.p1 != fc.SquarePad('45mil','10mil','5mil'))

    def test_04extents(self):
        self.assertEqual(self.p1.extents(), [
            fc.Pt(fc.Dim(-0.635,'mil'),fc.Dim(-0.635,'mil')),
            fc.Pt(fc.Dim(0.635,'mil'),fc.Dim(-0.635,'mil')),
            fc.Pt(fc.Dim(-0.635,'mil'),fc.Dim(0.635,'mil')),
            fc.Pt(fc.Dim(0.635,'mil'),fc.Dim(0.635,'mil'))])

    def test_05covers(self):
        pl = []
        pl.append((fc.SquarePad('40mil','8mil','8mil'),False))
        pl.append((fc.SquarePad('60mil','8mil','8mil'),True))
        pl.append((fc.RoundPad('40mil','8mil','8mil'),False))
        pl.append((fc.RoundPad('60mil','8mil','8mil'),True))
        # FIXME: add other pad types.
        for pad, invert in pl:
            self.assertTrue(self.p1.covers(pad) ^ invert)
                

    def test_06annulus(self):
        self.assertEqual(self.p1.annulus(fc.Dim.MIL(30)),fc.Dim.MIL(10))
        
    def test_NNvalid_annulus(self):
        pass # FIXME

    
    

if __name__ == '__main__':
    ut.main()
    
