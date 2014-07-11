#   Copyright 2014 David B. Curtis

#   This file is part of landmaker.
#   
#   landmaker is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   landmaker is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with landmaker.  If not, see <http://www.gnu.org/licenses/>.
#   

# Footprints for:
# Alpha through hole: Rotary encoder RE130F

import footprintcore as fc
import datetime as dt
from collections import namedtuple

DrillFit=namedtuple('DrillFit','closeFit freeFit')

metric = {
    "M1.0":DrillFit(fc.Dim.MM(1.05),fc.Dim.MM(1.2)),
    "M1.1":DrillFit(fc.Dim.MM(1.15),fc.Dim.MM(1.3)),
    "M1.2":DrillFit(fc.Dim.MM(1.3),fc.Dim.MM(1.5)),
    "M1.4":DrillFit(fc.Dim.MM(1.5),fc.Dim.MM(1.7)),
    "M1.6":DrillFit(fc.Dim.MM(1.7),fc.Dim.MM(2.0)),
    "M1.8":DrillFit(fc.Dim.MM(1.9),fc.Dim.MM(2.2)),
    "M2.0":DrillFit(fc.Dim.MM(2.2),fc.Dim.MM(2.6)),
    "M2.2":DrillFit(fc.Dim.MM(2.4),fc.Dim.MM(2.8)),
    "M2.5":DrillFit(fc.Dim.MM(2.7),fc.Dim.MM(3.1)),
    "M3.0":DrillFit(fc.Dim.MM(3.2),fc.Dim.MM(3.6)),
    "M3.5":DrillFit(fc.Dim.MM(3.7),fc.Dim.MM(4.2)),
    "M4.0":DrillFit(fc.Dim.MM(4.3),fc.Dim.MM(4.8)),
    "M4.5":DrillFit(fc.Dim.MM(4.8),fc.Dim.MM(5.3)),
    "M5.0":DrillFit(fc.Dim.MM(5.3),fc.Dim.MM(5.8)),
}

number = {}

class FP_hole(fc.Footprint):
    @classmethod
    def helptext(cls):
        yield 'Holes for hardware.'
        yield '  specify one of:'
        yield "    drill=<size> ; explicit dimension size"
        yield '    screw="Mn.n"  ; metric screw'
        yield '    screw="#nn"  ; hardware size number.'
        yield '  specify pad size:'
        yield '    pad=<size>'
        yield "  optinally:"
        yield '    fit="free" ; the default'
        yield '    fit="close" '
    @classmethod
    def parse(cls, params, rules, rack, warningCallback):
        # Call the standard parameter parser.
        kwspecs = {
            'pad':      fc.KWSpec('mm', True, False),
            'drill':    fc.KWSpec(None, False, False),
            'screw':    fc.KWSpec(None, False, False),
            'fit':      fc.KWSpec(None, False, False),
        }
        kw = cls.parseKwargs(params, kwspecs)
        return cls.fromKwargs(rules, rack, warningCallback, **kw)
    @classmethod
    def fromKwargs(cls, rules, rack, warningCallback, **kw):
        # Pick up general rules
        maskrelief = rules['maskrelief']
        clearance = rules['minspace']
        if 't' in fc.debug:
            fc.trace('maskrelief',globals(),locals())
        # Generate the pin.
        try:
            fit = kw['fit']
            if fit not in ['free','close']:
                raise fc.ParamSyntax('fit must be one of: "free","close".')
        except KeyError:
            fit = 'free'
        try:
            drill = kw['drill']
        except KeyError:
            try:
                screw=kw['screw']
            except KeyError:
                raise fc.ParamSyntax("Expected one of 'drill' or 'screw'.")
            try:
                drillChoices = metric[screw]
            except KeyError:
                try:
                    drillChoices = number[screw]
                except KeyError:
                    raise fc.ParamSyntax(screw.join(["drill '","' not found."]))
            drill = drillChoices.freeFit if fit == 'free' else drillChoices.closeFit
        rackDrill = rack[drill]
        # construct Pad
        pad = cls.roundPad(kw['pad'], clearance, maskrelief)
        # construct pin geometry
        geo = cls.pinGeometry(pad, rackDrill)
        # construct pin specs
        #pinSpecs = [cls.pinSpec(fc.Dim.MIL(0),fc.Dim.MIL(0),1,geo)]
        pinSpecs = [cls.pinSpec(fc.Pt.MIL(0,0),1,geo)]
        # No silk
        silk = []
        # No keep-outs
        keepOuts = []
        # Make comments
        cmt = cls.standardComments(cls.pluginName(), kw, rules,
            ['maskrelief','minspace','refdessize'])
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(fc.Pt.MM(0,2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Screw hole.'
        return cls(desc, rd, pinSpecs, silk, cmt, keepOuts) 
