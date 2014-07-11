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

class RenderPadBase(object):
    padFormatStr = 'Pad[{x1:d} {y1:d} {x2:d} {y2:d} {width:d} ' \
            +'{clear:d} {relief:d} "{name:s}" "{num:d}" "{tflags:s}"]'
    def smtPad(self, p1, p2, width, clearance, mask_width, name, num, flags):
        return self.padFormatStr.format( \
            x1=p1.x.gu, y1=-p1.y.gu, # end 1 \
            x2=p2.x.gu, y2=-p1.y.gu, # end 2 \
            width=width.gu,
            clear=(clearance*2.0).gu,
            relief=mask_width.gu,
            name=name,
            num=num,
            tflags=flags)

class Geda_RoundPad(RenderPadBase, fc.RoundPad):
    @property
    def square(self):
        return False
    @property
    def padRadius(self):
        return self.dia/2.0
    def tFlags(self, side = 'c'):
        assert side in 'cs'
        return 'onsolder' if side == 's' else ''
    def rendering(self, loc, num, name='', side='c'):
        yield self.smtPad(loc, loc, self.dia, self.clearance, \
                          self.maskRelief*2.0+self.dia,
                          name if name else str(num),
                          num, 
                          self.tFlags(side))
##    def smtPad(self, x, y, num, name='', side='c'):
##        yield 'Pad[{0:d} {1:d} {2:d} {3:d} {4:d} {5:d} {6:d} "{7:s}" "{8:d}" "{9:s}"]'.format(\
##            x.gu, y.gu, # x,y of end 1 \
##            x.gu, y.gu, # x,y of end 2 \
##            self.dia.gu, # width of stripe \
##            (2.0*self.clearance).gu, \
##            (2.0*+self.relief+self.dia).gu, \
##            name, \
##            num, \
##            self.tFlags(side))

class Geda_SquarePad(fc.SquarePad):
    @property
    def square(self):
        return True
##    @property
##    def dia(self):
##        return self.width # A pcb-ism. This hack simplifies Pin[] rendering.
    def tFlags(self, side = 'c'):
        assert side in 'cs'
        return 'square,onsolder' if side == 's' else 'square'
    def rendering(self, loc, num, name='', side='c'):
        # FIXME: Round,Square can use same code.
        yield self.smtPad(loc, loc, self.width, self.clearance, \
                          self.maskRelief*2.0+self.width,
                          name if name else str(num),
                          self.tFlags(side))
##    def smtPad(self, x, y, num, name='',  side='c'):
##        assert side in 'cs'
##        return '# <SquarePad as SMT>'

class RenderRect_Base(RenderPadBase):
    @property
    def width(self):
        xd = self.ur.x - self.ll.x
        yd = self.ur.y - self.ll.y
        return min([xd, yd])
    @property
    def padRadius(self):
        radius = self.width/2.0
        assert radius > 0.0
        return radius
##    @property
##    def orientation(self):
##        xd = self.ur.x-self.ll.x
##        yd = self.ur.y-self.ll.y
##        return 'h' if xd > yd else 'v'
    def rendering(self, loc, num, name='', side='c'):
        radius = self.padRadius
        radOffset = fc.Pt(radius,radius)
        p1 = (self.ll + radOffset) + loc
        p2 = (self.ur - radOffset) + loc
        yield self.smtPad(p1, p2, self.width, self.clearance, \
                          self.maskRelief*2.0 + self.width,
                          name if name else str(num),
                          num, 
                          self.tFlags(side))            
