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

class FP_enc(fc.Footprint):
    kwspecs = {
        'type':     fc.KWSpec(None, True, False),
        'ann':      fc.KWSpec('mil', False, False),
    }
    @classmethod
    def helptext(cls):
        yield "Alpha encoders."
        yield "Currently only handles RE130F"
        yield "  type must be one of:"
        yield "    RE130F"
        yield "    <others tbw>"
    @classmethod
    def parse(cls, footprintname, params, rules, rack, warning_callback):
        # Call the standard parameter parser.
        kw = cls.parse_kwargs(params, cls.kwspecs)
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
            # Construct Pin Geometries
            ioGeo = cls.thruPin.circle(ioDrill, clearance, ioPadDia, maskrelief)
            mntGeo = cls.thruPin.circle(mntRackDrill, clearance, mntPadDia, maskrelief)
            # Construct pin specs
            pinSpecs = []
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL(-275, 100),1,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL(-275,-100),2,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL( 295,-100),3,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL( 295,   0),4,ioGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL( 295, 100),5,ioGeo))
            # Mounting pins become pins 6 & 7 for "hardware" connection.
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL(0,-520/2.0),6,mntGeo))                            
            pinSpecs.append(cls.pinSpec(fc.Pt.MIL(0, 520/2.0),7,mntGeo))                            
            # Silk
            silk = []
            pw = rules['minsilk']
            silkCorner = fc.Pt.MIL(520/2.0, 490/2.0)
            silkXLineEP = fc.Pt(fc.Dim.MIL(70), silkCorner.y)
            silkYLineEP = fc.Pt(silkCorner.x, fc.Dim.MIL(150))
            silk.append(cls.silkLine( silkCorner,  silkXLineEP, pw))
            silk.append(cls.silkLine( silkCorner,  silkYLineEP, pw))
            silk.append(cls.silkLine(-silkCorner, -silkXLineEP, pw))
            silk.append(cls.silkLine(-silkCorner, -silkYLineEP, pw))
            silk.append(cls.silkLine( silkCorner.reflox,  silkXLineEP.reflox, pw))
            silk.append(cls.silkLine( silkCorner.reflox,  silkYLineEP.reflox, pw))
            silk.append(cls.silkLine( silkCorner.refloy,  silkXLineEP.refloy, pw))
            silk.append(cls.silkLine( silkCorner.refloy,  silkYLineEP.refloy, pw))
            # Keep-outs
            keepOuts = []
        else:
            raise fc.ParamSyntax(str(kw['type']).join(["Unkown type: ","'"]))
        # Make comments
        cmt = cls.standard_comments(cls.plugin_name(), kw, rules,
            ['maskrelief','minspace','annulus_hs','refdessize'])
        cmt.append('Pins 6 & 7 are case.')
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(fc.Pt.MM(0,2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Alpha ' + kw['type'] + ' encoder.'
        return cls(footprintname, desc, rd, pinSpecs, silk, cmt, keepOuts) 
