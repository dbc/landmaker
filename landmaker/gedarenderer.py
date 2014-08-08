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

import os
from collections import namedtuple
# Import the plug-in core.
import footprintcore as fc

def box(ll,ur):
    "Make (ur,ul,ll,lr) tuple from (ll,ur)"
    return (ur, fc.Pt(ur.x, ll.y), ll, fc.Pt(ll.x, ur.y))

# Define primitive rendering for gEDA.

pin_format_str = ('Pin[{x:d} {y:d} {dia:d} {clear:d} {mask:d} {drill:d} ' +
    '"{pname:s}" "{pnum:d}" "{tflags:s}"]')

pad_format_str = ('Pad[{x1:d} {y1:d} {x2:d} {y2:d} {width:d} ' +
    '{clear:d} {mask:d} "{name:s}" "{num:d}" "{tflags:s}"]')

##class RenderPadBase(object):
##    def smtPad(self, p1, p2, width, clearance, mask_width, name, num, flags):
##        return pad_format_str.format( \
##            x1=p1.x.gu, y1=-p1.y.gu, # end 1 \
##            x2=p2.x.gu, y2=-p1.y.gu, # end 2 \
##            width=width.gu,
##            clear=(clearance*2.0).gu,
##            mask=mask_width.gu,
##            name=name,
##            num=num,
##            tflags=flags)

class GedaSimpleAperture(object):
    @property
    def is_simple_pin(self):
        return False
    @property
    def is_simple_pad(self):
        return False
    
class Geda_SACircle(fc.SACircle, GedaSimpleAperture):
    @property
    def is_simple_pin(self):
        return True
    @property
    def thickness(self):
        return self.diameter
    @property
    def tflags(self):
        return ''

class GedaSARectangular(GedaSimpleAperture):
    @property
    def thickness(self):
        return min([self.xsize, self.ysize])
    @property
    def is_simple_pad(self):
        return True
    def format_pad(self, pin_spec, land, mask, onsolder=False):
        loc = pin_spec.loc + land.loc
        if self.xsize > self.ysize:
            lenby2 = (self.xsize - self.ysize)/2.0
            x1,x2 = loc.x.minus_plus(lenby2)
            width = self.ysize
            y1,y2 = loc.y, loc.y
        else:
            lenby2 = (self.ysize - self.xsize)/2.0
            y1,y2 = loc.y.minus_plus(lenby2)
            width = self.xsize
            x1,x2 = loc.x, loc.x
        flags = ''.join([self.tflags, 'onsolder' if onsolder else ''])
        return pad_format_str.format(
            x1=x1.gu, y1=-y1.gu, x2=x2.gu, y2=-y2.gu, width=width.gu,
            clear=(land.clearance*2.0).gu,
            mask=mask.width.gu,
            name=pin_spec.name,
            num=pin_spec.num,
            tflags=flags)
    
class Geda_SARectangle(fc.SARectangle, GedaSARectangular):
    @property
    def is_simple_pin(self):
        return self.is_square
    @property
    def tflags(self):
        return 'square'

class Geda_SAObround(fc.SAObround, GedaSARectangular):
    @property
    def tflags(self):
        return ''

class Geda_SAPolygon(fc.SAPolygon, GedaSimpleAperture):
    pass

class GedaCantDo(object):
    def __init__(self, *args, **kwargs):
        raise CanNotRenderError(''.join([self.__class__.__name__, ' in gEDA/PCB.']))

class Geda_MPComment(GedaCantDo):
    pass

class Geda_MPCircle(GedaCantDo):
    pass

class Geda_MPVectorLine(GedaCantDo):
    pass

class Geda_MPCenterLine(GedaCantDo):
    pass

class Geda_MPLowerLeftLine(GedaCantDo):
    pass

class Geda_MPOutline(GedaCantDo):
    pass

class Geda_MPPolygon(GedaCantDo):
    pass

class Geda_MPMoire(GedaCantDo):
    pass

class Geda_MPThermal(GedaCantDo):
    pass

class Geda_ApertureMacro(GedaCantDo):
    pass

class Geda_PlatedDrill(fc.PlatedDrill):
    pass

class Geda_PlatedSlot(GedaCantDo):
    pass

class Geda_Land(fc.Land):
    @property
    def is_simple_pin(self):
        return self.aperture.is_simple_pin
    @property
    def is_simple_pad(self):
        return self.aperture.is_simple_pad

