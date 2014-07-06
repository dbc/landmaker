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

class FP_enc(fc.Footprint):
    @classmethod
    def helptext(cls):
        yield "Alpha encoders."
        yield "Currently only handles RE130F"
        yield "  type must be one of:"
        yield "    RE130F"
        yield "    <others tbw>"
    @classmethod
    def parse(cls, params, rules, rack, warningCallback):
        # Call the standard parameter parser.
        kwspecs = {
            'type':     fc.KWSpec(None, True, False),
            'ann':      fc.KWSpec('mil', False, False),
        }
        kw = cls.parseKwargs(params, kwspecs)
        # Pick up general rules
        maskrelief = rules['maskrelief']
        clearance = rules['minspace']
        # Do type-specific work.
        if kw['type'].upper() == 'RE130F':
            # Construct pads
            exactDrill = fc.Dim.INCH(0.04)
            rackDrill =  rack[exactDrill]
            ioPadDia = rules['annulus_hs']*2.0 + rackDrill
            mntExactDrill = fc.Dim.INCH(.083)
            mntRackDrill = rack[mntExactDrill]
            mntPadDia = rules['annulus_hs']*2.0 + mntRackDrill
            if True:
                # Someday there might be a parameter option w.r.t. drill
                ioDrill = rackDrill
            ioPad = cls.roundPad(ioPadDia, clearance, maskrelief)
            mntPad = cls.roundPad(mntPadDia, clearance, maskrelief)
            # Construct Pin geometries
            ioGeo = cls.pinGeometry(ioPad, ioDrill)
            mntGeo = cls.pinGeometry(mntPad, mntRackDrill)
            # Construct pin specs
            pinSpecs = []
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(-275),-fc.Dim.MIL(100),1,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(-275), fc.Dim.MIL(100),2,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(295), fc.Dim.MIL(100),3,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(295), fc.Dim.MIL(0),4,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(295),-fc.Dim.MIL(100),5,ioGeo))
            # Mounting pins become pins 6 & 7 for "hardware" connection.
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(0),-fc.Dim.MIL(520/2.0),6,mntGeo))                            
            pinSpecs.append(cls.pinSpec(fc.Dim.MIL(0), fc.Dim.MIL(520/2.0),7,mntGeo))                            
            # Silk
            silk = []
            pw = rules['minsilk']
            silkx = fc.Dim.MIL(520)/2.0
            silky = fc.Dim.MIL(490)/2.0
            silkxgap = fc.Dim.MIL(70)
            silkygap = fc.Dim.MIL(150)
            silk.append(cls.silkLine( silkx,-silky, silkxgap,-silky, pw))
            silk.append(cls.silkLine(-silkx,-silky,-silkxgap,-silky, pw))
            silk.append(cls.silkLine( silkx, silky, silkxgap, silky, pw))
            silk.append(cls.silkLine(-silkx, silky,-silkxgap, silky, pw))
            silk.append(cls.silkLine(-silkx,-silky,-silkx,-silkygap, pw))
            silk.append(cls.silkLine(-silkx, silky,-silkx, silkygap, pw))
            silk.append(cls.silkLine( silkx,-silky, silkx,-silkygap, pw))
            silk.append(cls.silkLine( silkx, silky, silkx, silkygap, pw))
            # Keep-outs
            keepOuts = []
        else:
            raise fc.ParamSyntax(str(kw['type']).join(["Unkown type: ","'"]))
        # Make comments
        cmt = cls.standardComments(cls.pluginName(), kw, kwspecs, rules,
            ['maskrelief','minspace','annulus_hs','refdessize'])
        cmt.append('Pins 6 & 7 are case.')
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(0,fc.Dim.MM(2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Alpha ' + kw['type'] + ' encoder.'
        return cls(desc, rd, pinSpecs, silk, cmt, keepOuts) 
