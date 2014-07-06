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

import footprintcore as fc
import datetime as dt

class FP_usbconnmolex(fc.Footprint):
    @classmethod
    def helptext(cls):
        yield "Molex USB connectors."
        yield "Currently only handles mini-AB receptical 54819-0519"
        yield "  type must be one of:"
        yield "    54819-0519"
        yield "    <others tbw>"
    @classmethod
    def parse(cls, params, rules, rack, warningCallback):
        # Call the standard parameter parser.
        kwspecs = {
            'type':     fc.KWSpec(None, True, False),
            'metric':   fc.KWSpec(None, False, False),
        }
        kw = cls.parseKwargs(params, kwspecs)
        # Pick up general rules
        maskrelief = rules['maskrelief']
        clearanceRule = rules['minspace']
        clearance = fc.Dim.MIL(12) # eradicate Cu hairs in gEDA/pcb
        # Do type-specific work.
        if kw['type'] == '54819-0519':
            # Construct pads
            exactDrill = fc.Dim.MM(0.7)
            ioPadDia = fc.Dim.MM(1.05)
            ioTopPad = cls.roundPad(ioPadDia, clearance, maskrelief)
            rackDrill =  rack[exactDrill]
            if not ioTopPad.validAnnulus(rackDrill, rules):
                warningCallback('Rack drill too large.')
                if 'metric' in kw:
                    warningCallback('Using ' + str(exactDrill))
                    ioDrill = exactDrill
                else:
                    warningCallback('Using #70.')
                    ioDrill = fc.Dim.DRILL('#70')
            else:
                ioDrill = rackDrill
            mountDrill = rack[fc.Dim.MM(1.9)]
            stretchBy = fc.Dim.MM(1.65) - ioTopPad.dia
            ioBotPadL = cls.roundedRectPad.stretch(ioTopPad,-stretchBy, 0)
            ioBotPadR = cls.roundedRectPad.stretch(ioTopPad, stretchBy, 0)
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
            pinSpecs.append(cls.pinSpec(zero,-2*pinLy,1,ioRGeo))
            pinSpecs.append(cls.pinSpec(pinLx,-pinLy,2,ioLGeo))
            pinSpecs.append(cls.pinSpec(zero,zero,3,ioRGeo))
            pinSpecs.append(cls.pinSpec(pinLx,pinLy,4,ioLGeo))
            pinSpecs.append(cls.pinSpec(zero,2*pinLy,5,ioRGeo))
            # Mounting pins become pins 6 & 7 for "hardware" connection.
            mntX = fc.Dim.MM(-5.05)
            mntY = fc.Dim.MM(7.3/2.0)
            pinSpecs.append(cls.pinSpec(mntX,-mntY,6,mntGeo))                            
            pinSpecs.append(cls.pinSpec(mntX, mntY,7,mntGeo))
            # Keep-outs
            keepOuts = []
            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-1.8),-fc.Dim.MM(3),\
                                            fc.Dim.MM( 0.7),-fc.Dim.MM(4.4)))
            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-1.8), fc.Dim.MM(3),\
                                            fc.Dim.MM( 0.7), fc.Dim.MM(4.4)))
##            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-6.8), fc.Dim.MM(3.1),\
##                                            fc.Dim.MM(-5.6),-fc.Dim.MM(3.1)))
            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-6.8), fc.Dim.MM(3.0),\
                                            fc.Dim.MM(-6.4),-fc.Dim.MM(3.0)))
            keepOuts.append(cls.keepOutRect(fc.Dim.MM(-6.4), fc.Dim.MM(2.2),\
                                            fc.Dim.MM(-5.6),-fc.Dim.MM(2.2)))
        else:
            raise fc.ParamSyntax(str(kw['type']).join(["Unkown type: ","'"]))
        # Make comments
        cmt = cls.standardComments(cls.__name__.split('_')[2],
            kw, kwspecs, rules,
            ['maskrelief','minspace','minannulus','refdessize'])
        cmt.append('Pins 6 & 7 are case.')
        # Create the refdes, description, and footprint instance.
        rd = cls.refDes(0,fc.Dim.MM(2),0, rules['minsilk'], '', rules['refdessize'])
        desc = 'Molex ' + kw['type'] + ' USB connector.'
        return cls(desc, rd, pinSpecs, [], cmt, keepOuts) 