class Geda_DrawnMask(fc.DrawnMask):
    @property
    def is_derived(self):
        return False

class Geda_DerivedMask(fc.DerivedMask):
    @property
    def is_derived(self):
        return True
    @property
    def width(self):
        return self.bloat*2.0 + self.base.aperture.thickness 

class Geda_NoMask(fc.NoMask):
    @property
    def width(self):
        return fc.Dim.MM(0)

class Geda_DrawnPaste(fc.DrawnPaste):
    pass

class Geda_DerivedPaste(fc.DerivedPaste):
    pass

class Geda_NoPaste(fc.NoPaste):
    pass

##class Geda_RoundPad(RenderPadBase, fc.RoundPad):
##    @property
##    def square(self):
##        return False
##    @property
##    def pad_radius(self):
##        return self.dia/2.0
##    def tFlags(self, side = 'c'):
##        assert side in 'cs'
##        return 'onsolder' if side == 's' else ''
##    def rendering(self, loc, num, name='', side='c'):
##        yield self.smtPad(loc, loc, self.dia, self.clearance, \
##                          self.mask_relief*2.0+self.dia,
##                          name if name else str(num),
##                          num, 
##                          self.tFlags(side))
##
##class Geda_SquarePad(fc.SquarePad):
##    @property
##    def square(self):
##        return True
##    def tFlags(self, side = 'c'):
##        assert side in 'cs'
##        return 'square,onsolder' if side == 's' else 'square'
##    def rendering(self, loc, num, name='', side='c'):
##        # FIXME: Round,Square can use same code.
##        yield self.smtPad(loc, loc, self.width, self.clearance, \
##                          self.mask_relief*2.0+self.width,
##                          name if name else str(num),
##                          self.tFlags(side))
##
##class RenderRect_Base(RenderPadBase):
##    @property
##    def width(self):
##        xd = self.ur.x - self.ll.x
##        yd = self.ur.y - self.ll.y
##        return min([xd, yd])
##    @property
##    def pad_radius(self):
##        radius = self.width/2.0
##        assert radius > 0.0
##        return radius
##    def rendering(self, loc, num, name='', side='c'):
##        radius = self.pad_radius
##        radOffset = fc.Pt(radius,radius)
##        p1 = (self.ll + radOffset) + loc
##        p2 = (self.ur - radOffset) + loc
##        yield self.smtPad(p1, p2, self.width, self.clearance, \
##                          self.mask_relief*2.0 + self.width,
##                          name if name else str(num),
##                          num, 
##                          self.tFlags(side))            
##        
##class Geda_RectPad(RenderRect_Base,fc.RectPad):
##    def tFlags(self, side='c'):
##        assert side in 'cs'
##        return 'square,onsolder' if side=='s' else 'square'
##
##class Geda_RoundedRectPad(RenderRect_Base,fc.RoundedRectPad):
##    def tFlags(self, side='c'):
##        assert side in 'cs'
##        return 'onsolder' if side=='s' else ''
            

# landmaker pins get classified for rendering to pcb footprint files
# according to the rendering strategy needed for each pin flavor.
PinClassifiers = namedtuple('PinClassifiers', 
        'drilled simple symmetric topOnly botOnly')

##class Geda_PinGeometry(fc.PinGeometry):
##    def classify(self):
##        "Returns classification for selecting rendering method."
##        drilled = self.drill != None
##        simple = drilled \
##            and self.symmetric \
##            and (isinstance(self.comp_pad, fc.RoundPad) \
##                or isinstance(self.comp_pad, fc.SquarePad))
##        if 'c' in fc.debug:
##            print 'comp_pad:',repr(self.comp_pad),self.solder_pad is None
##        topOnly = (not self.symmetric) and (self.solder_pad is None)
##        botOnly = (not self.symmetric) and (self.comp_pad is None)
##        return PinClassifiers(drilled, simple, self.symmetric, topOnly, botOnly)


