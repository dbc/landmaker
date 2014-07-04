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

# Define primitive rendering for gEDA.

class Geda_RoundPad(fc.RoundPad):
    @property
    def square(self):
        return False

class Geda_SquarePad(fc.SquarePad):
    @property
    def square(self):
        return True
    @property
    def dia(self):
        return self.width # A pcb-ism. This hack simplifies Pin[] rendering.

##class Geda_RectPad(fc.RectPad):
##    def rendering(self, context):
##        "Context is 'c' or 's' for component or solder side."
##        pass
##
##class Geda_RoundedRectPad(fc.RoundedRectPad):
##    def rendering(self, context):
##        "Context is 'c' or 's' for component or solder side."
##        pass

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
        botOnly = not self.symmetric and self.topPad == None
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
            yield 'Pin[{0:d} {1:d} {2:d} {3:d} {4:d} {5:d} "{6:s}" "{7:d}" "{8:s}"]'.format( \
                self.x.gu, self.y.gu,  # x,y relative to mark \
                p.dia.gu,  # pad diameter \
                (p.clearance * 2.0).gu,  # Cu clearance \
                (p.dia + p.relief).gu,  # Diameter of mask anti-pad \
                self.geo.drill.gu,  # Drill diameter \
                self.name,  # pin name \
                self.num,  # pin number \
                'square' if p.square else '')
        elif cl.topOnly and not cl.drilled:
            # These map directly to Pad[] elements.
            yield '# <render a normal SMT pad>'
        elif cl.drilled and not cl.simple:
            # These require obscure jiggery-pokery in pcb.
            yield '# <render a complex drilled pad>'
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
        params = [self.x, self.y, self.x2, self.y2, self.penWidth]
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



# Define footprint-level gEDA renderer.
class Geda_Footprint(object):
    roundPad = Geda_RoundPad
    squarePad = Geda_SquarePad
    #rectPad = Geda_RectPad
    #roundedRectPad = Geda_RoundedRectPad
    pinGeometry = Geda_PinGeometry
    pinGang = Geda_PinGang
    pinSpec = Geda_PinSpec
    silkText = Geda_SilkText # No such beast in gEDA except for refdes.
    silkLine = Geda_SilkLine
    silkArc = Geda_SilkArc
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
        yield 'Element["{0:s}" "" "" "" {1:d} {2:d} {3:d} {4:d} {5:d} {6:d} "{7:s}"]'.format( \
            sflags, markY, markY, self.refdes.x.gu, self.refdes.y.gu, \
            textRot, textScale, textFlags)
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
    
### Import the generic plug-ins.
##from fp_so import FP_so
##from fp_th2pad import FP_th2pad


##class Geda_FP_so(Geda_Footprint, plmod['FP_so'].FP_so):
##    pass
##
##class Geda_FP_th2pad(Geda_Footprint, plmod['FP_th2pad'].FP_th2pad):
##    pass

fp_plugins = fc.collectPlugins(globals())

if __name__ == '__main__':
    print fp_plugins
    gg = Geda_FP_so()
    ff = gg.silkText(1,2,3,4,"5",10)
    ff.foo()


