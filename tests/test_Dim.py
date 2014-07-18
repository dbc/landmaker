import landmaker.footprintcore as fc
import unittest as ut

class TestDim(ut.TestCase):
    def setUp(self):
        self.mm1inch = fc.Dim(25.4,'mm')
        self.inch1inch = fc.Dim.INCH(1)
        self.mm1mm = fc.Dim.MM(1)
        self.mm2mm = fc.Dim.MM(2)

    def test_00oper_eq_ne(self):
        self.assertEqual(self.mm1mm, 1.0)
        self.assertEqual(1.0, self.mm1mm)
        self.assertNotEqual(self.mm1mm, 2.0)
        self.assertNotEqual(2.0, self.mm1mm)
        self.assertEqual(self.mm1inch,self.inch1inch)
        self.assertNotEqual(self.mm1mm, self.mm2mm)
        self.assertTrue(self.mm1mm == 1.0)
        self.assertTrue(1.0 == self.mm1mm)
        self.assertTrue(self.mm1mm != 2.0)
        self.assertTrue(2.0 !=self.mm1mm)
        self.assertTrue(self.mm1inch == self.inch1inch)
        self.assertTrue(self.mm1mm !=  self.mm2mm)
        self.assertTrue(1 == self.mm1mm)
        self.assertTrue('1' == self.mm1mm)
    
    def test_01oper_lt(self):
        self.assertTrue(self.mm1mm < self.mm2mm)
        self.assertFalse(self.inch1inch < self.mm1mm)
        self.assertTrue(self.mm1mm < 2.0)
        self.assertTrue(self.inch1inch < 5.0)
        self.assertTrue(1.0 < self.mm2mm)
        self.assertFalse(50.0 < self.inch1inch)

    def test_02oper_ge(self):
        self.assertFalse(self.mm1mm >= self.mm2mm)
        self.assertTrue(self.inch1inch >= self.mm1mm)
        self.assertFalse(self.mm1mm >= 2.0)
        self.assertTrue(self.inch1inch >= 0.5)
        self.assertFalse(1.0 >= self.mm2mm)
        self.assertTrue(50.0 >= self.inch1inch)
        self.assertTrue(self.mm1mm >= 1.0)
        self.assertTrue(1.0 >= self.mm1mm)
        self.assertTrue(self.mm1inch >= self.inch1inch)

    def test_03convert(self):
        self.assertEqual(int(self.inch1inch),25)
        self.assertEqual(float(self.inch1inch),25.4)
        self.assertEqual(float(self.mm1mm),1.0)

    def test_04fromStr(self):
        d = fc.Dim.from_str('3.0 mm')
        self.assertEqual(d, fc.Dim.MM(3))

 
if __name__ == '__main__':
    ut.main()