class Geda_ThruPin(fc.ThruPin):
    def rendering(self, pin_spec, warning_callback):
        # FIXME: Handle plated slots. Make Geda_PlatedSlot behave like drill? Issue warning.
        if not self.solder_mask.is_derived:
            raise fc.CanNotRenderError('Can only render derived masks for ThruPin.')
        if self.symmetric and self.solder_land.is_simple_pin:
            yield pin_format_str.format(
                x=pin_spec.loc.x.gu, y=-pin_spec.loc.y.gu,
                dia=self.solder_land.aperture.diameter.gu,
                clear=(self.solder_land.clearance*2.0).gu,
                mask=self.solder_mask.width.gu,
                drill=self.hole.diameter.gu,
                pname=pin_spec.name,
                pnum=pin_spec.num,
                tflags=self.solder_land.aperture.tflags)
        else:
            pin_dia = min([self.solder_land.aperture.thickness,
                           self.comp_land.aperture.thickness])
            pin_mask = min([self.solder_mask.width, self.comp_mask.width])
            clearance = min([self.solder_land.clearance,
                             self.comp_land.clearance])
            yield pin_format_str.format(
                x=pin_spec.loc.x.gu, y=-pin_spec.loc.y.gu,
                dia=pin_dia.gu,
                clear=(clearance*2.0).gu,
                mask=pin_mask.gu,
                drill=self.hole.diameter.gu,
                pname=pin_spec.name,
                pnum=pin_spec.num,
                tflags='')
            if self.comp_land.aperture.thickness != pin_dia \
              or not self.comp_land.aperture.is_simple_pin:
                if 'c' in fc.debug:
                    yield '# Draw top pad.'
                yield '# <top pad>'
            if self.solder_land.aperture.thickness != pin_dia \
              or not self.solder_land.aperture.is_simple_pin:
                if 'c' in fc.debug:
                    yield '# Draw bottom pad.'
                yield self.solder_land.aperture.format_pad(
                    pin_spec, self.solder_land, self.solder_mask, True)
 
class Geda_SMTPad(fc.SMTPad):
    def rendering(self, pin_spec, warning_callback):
        if not self.mask.is_derived:
            # FIXME: Need to handle ganged mask.
            # 1. Collect pads in the gang.
            # 2. Analyze geometry of pads in the gang
            # 3. Create mask control pads define the gang aperture
            # 4. Render the regular pads also.
            raise fc.CanNotRenderError('Can only render derived masks for SMTPad.')
        if not self.land.is_simple_pad:
            raise fc.CanNotRenderError('Can only render simple SMTPad.')
        yield self.land.aperture.format_pad(
            pin_spec, self.land, self.mask)
##        ap = self.land.aperture
##        loc = pin_spec.loc
##        if ap.xsize > ap.ysize:
##            lenby2 = (ap.xsize - ap.ysize)/2.0
##            x1,x2 = loc.x.minus_plus(lenby2)
##            width = ap.ysize
##            y1,y2 = loc.y, loc.y
##        else:
##            lenby2 = (ap.ysize - ap.xsize)/2.0
##            y1,y2 = loc.y.minus_plus(lenby2)
##            width = ap.xsize
##            x1,x2 = loc.x, loc.x
##        # FIXME: Delegate to Geda_Land()
##        yield pad_format_str.format(
##            x1=x1.gu, y1=y1.gu, x2=x2.gu, y2=y2.gu, width=width.gu,
##            clear=(self.land.clearance*2.0).gu,
##            mask=self.mask.width.gu,
##            name=pin_spec.name,
##            num=pin_spec.num,
##            tflags=self.land.aperture.tflags)

class Geda_ThermalPolygon(fc.ThermalPolygon):
    def rendering(self, pin_spec, warning_callback):
        zero = fc.Dim.MM(0)
        yield '# thermal pad'
        yield self.land.aperture.format_pad(
            pin_spec, self.land, Geda_NoMask())
        for m in self.masks:
            yield m.aperture.format_pad(
                pin_spec, Geda_Land(
                    zero, m.aperture, fc.Pt.MM(0,0)),
                Geda_DerivedMask(m, zero))
        for h in self.holes:
            paddia = h.diameter + fc.Dim.MIL(20)
            yield pin_format_str.format(
                x=h.offset.x.gu, y=h.offset.y.gu, dia=paddia.gu,
                clear=(self.land.clearance*2.0).gu, mask=zero.gu,
                drill=h.diameter.gu,
                pname=pin_spec.name, pnum=pin_spec.num, tflags="")
        yield '# end thermal pad'

pin_format_str = ('Pin[{x:d} {y:d} {dia:d} {clear:d} {mask:d} {drill:d} ' +
    '"{pname:s}" "{pnum:d}" "{tflags:s}"]')


