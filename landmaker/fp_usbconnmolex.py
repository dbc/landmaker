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
# Molex throughhole: USB mini-AB receptical 54819-0519

# FIXME:
# check min annulus rule carefully

import footprintcore as fc

class FP_usbconnmolex(fc.Footprint):
    kwspecs = {
        'type':     fc.KWSpec(None, True, False),
        'metric':   fc.KWSpec(None, False, False),
    }
    @classmethod
    def helptext(cls):
        yield "Molex USB connectors."
        yield "Currently only handles mini-AB receptical 54819-0519"
        yield "  type must be one of:"
        yield "    54819-0519"
        yield "    <others tbw>"
    @classmethod
    def parse(cls, footprintname, params, rules, rack, warning_callback):
        # Call the standard parameter parser.
        kw = cls.parse_kwargs(params, cls.kwspecs)
        # Pick up general rules
        maskrelief = rules['maskrelief']
        clearanceRule = rules['minspace']
	# FIXME: add a parameter to select either rule-based clearance,
	# explicitly set clearance, or default of 12mil.
        clearance = fc.Dim.MIL(12) # eradicate Cu hairs in gEDA/pcb
        # Do type-specific work.
        if kw['type'] == '54819-0519':
            # Construct pads
            exactDrill = fc.Dim.MM(0.7)
            ioPadDia = fc.Dim.MM(1.05)
            ioTopPad = cls.roundPad(ioPadDia, clearance, maskrelief)
            rackDrill =  rack[exactDrill]
            if not ioTopPad.valid_annulus(rackDrill, rules):
                warning_callback('Rack drill too large.')
                if 'metric' in kw:
                    warning_callback('Using ' + str(exactDrill))
                    ioDrill = exactDrill
                else:
                    warning_callback('Using #70.')
                    ioDrill = fc.Dim.DRILL('#70')
            else:
                ioDrill = rackDrill
            mountDrill = rack[fc.Dim.MM(1.9)]
            # Make bot I/O pads by stretching.
            stretch_by = fc.Dim.MM(1.65) - ioTopPad.dia
            ioBotPadL = cls.roundedRectPad.fromPad(ioTopPad)
            ioBotPadL.stretch(stretch_by,  '-x')
            ioBotPadR = cls.roundedRectPad.fromPad(ioTopPad)
            ioBotPadR.stretch(stretch_by,  '+x')
##            stretchBy = fc.Dim.MM(1.65) - ioTopPad.dia
##            ioBotPadL = cls.roundedRectPad.stretch(ioTopPad,-stretchBy, 0)
##            ioBotPadR = cls.roundedRectPad.stretch(ioTopPad, stretchBy, 0)
            mountPad = cls.roundPad(fc.Dim.MM(2.7), clearanceRule, maskrelief)
            # Construct Pin geometries
            ioLGeo = cls.pinGeometry(ioTopPad, ioDrill, ioBotPadL)
            ioRGeo = cls.pinGeometry(ioTopPad, ioDrill, ioBotPadR)
            mntGeo = cls.pinGeometry(mountPad, mountDrill)
            # Construct pin specs
            pinLx = fc.Dim.MM(-1.2)
            pinLy = fc.Dim.MM(0.8)
            zero = fc.Dim.MM(0)
            pinSpecs = []
            pinSpecs.append(cls.pinSpec(fc.Pt(zero,2*pinLy),1,ioRGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt(pinLx,pinLy),2,ioLGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt(zero,zero),3,ioRGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt(pinLx,-pinLy),4,ioLGeo))
            pinSpecs.append(cls.pinSpec(fc.Pt(zero,-2*pinLy),5,ioRGeo))
            # Mounting pins become pins 6 & 7 for "hardware" connection.
            mntPt = fc.Pt.MM(-5.05, 7.3/2.0)
##            mntX = fc.Dim.MM(-5.05)
##            mntY = fc.Dim.MM(7.3/2.0)
            pinSpecs.append(cls.pinSpec(mntPt,6,mntGeo))                            
            pinSpecs.append(cls.pinSpec(mntPt.reflox,7,mntGeo))
            # Keep-outs
            keepOuts = []
            keepOuts.append(cls.keepOutRect(fc.Pt.MM(-1.8, 3), fc.Pt.MM( 0.7, 4.4)))
            keepOuts.append(cls.keepOutRect(fc.Pt.MM(-1.8, -4.4), fc.Pt.MM( 0.7, -3)))
##            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-6.8), fc.Dim.MM(3.1),\
##                                            fc.Dim.MM(-5.6),-fc.Dim.MM(3.1)))
            keepOuts.append(cls.keepOutRect(fc.Pt.MM(-6.8, 3.0),\
                                            fc.Pt.MM(-6.4,-3.0)))
            keepOuts.append(cls.keepOutRect(fc.Pt.MM(-6.4, 2.2),\
                                            fc.Pt.MM(-5.6,-2.2)))
        else:
            raise fc.ParamSyntax(str(kw['type']).join(["Unkown type: ","'"]))
        # Make comments
        cmt = cls.standard_comments(cls.plugin_name(), kw, rules,
            ['maskrelief','minspace','minannulus','refdessize','minsilk'])
        cmt.append('Pins 6 & 7 are case.')
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(fc.Pt.MM(0,2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Molex ' + kw['type'] + ' USB connector.'
        return cls(footprintname, desc, rd, pinSpecs, [], cmt, keepOuts) 
