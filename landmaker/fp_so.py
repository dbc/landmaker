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
    kwspecs = {
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
    def parse(cls, footprintname, params, rules, rack, warning_callback):
        kw = cls.parse_kwargs(params, cls.kwspecs)
        if kw['pins'] % 2:
            raise fc.ParamSyntax('Must have even number of pins.')
        return cls.from_kwargs(footprintname, rules, rack, warning_callback, **kw)
    @classmethod
    def from_kwargs(cls, footprintname, rules, rack, warning_callback, **kw):
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
        pingeo = cls.smtPad.obround(clear, padlen, padwidth, mask)
        # Make pins.
        pinx = (kw['span']-padwidth)/2.0
        pitch = kw['pitch']
        numpins = int(kw['pins'])
        pins = cls.dil_geometry(numpins, kw['span']-padwidth, pitch, pingeo)
        # Make thermal pad.
        try:
            thermal_cu = kw['thermal']
        except:
            thermal_cu = None
        if thermal_cu:
            print thermal_cu
            cu_x, cu_y = thermal_cu
            cu_ur = fc.Pt(cu_x/2.0, cu_y/2.0)
            cu_ll = -cu_ur
            thermal_antimask = kw['thermalexp']
            if thermal_antimask:
                mask_x, mask_y = thermal_antimask
                mask_ur = fc.Pt(mask_x/2.0, mask_y/2.0)
                mask_ll = -mask_ur
            else:
                mask_ll, mask_ur = None,None
                warning_callback('No thermal anti-mask specified.')
            #thermal_drills = cls._drill_field(thermal_cu[0],**kw)
            thermal_drills = kw['vias']
            if thermal_drills:
                x_drills, y_drills = (int(x) for x in thermal_drills)
                p0 = cu_ll + fc.Pt(cu_x/(2.0 * x_drills), cu_y/(2.0 * y_drills))
                p1 = p0 + fc.Pt(cu_x/x_drills, cu_y/y_drills)
                drill_points = fc.Pt.point_array(p0,p1,(x_drills, y_drills)) # FIXME: Lame error checking.
            else:
                drill_points = []
            print 'drill points',drill_points
            drill_size = kw['viadrill']
            t = cls.thermalPolygon.rectangle(
                clear, cu_ll, cu_ur, mask_ll, mask_ur,
                drill_size, drill_points)
            pins.append(cls.pinSpec(fc.Pt.MM(0,0), numpins+1, t, 0, 'THRM' ))
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
        cmt = cls.standard_comments(cls.__name__.split('_')[2],
            kw, rules,
            ['maskrelief','minspace','minsilk','refdessize'])
        # refdes
        # FIXME: move off below part
        rd = cls.refDes(fc.Pt.MM(0,0),0,rules['minsilk'],'',rules['refdessize'])
        return cls(footprintname, '', rd, pins, silk, cmt)
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
        
        
        