class Geda_PinSpec(fc.PinSpec):
    def rendering(self, warning_callback):
        for ln in self.geo.rendering(self, warning_callback):
            yield ln
            
##        # pcb's notion of pins/pads don't map well to landmaker logic.
##        # Instead of delegating rendering to sub-primitives, delegation
##        # stops here and this method walks the sub-primitive properties.
##        cl = self.geo.classify()
##        if 'c' in fc.debug:
##            yield '# pin ' + str(self.num)
##            yield '# classifiers: ' + repr(cl)
##        if cl.drilled and cl.simple and cl.symmetric:
##            # These map directly to Pin[] elements.
##            p = self.geo.comp_pad
##            # FIXME: make RenderingPin classs to handle Pin[] cases.
##            yield 'Pin[{x:d} {y:d} {dia:d} {clear:d} {mask:d} {drill:d} "{pname:s}" "{pnum:d}" "{tflags:s}"]'.format( \
##                x=self.loc.x.gu, y=-self.loc.y.gu,  # x,y relative to mark \
##                dia=p.dia.gu,  # pad diameter \
##                clear=(p.clearance * 2.0).gu,  # Cu clearance \
##                mask=(p.dia + 2.0*p.mask_relief).gu,  # Diameter of mask anti-pad \
##                drill=self.geo.drill.gu,  # Drill diameter \
##                pname=self.name,  # pin name \
##                pnum=self.num,  # pin number \
##                tflags='square' if p.square else '')
##        elif cl.topOnly and not cl.drilled:
##            # These map directly to ordinary Pad[] elements.
##            if 'r' in fc.debug:
##                yield '# <render a normal SMT pad>'
##            for ln in self.geo.comp_pad.rendering(self.loc, self.num, self.name):
##                yield ln
##        elif cl.drilled and not cl.simple:
##            # These require obscure jiggery-pokery in pcb.
##            yield '# complex drilled pad for pin #{0:d}'.format(self.num)
##            # First, compute a pcb Pin[] element to hold the drill info,
##            # and select a pad diameter that is <= either top or
##            # bottom extents.
##            radius = min([self.geo.solder_pad.pad_radius, self.geo.comp_pad.pad_radius])
##            yield 'Pin[{0:d} {1:d} {2:d} {3:d} {4:d} {5:d} "{6:s}" "{7:d}" "{8:s}"]'.format( \
##                self.loc.x.gu, -self.loc.y.gu,  # x,y relative to mark \
##                (2.0*radius).gu, # pad diameter \
##                0, # Cu clearance comes from Pad[] \
##                0, # mask relief comes from Pad[] \
##                self.geo.drill.gu,  # Drill diameter \
##                self.name,  # pin name \
##                self.num,  # pin number \
##                '')  # no flags
##            # Now put down the pads on each side of the board.
##            for ln in self.geo.comp_pad.rendering(self.loc, self.num, self.name):
##                yield ln
##            for ln in self.geo.solder_pad.rendering(self.loc, self.num, self.name,'s'):
##                yield ln
##        elif not cl.drilled and not (cl.topOnly or cl.botOnly):
##            # This is most likely an edge connector.
##            yield '# <render edge connector (or similar).'
##        else:
##            yield '# pin {0:d} not yet handled: {1:s}'.format(self.num,repr(cl))