##        if self.orientation == 'h':
##            # horizontal
##            x1 = (self.x1 + radius) + x
##            x2 = (self.x2 - radius) + x
##            y1 = y
##            y2 = y
##        else:
##            # vertical
##            x1 = x
##            x2 = x
##            y1 = (self.y1+radius) + y
##            y2 = (self.y2-radius) + y
##        yield 'Pad[{0:d} {1:d} {2:d} {3:d} {4:d} {5:d} {6:d} "{7:s}" "{8:d}" "{9:s}"]'.format(\
##            x1.gu, y1.gu, # x,y of end 1 \
##            x2.gu, y2.gu, # x,y of end 2 \
##            (2.0*radius).gu, # width of stripe \
##            (2.0*self.clearance).gu, \
##            (2.0*(self.relief+radius)).gu, \
##            name, \
##            num, \
##            self.tFlags(side))
        
class Geda_RectPad(RenderRect_Base,fc.RectPad):
    def tFlags(self, side='c'):
        assert side in 'cs'
        return 'square,onsolder' if side=='s' else 'square'

class Geda_RoundedRectPad(RenderRect_Base,fc.RoundedRectPad):
    def tFlags(self, side='c'):
        assert side in 'cs'
        return 'onsolder' if side=='s' else ''
            

# landmaker pins get classified for rendering to pcb footprint files
# according to the rendering strategy needed for each pin flavor.
PinClassifiers = namedtuple('PinClassifiers', 
        'drilled simple symmetric topOnly botOnly')

class Geda_PinGeometry(fc.PinGeometry):
    def classify(self):
        "Returns classification for selecting rendering method."
        drilled = self.drill != None
        simple = drilled \
            and self.symmetric \
            and (isinstance(self.compPad, fc.RoundPad) \
                or isinstance(self.compPad, fc.SquarePad))
        topOnly = not self.symmetric and self.solderPad == None
        botOnly = not self.symmetric and self.compPad == None
        return PinClassifiers(drilled, simple, self.symmetric, topOnly, botOnly)

class Geda_PinSpec(fc.PinSpec):
    def rendering(self, warningCallback):
        # pcb's notion of pins/pads don't map well to landmaker logic.
        # Instead of delegating rendering to sub-primitives, delegation
        # stops here and this method walks the sub-primitive properties.
        cl = self.geo.classify()
        if 'c' in fc.debug:
            yield '# pin ' + str(self.num)
            yield '# classifiers: ' + repr(cl)
        if cl.drilled and cl.simple and cl.symmetric:
            # These map directly to Pin[] elements.
            p = self.geo.compPad
            # FIXME: make RenderingPin classs to handle Pin[] cases.
            yield 'Pin[{x:d} {y:d} {dia:d} {clear:d} {mask:d} {drill:d} "{pname:s}" "{pnum:d}" "{tflags:s}"]'.format( \
                x=self.loc.x.gu, y=-self.loc.y.gu,  # x,y relative to mark \
                dia=p.dia.gu,  # pad diameter \
                clear=(p.clearance * 2.0).gu,  # Cu clearance \
                mask=(p.dia + 2.0*p.maskRelief).gu,  # Diameter of mask anti-pad \
                drill=self.geo.drill.gu,  # Drill diameter \
                pname=self.name,  # pin name \
                pnum=self.num,  # pin number \
                tflags='square' if p.square else '')
        elif cl.topOnly and not cl.drilled:
            # These map directly to Pad[] elements.
            yield '# <render a normal SMT pad>'
        elif cl.drilled and not cl.simple:
            # These require obscure jiggery-pokery in pcb.
            yield '# complex drilled pad for pin #{0:d}'.format(self.num)
            # First, compute a pcb Pin[] element to hold the drill info,
            # and select a pad diameter that is <= either top or
            # bottom extents.
            radius = min([self.geo.solderPad.padRadius, self.geo.compPad.padRadius])
            yield 'Pin[{0:d} {1:d} {2:d} {3:d} {4:d} {5:d} "{6:s}" "{7:d}" "{8:s}"]'.format( \
                self.loc.x.gu, -self.loc.y.gu,  # x,y relative to mark \
                (2.0*radius).gu, # pad diameter \
                0, # Cu clearance comes from Pad[] \
                0, # mask relief comes from Pad[] \
                self.geo.drill.gu,  # Drill diameter \
                self.name,  # pin name \
                self.num,  # pin number \
                '')  # no flags
            # Now put down the pads on each side of the board.
            for ln in self.geo.compPad.rendering(self.loc, self.num, self.name):
                yield ln
            for ln in self.geo.solderPad.rendering(self.loc, self.num, self.name,'s'):
                yield ln
                

        elif not cl.drilled and not (cl.topOnly or cl.botOnly):
            # This is most likely an edge connector.
            yield '# <render edge connector (or similar).'
        else:
            yield '# pin {0:d} not yet handled: {1:s}'.format(self.num,repr(cl))

