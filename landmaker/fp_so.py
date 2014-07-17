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

# FIXME: Check minmask rule between pads.
# FIXME: Add option to generate gang masks.

import footprintcore as fc

class FP_so(fc.Footprint):
    kw_specs = {
        'pins'       : fc.KWSpec(None, True, False),
        'padlen'     : fc.KWSpec('mm', True, False),
        'padwidth'   : fc.KWSpec('mm', True, False),
        'pitch'      : fc.KWSpec('mm', True, False),
        'span'       : fc.KWSpec('mm', True, False),
        'pkglen'     : fc.KWSpec('mm', True, False),
        'thermal'    : fc.KWSpec('mm', False, True),
        'thermalexp' : fc.KWSpec('mm', False, True),
        'vias'       : fc.KWSpec(None, False, True),
        'viadrill'   : fc.KWSpec('mm', False, False),
        'clearance'  : fc.KWSpec('mm', False, False),
        'mask'       : fc.KWSpec('mm', False, False),
    }
    @classmethod
    def helptext(cls):
        yield "SO, TSSOP, HSOP family."
        yield "  Default dimensions are mm."
        yield "  pins=<n> -- number of gull-wing pins."
        yield "  padlen=<dim> -- length of pin pads."
        yield "  padwidth=<dim> -- width of pin pads."
        yield "  pitch=<dim> -- distance between pin centerlines."
        yield "  span=<dim>  -- wing-span of pin pads, tip-to-tip."
        yield "  pkglen=<dim>  -- length of packgage (for silk)."
        yield "  thermal=<width>,<length> -- thermal pad, assigned number <pins>+1."
        yield "  thermalexp=<width>,<length> -- thermal pad exposure."
        yield '  vias=<nw>,<nl>[,s] -- number of vias across width/length/stagger.'
        yield "  viadrill=<dim>  -- drill size for vias."
        yield "  clearance=<dim> -- optional pad clearance."
        yield "  mask=<dim> -- optional mask relief."
    @classmethod
    def parse(cls, footprintname, params, rules, rack, warningcallback):
        kw = cls.parseKwargs(params, cls.kw_specs)
        if kw['pins'] % 2:
            raise fc.ParamSyntax('Must have even number of pins.')
        return cls.fromKwargs(footprintname, rules, rack, warningcallback, **kw)
    @classmethod
    def fromKwargs(cls, footprintname, rules, rack, warningcallback, **kw):
        # Make pin pad.
        try:
            mask = kw['mask']
        except KeyError:
            mask = rules['maskrelief']
        try:
            clear = kw['clearance']
        except KeyError:
            clear = rules['minspace']
        padlen = kw['padlen']
        padwidth = kw['padwidth']
        ur = fc.Pt(padlen/2.0, padwidth/2.0)
        ll = - ur
        pad = cls.rectPad(ll, ur, clear, mask)
        pingeo = cls.pinGeometry(pad)
        # Make pins.
        pinx = (kw['span']-padwidth)/2.0
        pitch = kw['pitch']
        numpins = int(kw['pins'])
        pins = cls.dil_geometry(numpins, kw['span']-padwidth, pitch, pingeo)
##        t = [x+1 for x in range(0,numpins/2)]
##        y = ((numpins/2) - 1) * pitch/2.0
##        leftpins = [] 
##        for pin in t:
##            leftpins.append((pin, fc.Pt(-pinx, y)))
##            y -= pitch
##        rightpins = [((numpins-pin)+1, fc.Pt(pinx, loc.y)) for pin, loc in leftpins]
##        leftpins.extend(rightpins)
##        pins = [cls.pinSpec(loc, num, pingeo) for num, loc in leftpins]
        # Make thermal pad.
        thermal_cu = cls._thermal_rect('thermal',**kw)
        if thermal_cu:
            thermal_antimask = cls._thermal_rect('thermalexp',**kw)
            thermal_drills = cls._drill_field(thermal_cu[0],**kw)
            if not thermal_antimask:
                warningcallback('No thermal anti-mask specified.')
            t = cls.thermalSink(fc.Pt.MM(0,0), thermal_cu, [thermal_antimask],
                               [],[], # nothing on solder side
                                thermal_drills,
                                numpins+1,'THRM')
            pins.append(t)
            
        # Make silk -- be sure it doesn't run into thermal anti-mask.
        pkglen = kw['pkglen']
        silkwidth = rules['minsilk']
        silkx = (kw['span']/2.0-padlen)-silkwidth
        silk = []
        silky = pkglen/2.0
        ur = fc.Pt(silkx,silky)
        lr = fc.Pt(silkx,-silky)
        ll = fc.Pt(-silkx, -silky)
        ul = fc.Pt(-silkx, silky)
        silk.append(cls.silkLine(ur,lr,silkwidth))
        silk.append(cls.silkLine(lr,ll,silkwidth))
        silk.append(cls.silkLine(ll,ul,silkwidth))
        silk.append(cls.silkLine(ul,ur,silkwidth))
        silk.append(cls.silkArc(fc.Pt.x0y(silky),silkx/5.0,0,180,silkwidth))
        # Comments
        cmt = cls.standardComments(cls.__name__.split('_')[2],
            kw, rules,
            ['maskrelief','minspace','minsilk','refdessize'])
        # refdes
        # FIXME: move off below part
        rd = cls.refDes(fc.Pt.MM(0,0),0,rules['minsilk'],'',rules['refdessize'])
        return cls(footprintname, '', rd, pins, silk, cmt)
    @classmethod
    def _thermal_rect(cls, keyword, **kw):
        try:
            t = kw[keyword]
        except KeyError:
            return []
        else:
            try:
                thermw, therml = t
            except ValueError:
                raise fc.ParamSyntax(
                    'Expected width,length for thermal feature: ' + keyword)
            else:
                thermw,therml = (thermw,therml) if thermw < therml \
                                else (therml, thermw)
                x,y = thermw/2.0, therml/2.0
                # Return lower-left as first point.
                rect = [fc.Pt(a,b) for a,b in [(-x,-y),(-x,y),(x,y),(x,-y)]]
                return rect
    @classmethod
    def _drill_field(cls, lower_left, **kw):
        try:
            v = kw['vias']
        except KeyError:
            return []
        try:
            sz = kw['viadrill']
        except KeyError:
            raise fc.ParamSyntax('No via drill specified.')
        try:
            v.append(False)
            #print 'v:',repr(v)
            nw, nl, stagger = v[0:3]
        except ValueError:
            raise fc.ParamSyntax('Expected width,length count for drill field.')
        nw,nl,stagger = int(nw),int(nl),bool(stagger)
        nw,nl = (nw,nl) if nw < nl else (nl,nw)
##        thermw = min(kw['thermal'])
##        therml = max(kw['thermal'])
        thermw,therml = kw['thermal']
        lenstep = fc.Pt.x0y(therml/nl)
        widthstep = fc.Pt.xy0(thermw/nw)
        #print 'tw,ws,tl,ls:',thermw,widthstep,therml,lenstep
        xoffset = widthstep/2.0
        yoffset = lenstep/2.0
        #print 'xo,yo:',xoffset,yoffset
        drill_locs = []
        colstart = lower_left + xoffset + yoffset
        #print 'll,colstart:',lower_left, colstart
        for i in xrange(0,nw):
            loc = colstart + yoffset if stagger and i%2 else colstart
            for j in xrange(0,(nl-1) if stagger and i%2 else nl):
                drill_locs.append(loc)
                loc += lenstep
            colstart += widthstep
        return [(loc, sz) for loc in drill_locs]
        
        
        