##class Geda_ThermalSink(fc.ThermalSink):
##    _not_rectangle = 'Can only render rectanglular thermal pads for now.'
##    def rendering(self, warning_callback):
##        # FIXME: add the clearance property correctly.
##        self.clearance = fc.Dim.MIL(8)
##        yield '# <render thermal sink here>'
##        # Component side copper polygon.
##        yield '# comp cu polygon'
##        for pt in self.comp_cu:
##            yield '# ' + str(pt)
##        if self.comp_cu:
##            if len(self.comp_cu) != 4:
##                raise fc.CanNotRenderError(self._not_rectangle + '(comp cu)')
##            yield self._rectangle_to_pad(self.comp_cu)
##        # Component side anti-mask polygons.
##        yield '# comp anti-mask polygons'
##        for gon in self.comp_mask:
##            if gon:
##                yield '#  mask clearance polygon'
##                for pt in gon:
##                    yield '# ' + str(pt)
##                yield self._rectangle_to_pad(gon, True)
##        yield '# solder cu polygon'
##        for pt in self.solder_cu:
##            yield '# ' + str(pt)
##        if self.solder_cu:
##            if len(self.solder_cu) != 4:
##                raise fc.CanNotRenderError(self._not_rectangle + '(solder cu)')
##            yield self._rectangle_to_pad(self.solder_cu)
##        yield '# solder side anti-mask polygons'
##        for gon in self.solder_mask:
##            if gon:
##                yield '# mask clearance polygon'
##                for pt in gon:
##                    yield '# ' + str(pt)
##                yield self._rectangle_to_pad(gon, True)  
##        yield '# Drills'
##        for loc,size in self.drills:
##            yield ' '.join(['#', str(loc),',',str(size)])
##            # FIXME: pad diameter is a bit of a kludge here.
##            yield pin_format_str.format(x=loc.x.gu, y=-loc.y.gu,
##                dia=(size+fc.Dim.MIL(20)).gu, clear=self.clearance.gu, mask=0,
##                drill=size.gu, pname='',pnum=self.num,tflags='')
##        yield '# ^^ end thermal sink'
##    def _rectangle_to_pad(self, polygon, antimask=False):
##        "Returns Pad[] for aRect."
##        p1, p2, width = self._rect_to_points_width(polygon)
##        p1 += self.loc
##        p2 += self.loc
##        return pad_format_str.format(
##            x1=p1.x.gu, y1=-p1.y.gu,
##            x2=p2.x.gu, y2=-p2.y.gu,
##            width=width.gu,
##            clear=0 if antimask else self.clearance.gu,
##            mask=width.gu if antimask else 0,
##            name=self.name,
##            num=self.num,
##            tflags="square")
##    def _rect_to_points_width(self, aRect):
##        "Convert points of a rectangle to geda-style end points + width."
##        p1,p2,p3,p4 = aRect
##        if not (p1.orthonormal(p2) and p2.orthonormal(p3) and
##                p3.orthonormal(p4) and p4.orthonormal(p1)):
##            raise fc.CanNotRenderError(self._not_rectangle)
##        if p1.dist(p2) < p2.dist(p3): # Could do this test more cheaply.
##            c1,c2 = p2.rectify(p4)
##        else:
##            c1,c2 = p1.rectify(p3)
##        t = c2-c1
##        width = min([t.x,t.y])
##        assert width != 0
##        offset = fc.Pt(width/2.0,width/2.0)
##        return (c1+offset, c2-offset, width)
##                    
##class Geda_PinGang(fc.PinGang):
##    def rendering(self, warning_callback):
##        yield '# <render ganged pins here>'
        
class Geda_SilkText(fc.SilkText):
    def rendering(self, warning_callback):
        msg = 'Arbitrarily placed SilkText not supported by pcb. (0:%s)'.format(self.text)
        warning_callback(msg)
        yield '# ' + msg

class Geda_SilkLine(fc.SilkLine):
    def rendering(self, warning_callback):
        # landmaker SilkLine maps directly to ElementLine[] element.
        s = 'ElementLine['
        params = [self.loc.x, -self.loc.y, self.p2.x, -self.p2.y, self.pen_width]
        s += ' '.join([str(param.gu) for param in params])
        s += ']'
        yield s

class Geda_SilkArc(fc.SilkArc):
    def rendering(self, warning_callback):
        # landmaker SilkArc maps directly to ElementArc[] element.
        # Truth be told, pcb's ElementArc[] allows the specification of
        # eliptical arcs (and landmaker does not). HOWEVER: pcb can't
        # correctly do arbitrary rotation of eliptical arcs, and since
        # RS-274X does not support an eliptical arc pcb's gerber back-end
        # renders eliptical arcs as a line segment approximation.
        # So... let's simply not do eliptical arcs at all.
        yield '# <silk arc>' # FIXME


class Geda_KeepOutRect(fc.KeepOutRect):
    def rendering(self, warning_callback):
        yield '# Keep Out'
        # pcb does not directly support keep-outs.
        # Construct some silk lines and render the keep-out area that way.'
        pen = fc.Dim.MIL(10) # FIXME: remove hard=coded silk width, use rule.
        # Silk line has some width, so offset the lines into the keep-out area.
        half_pen = pen/2.0
        offset = fc.Pt(half_pen, half_pen)
        s = []
        # Make a box.
        ur,ul,ll,lr = box(self.ll,self.ur)
        s.append(Geda_SilkLine(ll,lr,pen))
        s.append(Geda_SilkLine(lr,ur,pen))
        s.append(Geda_SilkLine(ur,ul,pen))
        s.append(Geda_SilkLine(ul,ll,pen))
        # Put an X in the box.
        s.append(Geda_SilkLine(ll,ur,pen))
        s.append(Geda_SilkLine(ul,lr,pen))
        # render the silk
        for silk in s:
            for ln in silk.rendering(warning_callback):
                yield ln