class Geda_PinGang(fc.PinGang):
    def rendering(self, warningCallback):
        yield # <render ganged pins here>
        
class Geda_SilkText(fc.SilkText):
    def rendering(self, warningCallback):
        msg = 'Arbitrarily placed SilkText not supported by pcb. (0:%s)'.format(self.text)
        warningCallback(msg)
        yield '# ' + msg

class Geda_SilkLine(fc.SilkLine):
    def rendering(self, warningCallback):
        # landmaker SilkLine maps directly to ElementLine[] element.
        s = 'ElementLine['
        params = [self.loc.x, -self.loc.y, self.p2.x, -self.p2.y, self.penWidth]
        s += ' '.join([str(param.gu) for param in params])
        s += ']'
        yield s

class Geda_SilkArc(fc.SilkArc):
    def rendering(self, warningCallback):
        # landmaker SilkArc maps directly to ElementArc[] element.
        # Truth be told, pcb's ElementArc[] allows the specification of
        # eliptical arcs (and landmaker does not). HOWEVER: pcb can't
        # correctly do arbitrary rotation of eliptical arcs, and since
        # RS-274X does not support an eliptical arc pcb's gerber back-end
        # renders eliptical arcs as a line segment approximation.
        # So... let's simply not do eliptical arcs at all.
        yield '# <silk arc>' # FIXME


class Geda_KeepOutRect(fc.KeepOutRect):
    def rendering(self, warningCallback):
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
        
##        # Silk line has some width, so offset the lines into the keep-out area.
##        offset = pen/2.0
##        ox1 = self.x1 + offset
##        oy1 = self.y1 + offset
##        ox2 = self.x2 - offset
##        oy2 = self.y2 - offset
##        s = []
##        # Make a box
##        s.append(Geda_SilkLine(ox1, oy1, ox1, oy2, pen))
##        s.append(Geda_SilkLine(ox1, oy2, ox2, oy2, pen))
##        s.append(Geda_SilkLine(ox2, oy2, ox2, oy1, pen))
##        s.append(Geda_SilkLine(ox2, oy1, ox1, oy1, pen))
##        # Put an X in the box
##        s.append(Geda_SilkLine(ox1, oy1, ox2, oy2, pen))
##        s.append(Geda_SilkLine(ox1, oy2, ox2, oy1, pen))        
        # render the silk
        for silk in s:
            for ln in silk.rendering(warningCallback):
                yield ln

# Define footprint-level gEDA renderer.
class Geda_Footprint(object):
    roundPad = Geda_RoundPad
    squarePad = Geda_SquarePad
    rectPad = Geda_RectPad
    roundedRectPad = Geda_RoundedRectPad
    pinGeometry = Geda_PinGeometry
    pinGang = Geda_PinGang
    pinSpec = Geda_PinSpec
    silkText = Geda_SilkText # No such beast in gEDA except for refdes.
    silkLine = Geda_SilkLine
    silkArc = Geda_SilkArc
    keepOutRect = Geda_KeepOutRect
    _indent = '    '
    def rendering(self, warningCallback):
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
            for ln in pin.rendering(warningCallback):
                yield self._indent + ln
        for art in self.silk:
            for ln in art.rendering(warningCallback):
                yield self._indent + ln
        # Render keep-outs
        for ko in self.keepOuts:
            for ln in ko.rendering(warningCallback):
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


