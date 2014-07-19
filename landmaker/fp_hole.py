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


import footprintcore as fc
from collections import namedtuple

DrillFit=namedtuple('DrillFit','close_fit, free_fit')

metric = {
    "M1.0":DrillFit(fc.Dim.MM(1.05),fc.Dim.MM(1.2)),
    "M1"  :DrillFit(fc.Dim.MM(1.05),fc.Dim.MM(1.2)),
    "M1.1":DrillFit(fc.Dim.MM(1.15),fc.Dim.MM(1.3)),
    "M1.2":DrillFit(fc.Dim.MM(1.3),fc.Dim.MM(1.5)),
    "M1.4":DrillFit(fc.Dim.MM(1.5),fc.Dim.MM(1.7)),
    "M1.6":DrillFit(fc.Dim.MM(1.7),fc.Dim.MM(2.0)),
    "M1.8":DrillFit(fc.Dim.MM(1.9),fc.Dim.MM(2.2)),
    "M2.0":DrillFit(fc.Dim.MM(2.2),fc.Dim.MM(2.6)),
    "M2"  :DrillFit(fc.Dim.MM(2.2),fc.Dim.MM(2.6)),
    "M2.2":DrillFit(fc.Dim.MM(2.4),fc.Dim.MM(2.8)),
    "M2.5":DrillFit(fc.Dim.MM(2.7),fc.Dim.MM(3.1)),
    "M3.0":DrillFit(fc.Dim.MM(3.2),fc.Dim.MM(3.6)),
    "M3"  :DrillFit(fc.Dim.MM(3.2),fc.Dim.MM(3.6)),
    "M3.5":DrillFit(fc.Dim.MM(3.7),fc.Dim.MM(4.2)),
    "M4.0":DrillFit(fc.Dim.MM(4.3),fc.Dim.MM(4.8)),
    "M4"  :DrillFit(fc.Dim.MM(4.3),fc.Dim.MM(4.8)),
    "M4.5":DrillFit(fc.Dim.MM(4.8),fc.Dim.MM(5.3)),
    "M5.0":DrillFit(fc.Dim.MM(5.3),fc.Dim.MM(5.8)),
    "M5"  :DrillFit(fc.Dim.MM(5.3),fc.Dim.MM(5.8)),
}

number = {}

class FP_hole(fc.Footprint):
    kwspecs = {
        'pad':      fc.KWSpec('mm', True, False),
        'drill':    fc.KWSpec('mm', False, False),
        'screw':    fc.KWSpec(None, False, False),
        'fit':      fc.KWSpec(None, False, False),
    }
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
    def parse(cls, footprintname, params, rules, rack, warning_callback):
        # Call the standard parameter parser.
        kw = cls.parse_kwargs(params, cls.kwspecs)
        return cls.from_kwargs(footprintname, rules, rack, warning_callback, **kw)
    @classmethod
    def from_kwargs(cls, footprintname, rules, rack, warning_callback, **kw):
        args = cls._norm_args(kw)
        # Pick up general rules
        maskrelief = rules['maskrelief']
        clearance = rules['minspace']
        if 't' in fc.debug:
            fc.trace('maskrelief',globals(),locals())
        # Select drill
        rackDrill = rack[args.drill]
        # construct Pad
        pad = cls.roundPad(args.pad, clearance, maskrelief)
        # construct pin geometry
        geo = cls.pinGeometry(pad, rackDrill, '=')
        # construct pin specs
        pinSpecs = [cls.pinSpec(fc.Pt.MIL(0,0),1,geo)]
        # No silk
        silk = []
        # No keep-outs
        keepOuts = []
        # Make comments
        cmt = cls.standard_comments(cls.plugin_name(), kw, rules,
            ['maskrelief','minspace','refdessize'])
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(fc.Pt.MM(0,2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Screw hole.'
        return cls(footprintname, desc, rd, pinSpecs, silk, cmt, keepOuts)
    @classmethod
    def _norm_args(cls, kwargs):
        try:
            if kwargs['fit'] not in ['free','close']:
                raise fc.ParamValueError('fit must be one of: "free","close".')
        except KeyError:
            kwargs['fit'] = 'free'
        try:
            drill = kwargs['drill']
        except KeyError:
            try:
                screw=kwargs['screw']
            except KeyError:
                raise fc.ParamSyntax("Expected one of 'drill' or 'screw'.")
            try:
                drillChoices = metric[screw]
            except KeyError:
                try:
                    drillChoices = number[screw]
                except KeyError:
                    raise fc.ParamValueError(screw.join(["drill '","' not found."]))
            kwargs['drill'] = drillChoices.free_fit if fit == 'free' else drillChoices.close_fit
        return cls.arg_object(kwargs)
       