# Define footprint-level gEDA renderer.
class Geda_Footprint(object):
    # Standard Apertures, gEDA/PCB supports mostly.
    saCircle = Geda_SACircle
    saRectangle = Geda_SARectangle
    saObround = Geda_SAObround
    saPolygon = Geda_SAPolygon
    # Aperture Macros, no support in gEDA/PCB
    mpComment = Geda_MPComment
    mpCircle = Geda_MPCircle
    mpVectorLine = Geda_MPVectorLine
    mpCenterLine = Geda_MPCenterLine
    mpLowerLeftLine = Geda_MPLowerLeftLine
    mpOutline = Geda_MPOutline
    mpPolygon = Geda_MPPolygon
    mpMoire = Geda_MPMoire
    mpThermal = Geda_MPThermal
    apertureMacro = Geda_ApertureMacro
    # Masks
    drawnMask = Geda_DrawnMask
    derivedMask = Geda_DerivedMask
    noMask = Geda_NoMask
    # Plated holes
    platedDrill = Geda_PlatedDrill
    platedSlot = Geda_PlatedSlot
    # Paste
    drawnPaste = Geda_DrawnPaste
    derivedPaste = Geda_DerivedPaste
    noPaste = Geda_NoPaste
    # Landmaker primitives
    land = Geda_Land
    thruPin = Geda_ThruPin
    smtPad = Geda_SMTPad
    thermalPolygon = Geda_ThermalPolygon
    pinSpec = Geda_PinSpec
    silkText = Geda_SilkText # No such beast in gEDA except for refdes.
    silkLine = Geda_SilkLine
    silkArc = Geda_SilkArc
    keepOutRect = Geda_KeepOutRect
    _indent = '    '
    def rendering(self, warning_callback):
        # Construct the Element[...] line.
        sflags = ''
        # Initial placement location -- 10 mils from corner for now.
        # FIXME: Compute based on extents.
        markX = 1000
        markY = 1000
        # Construct refdes parameters.
        # refdes scaling in gEDA is % of default size, which is 40 mils.
        # FIXME: Throw warnings on questionable values.
        textScale = int((self.refdes.size / fc.Dim.MIL(40)) * 100.0)
        textFlags = ''
        textRot = int((self.refdes.rot %360.0) / 90.0)
        yield 'Element["{sflags:s}" "" "" "" {markx:d} {marky:d} {refdesx:d} {refdesy:d} {trot:d} {tscale:d} "{tflags:s}"]'.format( \
            sflags=sflags, markx=markX, marky=markY,
            refdesx=self.refdes.loc.x.gu, refdesy=self.refdes.loc.y.gu, \
            trot=textRot, tscale=textScale, tflags=textFlags)
        yield '('
        # Render comments.
        if self.desc != '':
            yield '# '.join([self._indent, self.desc])
        for ln in self.comments:
            yield '# '.join([self._indent, ln])
        for pin in self.pins:
            for ln in pin.rendering(warning_callback):
                yield self._indent + ln
        for art in self.silk:
            for ln in art.rendering(warning_callback):
                yield self._indent + ln
        # Render keep-outs
        for ko in self.keepOuts:
            for ln in ko.rendering(warning_callback):
                yield self._indent + ln
        # All done!
        yield ')'

# Define the rendering plug-ins for gEDA.
# Rendering plug-ins all have names in the form:
#  <cad system>_FP_<plug-in name>
# example: Geda_FP_so

foundPlugins = fc.reconnoiterPlugins()
fc.importPlugins(foundPlugins, globals(), locals())

# Any rendering classes that must be manually defined should
# be declared here before calling deriveRenderingClasses().

fc.deriveRenderingClasses(foundPlugins, 'Geda', Geda_Footprint, globals())
fp_plugins = fc.collectPlugins(globals())

if __name__ == '__main__':
    pass


