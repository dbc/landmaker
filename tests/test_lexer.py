import plugins.footprintcore as fc
import lookaheadtools as la
import unittest as ut

class TestKWLexer(ut.TestCase):
    def setUp(self):
        self.stim = [
            'a=1',
            'abc  def  123 45ab6 . * 9 "abc"',
            '0.1mm 1.2 mm 4 mil .1inch #48 5 6.7 .8',
            '"abc"' + "'def'",
            '"no quote',
            "'quoteless, too",
            "abc=1,2 def=3 ghi jlk 4 4.5mm",
        ]

    def test_00touch(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[0]))
        expect = [fc.KWToken(t,v) for t,v in [('KW','a'),('=','='),('NUM',1.0)]]
        actual = [tkn for tkn in lxr]
        self.assertEqual(actual, expect)

    def test_01kwbasic(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[1]))
        actual = [tkn for tkn in lxr]
        expect = []
        #self.assertEqual(actual, expect)

    def test_02dim(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[2]))
        actual = [tkn for tkn in lxr]
        expect = [
            fc.KWToken('NUM',fc.Dim(0.1,'mm')),
            fc.KWToken('NUM',fc.Dim(1.2,'mm')),
            fc.KWToken('NUM',fc.Dim(0.1016,'mil')),
            fc.KWToken('NUM',fc.Dim(2.54,'inch')),
            fc.KWToken('NUM',fc.Dim(1.9304,'inch')),
            fc.KWToken('NUM',5.0),
            fc.KWToken('NUM',6.7),
            fc.KWToken('NUM',0.8),
        ]
        self.assertEqual(actual, expect)

    def test_03str(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[3]))
        actual = [tkn for tkn in lxr]
        expect = [fc.KWToken('STR','abc'), fc.KWToken('STR','def')]
        self.assertEqual(actual, expect)
        
    def test_04badstr(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[4]))
        actual = [tkn for tkn in lxr]
        expect = [fc.KWToken('STR','no quote')]
        self.assertEqual(actual, expect)
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[5]))
        actual = [tkn for tkn in lxr]
        expect = [fc.KWToken('STR','quoteless, too')]        
        self.assertEqual(actual, expect)

    def test_05mixed1(self):
        lxr = fc.KWParamLexer(la.LinesOf(self.stim[6]))
        actual = [tkn for tkn in lxr]
        expect = [
            fc.KWToken('KW','abc'),
            fc.KWToken('=','='),
            fc.KWToken('NUM',1.0),
            fc.KWToken(',',','),
            fc.KWToken('NUM',2.0),
            fc.KWToken('KW','def'),
            fc.KWToken('=','='),
            fc.KWToken('NUM',3.0),
            fc.KWToken('KW','ghi'),
            fc.KWToken('KW','jlk'),
            fc.KWToken('NUM',4.0),
            fc.KWToken('NUM',fc.Dim(4.5,'mm'))
        ]
        self.assertEqual(actual, expect)
        
 
if __name__ == '__main__':
    ut.main()
