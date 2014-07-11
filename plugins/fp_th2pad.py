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
import datetime as dt

class FP_th2pad(fc.Footprint):
    @classmethod
    def helptext(cls):
        yield "Through-hole, two-pad components."
        yield "th2pad desc=<s> dia=<mils> spacing=<mils> drill=<size, inches> artwidth=<mils> artlen=<mils>"
        yield "th2pad desc=<s> annulus=[<mils>|lhsa|shsa|asa] spacing=<mils> drill=<size, inches> artwidth=<mils> artlen=<mils>"
        yield "  desc is a description string."
        yield "  One of dia, pad diameter in mils, or annulus must be specified."
        yield "  Annulus is size in mils over effective pre-plated hole size,"
        yield "  after applying drill rack, if any is in force."
        yield "  Annulus may be specified in rules:"
        yield "    lhsa - large hand solder annulus."
        yield "    shsa - small hand solder annulus."
        yield "    asa - automatic assembly solder annulus."
        yield "  Spacing is the distance in mils between the two pad drill centers."
        yield "  Drill size is specified in fractional inches.  If a drill rack"
        yield "  is in force, the drill size will select a drill from the rack,"
        yield "  otherwise the given drill size will be used.  "
        yield "  When annulus is specified, the final pad diameter is driven by"
        yield "  the drill size chosen from the rack."
        yield "  An optional silk screen rectangle is generated by setting artwidth"
        yield "  to the width of the rectangle.  Length can be automatcially "
        yield "  calculated, or can be specified in artlen."
        yield "  Rules referenced: maskrelief, minspace, silkwidth, refdessize."
    @classmethod
    def parse(cls, params, rules, rack, warningCallback):
        # Call the standard parameter parser.
        kwspecs = {
            'desc':     fc.KWSpec(None, True, False),
            'spacing':  fc.KWSpec('mil', True, False),
            'drill':    fc.KWSpec('inch', True, False),
            'dia' :     fc.KWSpec('mil', False, False),
            'annulus': fc.KWSpec('mil', False, False),
            'artwidth': fc.KWSpec('mil', False, False),
            'artlen' :  fc.KWSpec('mil', False, False),
        }
        kw = cls.parseKwargs(params, kwspecs)
        # Compute sizes.
        drill = rack[kw['drill']]
        if 'dia' in kw:
            diameter = kw['dia']
        elif 'annulus' in kw:
            diameter = drill + 2.0 * rules.symb(kw['annulus'])
        else:
            raise fc.ParamSyntax("Must specify one of 'dia' or 'annulus'.")
        maskrelief = rules['maskrelief']
        clearance = rules['minspace']
        # Build the pin geometry
        pad = cls.roundPad(diameter, clearance, maskrelief)
        pg = cls.pinGeometry(pad, drill)
        pg.valid(rules)
        # Make pins
        halfwidth = kw['spacing'] / 2.0
        zero = halfwidth.u0
        pin1 = cls.pinSpec(fc.Pt(-halfwidth, zero), 1, pg)
        pin2 = cls.pinSpec(fc.Pt( halfwidth, zero), 2, pg)
        # Make silk
        box = []
        silkw = rules['minsilk']
        try:
            awhalf = kw['artwidth']/2.0
            try:
                alhalf = kw['artlen']/2.0
            except KeyError:
                alhalf = halfwidth - (diameter + maskrelief + 1.5*silkw)
            # Draw a box.
            box.append(cls.silkLine(fc.Pt( alhalf,  awhalf), fc.Pt(-alhalf,  awhalf), silkw))
            box.append(cls.silkLine(fc.Pt( alhalf, -awhalf), fc.Pt(-alhalf, -awhalf), silkw))
            box.append(cls.silkLine(fc.Pt( alhalf,  awhalf), fc.Pt( alhalf, -awhalf), silkw))
            box.append(cls.silkLine(fc.Pt(-alhalf,  awhalf), fc.Pt(-alhalf, -awhalf), silkw))
        except KeyError:
            # No silk at all.
            awhalf = fc.Dim.MIL(0) # For placing refdes
        # Make refdes
        silky = awhalf+20
        rd = cls.refDes(fc.Pt(silky.u0,silky),0, rules['minsilk'], '', rules['refdessize'])
        # Make comments
        cmt = cls.standardComments('th2pad', kw, rules, 
            ['maskrelief','minspace','minsilk','refdessize'])
        # Create the footprint instance.
        desc = str(kw['desc'])
        return cls(desc, rd, [pin1, pin2], box, cmt)
