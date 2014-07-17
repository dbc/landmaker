import landmaker.gedascripting as s
import unittest as ut

def warning_sink(msg):
    pass

class TestScripting(ut.TestCase):
    def setUp(self):
        self.rack = s.DrillRack()
        self.rules = s.RulesDictionary()
        self.rules['maskrelief'] = s.Dim('4mil')
        self.rules['minspace'] = s.Dim('8mil')
        self.rules['refdessize'] = s.Dim('40mil')
        self.rules['minsilk'] = s.Dim('8mil')

    def test_00hole01(self):
        fp = s.hole.fromKwargs('hole01',self.rules,self.rack,warning_sink,
            drill=s.Dim('0.02inch'), pad=s.Dim('35mil'))
