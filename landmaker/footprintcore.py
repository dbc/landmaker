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

from collections import namedtuple
import re
import math as m
import datetime as dt
import os
import tokenizertools as tt
from lookaheadtools import LinesOf
from inspect import stack,getframeinfo

debug = ''

TAU = m.pi * 2.0
HALF_PI = m.pi / 2.0

def trace(name, globalVars, localVars=None):
    callerFrameRecord = stack()[1]
    info = getframeinfo(callerFrameRecord[0])
    try:
        v = localVars[name]
    except (TypeError,KeyError):
        v = globalVars[name]
    print '{0:s} = {1:s} ({info.filename}:{info.function}@{info.lineno})'.format(
        name, repr(v),info=info)


#
# Exceptions
#
class FootprintException(Exception):
    "Base class for footprint generation exceptions raised by plugins."
    @property
    def msg(self):
        return "FootprintException: " + self.__class__.__name__ 

class RuleNotFound(FootprintException):
    @property
    def msg(self):
        return self.args[0].join(["Required rule '","' not found."])

class RuleError(FootprintException):
    "Raise on validation failure."
    pass

class RequiredKWError(FootprintException):
    @property
    def msg(self):
        return self.args[0].join(["Required keyword '","' missing."])

class InvalidKWError(FootprintException):
    @property
    def msg(self):
        return self.args[0].join(["Invalid keyword '","' present."])

class ParamSyntax(FootprintException):
    @property
    def msg(self):
        return "Parameter syntax error: " + self.args[0]

class ParamValueError(FootprintException):
    @property
    def msg(self):
        return "Parameter value error: " + self.args[0]

class CanNotRenderError(FootprintException):
    @property
    def msg(self):
        return "Can not render: " + self.args[0]

class InternalError(Exception):
    pass

#
# Foundation class.
#
class FPCoreObj(object):
    def __repr__(self):
        return ''.join([self.__class__.__name__,'(',
            ','.join([repr(x) for x in self.reprvals()]),
                 ')'])
    def reprvals(self):
        return []
    def mustbe(self, a_type, optional_message=None):
        if isinstance(self, a_type):
            return self
        wanted = a_type.__name__
        got = self.__class__.__name__
        msg = (optional_message if optional_message else
               ''.join(['Expected: ',wanted,', but got: ',got]))
        raise TypeError(msg)

#
# Dim -- linear dimension with prefered diplay units
#
class Dim(FPCoreObj):
    "Linear dimension carrying along prefered display units."
    mm_per_mil = 0.0254
    valid_display_units = frozenset(['mm','mil','inch'])
    def __init__(self, mm_value, display_units=None):
        if display_units:
            self._v = float(mm_value)
            self.du = display_units
        else:
            if isinstance(mm_value,str):
                t = self.__class__.from_str(mm_value)
                self._v = t._v
                self.du = t.du
            elif isinstance(mm_value,Dim):
                self._v = mm_value._v
                self.du = mm_value.du
            elif mm_value == None:
                return None # FIXME: add unit test
            else:
                raise ValueError(' '.join(['Can not convert',repr(mm_value),repr(display_units),'to Dim.']))
    def reprvals(self):
        return [self._v, self.du]
    @property
    def du(self):
        return self._du
    @du.setter
    def du(self, display_units):
        if not display_units in self.valid_display_units:
            raise ValueError (str(display_units) + ' not a valid display unit.')
        self._du = display_units
    def __str__(self):
        if self.du == 'mil':
            v = self.mil
        elif self.du == 'mm':
            v = self.mm
        else:
            v = self.inch
        return '{0:g} {1:s}'.format(v,self.du)
    def copy(self):
        return self.__class__(self._v, self.du)
    @classmethod
    def MM(cls, v):
        "Construct from millimeters."
        return cls(v,'mm')
    @classmethod
    def MIL(cls,v):
        "Construct from mils."
        return cls(float(v) * cls.mm_per_mil, 'mil')
    @classmethod
    def INCH(cls,v):
        "Construct from inches."
        return cls(float(v) * cls.mm_per_mil * 1000.0, 'inch')
    @classmethod
    def DRILL(cls,v):
        "Construct from #nn drill number."
        # Look up via DrillRack class method.
        try:
            return DrillRack.number[v]
        except:
            raise ValueError(v + ' drill size not found.')
    @classmethod
    def VU(cls, v, display_units):
        "Construct from display units specified in variable."
        if display_units in ['mil','thou']:
            return cls.MIL(v)
        if display_units == 'mm':
            return cls.MM(v)
        if display_units in ['inch','in']:
            return cls.INCH(v)
        raise ValueError(repr(display_units) + ' is not a valid display unit.')
    @classmethod
    def from_str(cls, s, default_units=None):
        "Construct from string consisting of number and unit keyword."
        mo = re.match(r'([0-9.]+)(\s*)(mm|mil|inch|in)?\Z', s.strip())
        if mo:
            v = float(mo.group(1))
            du = mo.group(3) if mo.group(3) else default_units
            return cls.VU(v,du)
        elif s.startswith('#'):
            return cls.DRILL(s)
        else:
            raise ValueError(s + ' not convertable to Dim().')
    @property
    def mm(self):
        "Value in millimeters."
        return self._v
    @mm.setter
    def mm(self, v):
        self._v = float(v)
    @property
    def mil(self):
        "Value in thousanths of inch."
        return self._v / self.mm_per_mil
    @mil.setter
    def mil(self, v):
        self._v = float(v) * self.mm_per_mil
    @property
    def inch(self):
        "Value in inches."
        return self.mil / 1000.0
    @inch.setter
    def inch(self, v):
        self.mil = float(v) * 1000.0
    @property
    def gu(self):
        "Value gEDA units (1/100,000 of inch)."
        return int (self.mil * 100.0)
    @gu.setter
    def gu(self, v):
        self.mil = (float(v) / 100.0)
    @property
    def u0(self):
        "Return a zero with same units."
        # FIXME: add unit tests
        return self.__class__(0.0, self.du)
    def minus_plus(self, other):
        return self-other, self+other
    # Arithmetic operators can take two Dim() instances, or
    # one Dim() and one float()'able operand.  Display units are
    # taken from the left-hand operand in the case of two Dim()'s.
    # Arithmetic doesn't need scaling, since everything is stored
    # in millimeters as the canonical representation.
    def __int__(self):
        return int(self._v)
    def __float__(self):
        return self._v
    def _scale(self, other):
        "Ensures unit consistency for addition operations."
        if isinstance(other,Dim):
            # Cool, already a Dim()
            return float(other)
        try:
            # Can it be made into a dim? (Perhaps it is a '3mm' style str...
            o = Dim(other)
        except ValueError:
            # If it's a scalar, match it to my units.
            o = self.__class__.VU(float(other),self.du)
        return float(o)
    def __add__(self, other):
        #return self.__class__(self._v + float(other), self.du)
        return self.__class__(self._v + self._scale(other), self.du)
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        return self.__class__(self._v - self._scale(other), self.du)
    def __rsub__(self, other):
        return self.__class__(self._scale(other)-self._v, self.du)
    def __mul__(self, other):
        return self.__class__(self._v * float(other), self.du)
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        return self.__class__(self._v / float(other), self.du)
    def __rdiv__(self, other):
        return self.__class__(float(other)/self._v, self.du)
    def __neg__(self):
        return self.__class__(-self._v, self.du)
    def __pos__(self):
        return self
    def __lt__(self, other):
        return self._v < self._scale(other)
    def __ge__(self, other):
        return self._v >= self._scale(other)
    def __le__(self, other):
        return self._v <= self._scale(other)
    def __gt__(self, other):
        return self._v > self._scale(other)
    def __eq__(self, other):
        if other==None: return False
        return self._v == self._scale(other)
    def __ne__(self, other):
        if other==None: return True
        return self._v != self._scale(other)
    def __abs__(self):
        return Dim(abs(self._v), self.du)

#
# Point
#
class Pt(FPCoreObj):
    def __init__(self, x, y=None):
        # In all cases below, we depend on the x.setter, y.setter to call Dim()
        if y == None:
            # Try to unpack an iterable, let any exceptions bubble up.
            self.x, self.y = x
        else:
            self.x = x
            self.y = y
    def reprvals(self):
        return [self._x, self._y]
    def __str__(self):
        return ''.join(['Pt(',str(self.x),',',str(self.y),')'])
    def __getitem__(self, index):
        # This enables __init__() to be a copy constructor.
        if index==0: return self.x
        if index==1: return self.y
        raise StopIteration
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self,v):
        self._x = Dim(v)
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, v):
        self._y = Dim(v)
    @classmethod
    def MM(cls, x, y):
        return cls(Dim.MM(x), Dim.MM(y))
    @classmethod
    def MIL(cls, x, y):
        return cls(Dim.MIL(x), Dim.MIL(y))
    @classmethod
    def INCH(cls, x, y):
        return cls(Dim.INCH(x), Dim.INCH(y))
    @classmethod
    def xy0(cls, x):
        return cls(x, Dim.VU(0,x.du))
    @classmethod
    def x0y(cls, y):
        return cls(Dim.VU(0,y.du),y)
    @classmethod
    def point_row(cls, p0, p1, count):
        pitch = p0 - p1
        return [p0 + pitch*i for i in xrange(count)]
    @classmethod
    def point_array(cls, p0, p1, counts):
        xcount, ycount = counts
        xpitch, ypitch = p0 - Pt(p1.x,p0.y), p0 - Pt(p0.x,p1.y)
        column_heads = cls.point_row(p0,p0+xpitch, xcount)
        print 'column heads:',column_heads
        t = []
        for p in column_heads:
            t.extend(cls.point_row(p, p+ypitch, ycount))
            print 't',t
        return t
    def order(self, other):
        return (self, other) if self <= other else (other, self)
    def rectify(self,  other):
        "Returns tuple (p1,p2) where x,y are swizzled to guarantee ll,ur rectangle."
        if self.x == other.x or self.y == other.y:
            raise ValueError("Points do not form rectangle.")
        xs = [self.x,  other.x]
        ys = [self.y,  other.y]
        p1 = self.__class__(min(xs), min(ys))
        p2 = self.__class__(max(xs), max(ys))
        return p1, p2
    def spans_org(self, other):
        "True if rectangle defined by self,other contains Pt(0,0)."
        p1,p2 = self.rectify(other)
        org = Pt.MM(0,0)
        return p1 < org and org < p2
    def left_of(self, other):
        return self.x < other.x
    def right_of(self, other):
        return self.x > other.x
    def below(self, other):
        return self.y < other.y
    def above(self, other):
        return self.y > other.y
    def alignedx(self, other):
        return self.x == other.x
    def alignedy(self, other):
        return self.y == other.y
    def orthonormal(self, other):
        return self.alignedx(other) or self.alignedy(other)
    def area(self, other):
        return abs(self.x-other.x) * abs(self.y-other.y)
    def dist(self, other):
        dv = m.sqrt(float((self.x - other.x))**2.0 + float((self.y-other.y))**2.0)
        du = self.x.du
        return Dim(dv,du)
    def bearing(self, other):
        raise NotImplementedError('FIXME')
    @property
    def on_axis(self):
        "True if on either X or Y axis."
        # FIXME: write unit test
        return self.x == 0.0 or self.y == 0.0
    @property
    def reflox(self):
        "Reflect over X axis."
        return self.__class__(self.x, -self.y)
    @property
    def refloy(self):
        "Reflect over Y axis."
        return self.__class__(-self.x, self.y)
    def min_span(self, other):
        a,b = self.rectify(other)
        return Dim(min([b.x-a.x, b.y-a.y]), self.x.du)
    def rotate(self, theta):
        s = m.sin(theta)
        c = m.cos(theta)
        return self.__class__(self.x*c - self.y*s, self.x*s + self.y*c)
    # comparisons
    def __eq__(self, other):
        if other==None:
            return False
        return self.x == other.x and self.y == other.y
    def __ne__(self, other):
        if other==None:
            return True
        return self.x != other.x or self.y != other.y
    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y
    def __lt__(self, other):
        # Same as below and to the left of
        return self.x < other.x and self.y < other.y
    def __ge__(self, other):
        return self.x >= other.x and self.y >= other.y
    def __gt__(self, other):
        # Same as: above and to the right of
        return self.x > other.x and self.y > other.y
    # arithmetic
    # add/subtract points.
    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return self.__class__(self.x - other.x, self.y - other.y)
    def __neg__(self):
        return self.__class__(-self.x, -self.y)
    def __pos__(self):
        return self.__class__(self.x, self.y)
    # Multiply/divide point by a scalar (float or Dim)
    def __mul__(self, other):
        m = float(other)
        return self.__class__(self.x*m, self.y*m)
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        m = float(other)
        return self.__class__(self.x/m, self.y/m)
    # __rdiv__ is non-sensical
    # Other ops
    def __len__(self):
        # FIXME: Add test case
        return self.dist(Pt.MM(0,0))
    
#
# Rules Dictionary
#
class RulesDictionary(dict):
    def __getitem__(self, index):
        try:
            return super(RulesDictionary,self).__getitem__(index)
        except KeyError:
            raise RuleNotFound(index)
    def symb(self, value):
        "Lookup value of symblic rule, or return Dim() if called with a Dim()."
        # Why?  So footprint parsers can pick up a paramter value as either
        # a symbolic or a Dim(), and always pass them through the rules
        # dictionary.  This will supply a value for the symbolic if there
        # is one, or return the Dim() unmolested, simplifying footprint
        # parameter parsing.
        try:
            return self[value]
        except RuleNotFound:
            if isinstance(value, Dim):
                return value
            raise

class DrillRack(FPCoreObj):
    "Map drill size to nearest larger neighbor, or map symbolic drill name."
    # Reference table of number and letter drills.
    number = {
        '#80': Dim.INCH(0.0135),
        '#79': Dim.INCH(0.0145),
        '#78': Dim.INCH(0.016),
        '#77': Dim.INCH(0.018),
        '#76': Dim.INCH(0.020),
        '#75': Dim.INCH(0.021),
        '#74': Dim.INCH(0.0225),
        '#73': Dim.INCH(0.024),
        '#72': Dim.INCH(0.025),
        '#71': Dim.INCH(0.026),
        '#70': Dim.INCH(0.028),
        '#69': Dim.INCH(0.0292),
        '#68': Dim.INCH(0.031),
        '#67': Dim.INCH(0.032),
        '#66': Dim.INCH(0.033),
        '#65': Dim.INCH(0.035),
        '#64': Dim.INCH(0.036),
        '#63': Dim.INCH(0.037),
        '#62': Dim.INCH(0.038),
        '#61': Dim.INCH(0.039),
        '#60': Dim.INCH(0.040),
        '#59': Dim.INCH(0.041),
        '#58': Dim.INCH(0.042),
        '#57': Dim.INCH(0.043),
        '#56': Dim.INCH(0.0465),
        '#55': Dim.INCH(0.052),
        '#54': Dim.INCH(0.055),
        '#53': Dim.INCH(0.0595),
        '#52': Dim.INCH(0.0635),
        '#51': Dim.INCH(0.067),
        '#50': Dim.INCH(0.070),
        '#49': Dim.INCH(0.073),
        '#48': Dim.INCH(0.076),
        '#47': Dim.INCH(0.0785),
        '#46': Dim.INCH(0.081),
        '#45': Dim.INCH(0.082),
        '#44': Dim.INCH(0.086),
        '#43': Dim.INCH(0.089),
        '#42': Dim.INCH(0.0935),
        '#41': Dim.INCH(0.096),
        '#40': Dim.INCH(0.098),
        '#39': Dim.INCH(0.0995),
        '#38': Dim.INCH(0.1015),
        '#37': Dim.INCH(0.104),
        '#36': Dim.INCH(0.1065),
        '#35': Dim.INCH(0.110),
        '#34': Dim.INCH(0.111),
        '#33': Dim.INCH(0.113),
        '#32': Dim.INCH(0.116),
        '#31': Dim.INCH(0.120),
        '#30': Dim.INCH(0.1285),
        '#29': Dim.INCH(0.136),
        '#28': Dim.INCH(0.1405),
        '#27': Dim.INCH(0.144),
        '#26': Dim.INCH(0.147),
        '#25': Dim.INCH(0.1495),
        '#24': Dim.INCH(0.152),
        '#23': Dim.INCH(0.154),
        '#22': Dim.INCH(0.157),
        '#21': Dim.INCH(0.159),
        '#20': Dim.INCH(0.161),
        '#19': Dim.INCH(0.166),
        '#18': Dim.INCH(0.1695),
        '#17': Dim.INCH(0.173),
        '#16': Dim.INCH(0.177),
        '#15': Dim.INCH(0.180),
        '#14': Dim.INCH(0.182),
        '#13': Dim.INCH(0.185),
        '#12': Dim.INCH(0.189),
        '#11': Dim.INCH(0.191),
        '#10': Dim.INCH(0.1935),
        '#9': Dim.INCH(0.196),
        '#8': Dim.INCH(0.199),
        '#7': Dim.INCH(0.201),
        '#6': Dim.INCH(0.204),
        '#5': Dim.INCH(0.2055),
        '#4': Dim.INCH(0.209),
        '#3': Dim.INCH(0.213),
        '#2': Dim.INCH(0.221),
        '#1': Dim.INCH(0.228),
        '#A': Dim.INCH(0.234),
        '#B': Dim.INCH(0.238),
        '#C': Dim.INCH(0.242),
        '#D': Dim.INCH(0.246),
        '#E': Dim.INCH(0.250),
        '#F': Dim.INCH(0.257),
        '#G': Dim.INCH(0.261),
        '#H': Dim.INCH(0.266),
        '#I': Dim.INCH(0.272),
        '#J': Dim.INCH(0.277),
        '#K': Dim.INCH(0.281),
        '#L': Dim.INCH(0.290),
        '#M': Dim.INCH(0.295),
        '#N': Dim.INCH(0.302),
        '#O': Dim.INCH(0.316),
        '#P': Dim.INCH(0.323),
        '#Q': Dim.INCH(0.332),
        '#R': Dim.INCH(0.339),
        '#S': Dim.INCH(0.348),
        '#T': Dim.INCH(0.358),
        '#U': Dim.INCH(0.368),
        '#V': Dim.INCH(0.377),
        '#W': Dim.INCH(0.386),
        '#X': Dim.INCH(0.397),
        '#Y': Dim.INCH(0.404),
        '#Z': Dim.INCH(0.413),
    }
    def __init__(self, drill_list = [], symbolic={}):
        self._dl = sorted(drill_list)
        self._symb = symbolic
    def drills(self):
        return self._dl[:]
    def symbolics(self):
        return self._symb.copy()
    def reprvals(self):
        return [self._dl, self._symb]
    def add_drill(self, aDrill):
        aDrill.mustbe(Dim, "Drills must be specified as Dim()'s")
        existing = self[aDrill]
        if existing == aDrill: return # Avoid adding redundant drills.
        self._dl.append(aDrill)
        self._dl = sorted(self._dl)
    def add_symbolic(self, aName, aDrill):
        aName.mustbe(str)
        aDrill.mustbe(Dim, 'Drills must be Dim().')
        self._symb[aName]=aDrill
    def __getitem__(self, v):
        # First do number drill or symbolic drill mapping.
        if isinstance(v,str):
            if v[0] == '#':
                try:
                    v = self.number[v]
                except KeyError:
                    raise ValueError('Number drill not found.')
            else:
                try:
                    v = self._symb[v]
                except KeyError:
                    raise ValueError(v.join(['Symbolic drill ',' not found.']))
        v.mustbe(Dim, "Drills must be Dim().")        
        # Find first drill >= to requested size.
        dli = iter(self._dl)
        try:
            cur = next(dli)
            while True:
                if v > cur:
                    cur = next(dli)
                else:
                    return cur
        except StopIteration:
            # Too large.  Return original drill value.
            return v

class NoRack(DrillRack):
    def add_drill(self, aDrill):
        print "Can't add to drill rack 'none'."
    def add_symbolic(self, aName, aDrill):
        print "Can't add to drill rack 'none'."

#
# Footprint primitives.
#
class Primitive(FPCoreObj):
    "Footprints must consist entirely of primitives."
    def __init__(self, loc):
        self.loc = loc
    def reprvals(self):
        return [self.loc]
    @property
    def loc(self):
        return self._loc
    @loc.setter
    def loc(self, v):
        # FIXME: Perhasps should just call Pt() constructor, let it throw exception.
        if not isinstance(v,Pt):
            raise TypeError('Location must be a Pt().')
        self._loc = v

#
# Aperture Classes
#
class Aperture(FPCoreObj):
    pass

class StandardAperture(Aperture):
    def __init__(self, xholesize=None, yholesize=None):
        self.xholesize = xholesize
        self.yholesize = yholesize

class SACircle(StandardAperture):
    def __init__(self, diameter, xholesize=None, yholesize=None):
        StandardAperture.__init__(self, xholesize, yholesize)
        self.diameter = diameter.mustbe(Dim)
    def reprvals(self):
        return [self.diameter,self.xholesize,self.yholesize]

class SARectangular(StandardAperture):
    def __init__(self, xsize, ysize, xholesize=None, yholesize=None):
        StandardAperture.__init__(self, xholesize, yholesize)
        self.xsize = xsize
        self.ysize = ysize
    @property
    def is_square(self):
        return self.xsize == self.ysize
    def reprvals(self):
        t = [self.xsize, self.ysize]
        if self.xholesize is not None or self.yholesize is not None:
            t.extend([self.xholesize, self.yholesize])
        return t

class SARectangle(SARectangular):
    pass

class SAObround(SARectangular):
    pass

class SAPolygon(StandardAperture):
    def __init__(self, diameter, num_vertices, rot=None,
                 xholesize=None, yholesize=None):
        StandardAperture.__init__(self, xholesize, yholesize)
        self.diameter = diameter
        self.num_vertices = num_vertices
        self.rot = rot

class ApertureMacroPrimitive(FPCoreObj):
    pass

class MPComment(ApertureMacroPrimitive):
    def __init__(self, text):
        pass

class MPCircle(ApertureMacroPrimitive):
    def __init__(self, diameter, loc, exposure=True):
        # loc is Pt()
        pass

class MPVectorLine(ApertureMacroPrimitive):
    def __init__(self, width, start, end, exposure=True, rot=None):
        # start,end are Pt()
        pass

class MPCenterLine(ApertureMacroPrimitive):
    def __init__(self, width, heigth, loc, exposure=True, rot=None):
        # loc is Pt()
        pass

class MPLowerLeftLine(ApertureMacroPrimitive):
    def __init__(self, width, heigth, loc, exposure=True, rot=None):
        # loc is Pt()
        pass

class MPOutline(ApertureMacroPrimitive):
    def __init__(self, point_list, exposure=True, rot=None):
        # point_list contains Pt() instances.  Since RS-274X requires
        # that the last point be equal to the first, the last point is
        # omitted in point_list, the value is implied.
        pass

class MPPolygon(ApertureMacroPrimitive):
    def __init__(self, diameter, num_vertices, loc, exposure=True, rot=0):
        # loc is Pt()
        pass

class MPMoire(ApertureMacroPrimitive):
    def __init__(self, loc, diameter, ring_thickness, ring_gap,
                 max_num_rings, crosshair_thickness, crosshair_length, rot=None):
        # loc is a Pt()
        pass

class MPThermal(ApertureMacroPrimitive):
    def __init__(self, loc, outer_diameter, inner_diameter, gap_thickness,
                 rot=None):
        pass

class ApertureMacro(Aperture):
    # Has list of primitives.
    # Has add_<primitive>() methods to add a primitive to the
    # list.
    # Has parameter list.
    # Values can be expression trees.
    pass

#
# Mask Classes
#
# Mask's can have an ID so that N:1 mapping doesn't cause re-draws.
# Maybe an automatic serializer in the creator?
class Mask(Primitive):
    "Base class for masks."
    _serial = 0
    def __init__(self):
        self.serial = self.__class__._serial
        self.__class__._serial += 1

class DrawnMask(Mask):
    # A ShapeInstance. ThermalPads have a list of these.
    def __init__(self, aperture, loc):
        Primitive.__init__(self, loc.mustbe(Pt))
        self.aperture = aperture
    @classmethod
    def rectangle(cls, xsize, ysize, loc=None):
        ap = fpbase.saRectangle(xsize, ysize)
        return cls(ap, loc)

class DerivedMask(Mask):
    "Derive a mask by bloating the aperture property of something that has one."
    # Presumeably, 'base' is a Land()
    def __init__(self, base, bloat):
        self.base = base
        self.bloat = bloat
    @property
    def loc(self):
        return self.base.loc

class NoMask(Mask):
    "Specifies no mask."
    pass

#
# Hole primitives
#
class PlatedHole(FPCoreObj):
    def __init__(self, tent):
        self.tent = bool(tent)

class PlatedDrill(PlatedHole):
    def __init__(self, diameter, offset=None, tent=False):
        PlatedHole.__init__(self, tent)
        self.offset = Pt.MM(0,0) if offset == None else offset.mustbe(Pt)
        self.diameter = diameter.mustbe(Dim)

class PlatedSlot(PlatedHole):
    # Not clear how best to specify.
    pass

#
# Paste classes
#
# Since gEDA/PCB derives all paste from Mask, the only
# sensible thing in PCB is a DerivedPaste that points to
# the Mask shape, or perhaps let None==automatic.
class Paste(Primitive):
    pass

class DrawnPaste(Paste):
    pass

class DerivedPaste(Paste):
    def __init__(self, base, bloat):
        self.base = base
        self.bloat = bloat
    @property
    def loc(self):
        return self.base.loc

class NoPaste(Paste):
    "Specifies no paste."
    pass

#
# Keep-outs
#
class CopperKeepout(Primitive):
    # Specified as an aperture.
    # List of these hangs off a footprint.
    pass

#
# Land pads
# 
class Land(Primitive):
    # Has a shape and a clearance.
    # Specify clearance by pad shape bloat here.
    # Specify other clearance shapes at footprint level.
    # OR.... should per-pad clearance be specified in PinDef?
    # Issue there is ThruPin may have different clearance per layer.
    # --
    # This might be a good place for convenience funcitons to create
    # the common shapes.
    def __init__(self, clearance, aperture, loc=None):
        flashpoint = Pt.MM(0,0) if loc is None else loc.mustbe(Pt)
        Primitive.__init__(self, flashpoint)
        self.aperture = aperture.mustbe(Aperture)
        self.clearance = clearance.mustbe(Dim)
    def reprvals(self):
        t = [self.loc, self.aperture, self.clearance]
        return t
    @classmethod
    def circle(cls, clearance, diameter):
        ap = fpbase.saCircle(diameter)
        return cls(clearance, ap)
    @classmethod
    def square(cls, clearance, diameter):
        ap = fpbase.saRectangle(diameter, diameter)
        return cls(clearance, ap)
    @classmethod
    def rectangle(cls, clearance, xsize, ysize, loc=None):
        ap = fpbase.saRectangle(xsize, ysize)
        return cls(clearance, ap, loc)
    @classmethod
    def obround(cls, clearance, xsize, ysize, offset=None):
        ap = fpbase.saObround(xsize, ysize)
        return cls(clearance, ap, offset)
        

#
# Pin Geometry Specifications
#
class PinGeometry(FPCoreObj):
    pass

class ThruPin(PinGeometry):
    # One PlatedHole, landing aperture(s), and apertures for masks.
    # Also aperture for inner land.
    # 1:1 Mask on comp, 1:1 Mask on solder
    # no paste
    # FIXME: symmetry also depends on both masks being derived from same
    # pad and have same bloat.
    def __init__(self, hole, solder_land, **kwargs):
        "kwargs: mask_bloat, solder_mask, comp_land, comp_mask, inner_land"
        self.hole = hole.mustbe(PlatedHole)
        self.solder_land = solder_land.mustbe(Land)
        try:
            self.comp_land = kwargs['comp_land']
        except KeyError:
            self.comp_land = '='
        try:
            self.inner_land = kwargs['inner_land'].mustbe(Land)
        except KeyError:
            self.inner_land = None
        try:
            bloat = kwargs['mask_bloat']
            kwargs['solder_mask'] = fpbase.derivedMask(self.solder_land, bloat)
            kwargs['comp_mask'] = fpbase.derivedMask(self.comp_land, bloat)
        except KeyError:
            pass
        self.solder_mask = kwargs['solder_mask'].mustbe(Mask)
        self.comp_mask = kwargs['comp_mask'].mustbe(Mask)
    def reprvals(self):
        return [self.hole, self.solder_land, self.comp_land,
                self.solder_mask, self.comp_mask]
    @property
    def solder_land(self):
        return self._solder_land
    @solder_land.setter
    def solder_land(self, v):
        v.mustbe(Land)
        try:
            if self._comp_land == '=':
                # Trap case of breaking symmetry.
                self._comp_land = self._solder_land
        except AttributeError:
            pass # _comp_land not yet set
        self._solder_land = v
        try:
            if self._solder_land == self._comp_land:
                # Trap case where creating symmetry.
                self._comp_land = '='
        except AttributeError:
            pass
    @property
    def comp_land(self):
        return self._solder_land if (self._comp_land == '=') \
               else self._comp_land
    @comp_land.setter
    def comp_land(self, v):
        try:
            self._comp_land = '=' if v == '=' or v == self.solder_land \
                                 else v.mustbe(Land)
        except AttributeError:
            self._comp_land = v.mustbe(Land) # _solder_land not yet set.
    @property
    def symmetric(self):
        return self._comp_land == '='
    @classmethod
    def circle(cls, drill, clearance, diameter, mbloat):
        dr = fpbase.platedDrill(drill) 
        land = fpbase.land.circle(clearance, diameter)
        return cls(dr, land, mask_bloat=mbloat)
    @classmethod
    def square(cls, drill, clearance, diameter, mbloat):
        dr = fpbase.platedDrill(drill) 
        land = fpbase.land.square(clearance, diameter)
        return cls(dr, land, mask_bloat=mbloat)
    @classmethod
    def obround(cls, drill, clearance, xsize, ysize, mbloat, offset=None):
        pass
    @classmethod
    def obround_solder(cls, drill, clearance, comp_dia, mbloat, **kwargs):
        "Must specify one of xstretch, ystretch. Optionally: solder_dia."
        try:
            solder_dia = kwargs['solder_dia']
        except:
            solder_dia = comp_dia
        try:
            stretch = kwargs['xstretch']
            offset = Pt(stretch/2.0, Dim.MM(0))
            xsize, ysize = solder_dia + abs(stretch), solder_dia
        except:
            stretch = kwargs['ystretch']
            offset = Pt(Dim.MM(0), stretch/2.0)
            xsize, ysize = solder_dia, solder_dia + abs(stretch)
        dr = fpbase.platedDrill(drill)
        topland = fpbase.land.circle(clearance, comp_dia)
        botland = fpbase.land.obround(clearance, xsize, ysize, offset)
        return cls(dr, botland, comp_land=topland, mask_bloat=mbloat)        
            
class SMTPad(PinGeometry):
    # Single SMT pad.
    # N:1 mapping of SMTPads to to Mask is allowed.  This allows
    # construction of a gang mask.  Should have convenience functions
    # for creation of a gang mask.
    # 1:1 to Paste
    def __init__(self, land, **kwargs):
        "kwargs: paste, mask, onback"
        self.land = land.mustbe(Land)
        try:
            self.paste = kwargs['paste'].mustbe(Paste)
        except KeyError:
            self.paste = fpbase.derivedPaste(self.land, Dim.MM(0))
        try:
            t = kwargs['mask']
            self.mask = fpbase.derivedMask(self.land, t) if isinstance(t, Dim) \
                        else t.mustbe(Mask)
        except KeyError:
            self.mask = fpbase.noMask()
        # 'onback' flag is for building edge connectors or anyplace there
        # is a land on the side opposite the component.
        try:
            self.onback = bool(kwargs['onback'])
        except KeyError:
            self.onback = False
    @classmethod
    def obround(cls, clearance, xsize, ysize, mbloat):
        land = fpbase.land.obround(clearance, xsize, ysize)
        return cls(land, mask=mbloat.mustbe(Dim))
    @classmethod
    def gang(cls, pads, bloat):
        """Construct gang mask by bloating extremes of listed pads,
        set all pads to gang."""
        # Result will be a DrawnMask()
        pass

class ThermalPolygon(PinGeometry):
    # Has a list of AntiMasks on each side.
    # 1 land, N holes
    # 1:N to Mask
    # 1:M to Paste
    # FIXME: onback should probably be back_land instead.
    def __init__(self, land, holes, masks, pastes, back_land=None):
        self.land = land.mustbe(Land)
        self.holes = [h.mustbe(PlatedHole) for h in holes]
        self.masks = [m.mustbe(Mask) for m in masks]
        self.pastes = [p.mustbe(Paste) for p in pastes]
        self.back_land = None if back_land is None else back_land.mustbe(Land)
    @classmethod
    def rectangle(cls, clearance, cu_ll, cu_ur, mask_ll, mask_ur,
                  drillsize, drill_locs):
        """Rectangular pad and mask. Pastes derived from mask.
        drill field auto-constructed. ll/ur is relative to flash point."""
        cu_span = cu_ur - cu_ll
        offset = (cu_ur + cu_ll) / 2.0
        land = fpbase.land.rectangle(clearance, cu_span.x, cu_span.y, offset)
        # FIXME: mask might be none
        if mask_ll:
            mask_span = mask_ur - mask_ll
            offset = (mask_ur + mask_ll) / 2.0
            mask = fpbase.drawnMask.rectangle(mask_span.x, mask_span.y, offset)
            paste = fpbase.derivedPaste(mask,0)
            masks = [mask]
            pastes = [paste]
        else:
            masks = []
            pastes = []
        if drill_locs:
            holes = [fpbase.platedDrill(drillsize, loc) for loc in drill_locs]
            # FIXME: Should add tenting for drill hits within the mask openning.
        else:
            holes = []
        return cls(land, holes, masks, pastes) 
        


#
# Pin classes
#
class PinInfo(Primitive):
    # FIXME: Refactor pin number and pin name down here.
    # although, PinGang should not reach num and name down here.
    pass

class PinSpec(PinInfo):
    def __init__(self, loc, pin_number, pin_geometry,
                 rotation = 0, pin_name = None):
        super(PinSpec, self).__init__(loc)
        self.num = int(pin_number)
        self.geo = pin_geometry.mustbe(PinGeometry)
        self.rot = rotation
        if pin_name is not None:
            self._name = str(pin_name)
    def reprvals(self):
        l = [self.loc, self.num, self.geo]
        try:
            nm = self._name
        except AttributeError:
            nm = None
        if (self.rot != 0 or nm != None): l.append(self.rot)
        if nm != None: l.append(nm)
        return l
    @property
    def name(self):
        try:
            return self._name
        except AttributeError:
            return str(self.num)
    @name.setter
    def name(self, v):
        self._name = str(v)

#
# Silk classes
#
class Silk(Primitive):
    def __init__(self, loc, pen_width):
        super(Silk, self).__init__(loc)
        self.pen_width = pen_width
    @property
    def pen_width(self):
        return self._pw
    @pen_width.setter
    def pen_width(self, v):
        self._pw = v.mustbe(Dim)
    
class SilkText(Silk):
    def __init__(self, loc, rotation, pen_width, text, size):
        super(SilkText, self).__init__(loc, pen_width)
        self.rot = rotation
        self.text = str(text) if text != None else ''
        size.mustbe(Dim)
        if size <= 0.0:
            raise ValueError('Silk width must be > 0.')
        self.size = size 
    def reprvals(self):
        #return [self.x, self.y, self.rot, self._pw, self.text, self._sz]
        return [self.loc, self.rot, self.pen_width, self.text, self.size]


class RefDes(SilkText):
    pass

class SilkLine(Silk):
    def __init__(self, p1, p2, pen_width):
        super(SilkLine, self).__init__(p1, pen_width)
        self.p2 = Pt(p2)

class SilkArc(Silk):
    "Fixed radius arc."
    def __init__(self, loc, radius, start_angle, arc_angle, pen_width):
        super(SilkArc, self).__init__(loc, pen_width)
        self.radius = radius.mustbe(Dim)
        if start_angle < 0.0 or start_angle > 360.0:
            raise ValueError('Angle must be in range 0..360')
        self.start = start_angle
        if arc_angle < 0.0 or arc_angle > 360.0:
            raise ValueError('Arc length must be between 0 and 360.')
        self.arc = arc_angle

class KeepOut(Primitive):
    "Specification of keep-out areas."
    pass

class KeepOutRect(KeepOut):
    "Keep out rectangle."
    def __init__(self, p1, p2):
        p1, p2 = Pt(p1), Pt(p2)
        if p1 == None or p2 == None:
            raise ValueError('Keep out corners can not be None.')
        self.ll, self.ur = p1.rectify(p2)


#
# Footprint base classes.
#
class KWToken(FPCoreObj):
    #keywords = {'mm':'MM','inch':'INCH', 'in':'INCH','mil':'MIL'}
    units = frozenset(['MIL', 'MM', 'INCH'])
    def __init__(self, ttype, value):
        self.type = ttype
        self.value = value
    def reprvals(self):
        return [self.type, self.value]
    @classmethod
    def type_KW(cls, s, lexposIgnored):
##        if s in cls.keywords:
##            return cls(cls.keywords[s],s)
        return cls('KW',s)
    @classmethod
    def type_punct(cls, s, lexposIgnored):
        return cls(s,s)
    @classmethod
    def type_NUM(cls, s, lexposIgnored):
##        try:
##            v = float(s)
##            return cls('NUM',v)
##        except ValueError:
##            return cls('BAD',s)
        try:
            d = Dim(s)
        except ValueError:
            #return cls('BAD',s)
            pass
        else:
            return cls('NUM',d)
        try:
            v = float(s)
        except ValueError:
            return cls('BAD',s)
        else:
            return cls('NUM',v)
##    @classmethod
##    def typeDrillNum(cls, s, lexposIgnored):
##        d = DrillRack.numberToDim(s)
##        if d == None:
##            return cls('BAD',s)
##        return cls('DIM',d)
    @classmethod
    def type_STR(cls, s, lexposIgnored):
        end = -1 if s[-1] in '"\'' else None
        return cls('STR',s[1:end])
    @classmethod
    def type_BAD(cls, s, lexposIgnored):
        return cls('BAD',s)
    def __eq__(self, other):
        if other is None:
            return False
        return self.type == other.type and self.value == other.value

KWSpec = namedtuple('KWSpec','units req vlist')

class KWParamLexer(tt.RegexTokenizer):
    spec = [
        # The order is critical!  First match encountered is always taken.
        # Floats need to come before integers or confusion reigns.
        (r'[a-zA-Z][a-zA-Z0-9_]*', KWToken.type_KW), # Keyword/identifier, etc.
        (r'[0-9]*[\.][0-9]+\s*(mm|mil|inch|in)?', KWToken.type_NUM), # Float.
        (r'[0-9]+\s*(mm|mil|inch|in)?', KWToken.type_NUM), # Integer.
        (r'#([0-9]+|[A-Z])', KWToken.type_NUM), # A number/letter drill.
        (r'".*"', KWToken.type_STR), # Quoted matter using "
        (r"'.*'", KWToken.type_STR), # Quoted matter using '
        (r'".*$', KWToken.type_STR), # Missing close " -- take it all :/
        (r"'.*$", KWToken.type_STR), # Missing close ' -- take it all
        (r'\s*',None), # Ignore white space.
        (r'[=,]', KWToken.type_punct), # Valid punctuation
        (r'.',KWToken.type_BAD), # Catch-all
    ]

class ArgObject(FPCoreObj):
    def reprvals(self):
        return self.__dict__.items()

class Footprint(FPCoreObj):
    # Plugins MUST instantiate primitive and sub-primitive classes
    # via these class variables so that rendering classes may
    # provide alternate specializations of them.
    # ------------------
    # Standard Apertures
    saCircle = SACircle
    saRectangle = SARectangle
    saObround = SAObround
    saPolygon = SAPolygon
    # Aperture Macros
    mpComment = MPComment
    mpCircle = MPCircle
    mpVectorLine = MPVectorLine
    mpCenterLine = MPCenterLine
    mpLowerLeftLine = MPLowerLeftLine
    mpOutline = MPOutline
    mpPolygon = MPPolygon
    mpMoire = MPMoire
    mpThermal = MPThermal
    apertureMacro = ApertureMacro
    # Masks
    drawnMask = DrawnMask
    derivedMask = DerivedMask
    noMask = NoMask
    # Plated holes
    platedDrill = PlatedDrill
    platedSlot = PlatedSlot
    # Lands and pins
    land = Land
    thruPin = ThruPin
    smtPad = SMTPad
    thermalPolygon = ThermalPolygon
    pinSpec = PinSpec
    # Silk
    silkText = SilkText
    refDes = RefDes
    silkLine = SilkLine
    silkArc = SilkArc
    keepOutRect = KeepOutRect
    def __init__(self, name, description, refdes, pins = [], silk = [], \
                 comments = [], keepOuts = []):
        self.name = str(name) if name is not None else ''
        self.desc = str(description) if description is not None else ''
        assert refdes != None
        if isinstance(refdes, str):
            refdes = self.refDes(0,0,0,'textpen',refdes,'refdessize')
        if not isinstance(refdes, RefDes):
            raise TypeError('Expected RefDes() or str().')
        self.refdes = refdes
        self.pins = pins
        self.silk = silk # FIXME: Add type-checking: must be silk primitives
        self.comments = [str(x) for x in comments]
        self.keepOuts = keepOuts # FIXME: add type-checking
    @property
    def pins(self):
        return self._pins
    @pins.setter
    def pins(self, l):
        if l and not min([isinstance(x, PinInfo) for x in l]):
            raise ValueError('Must be list of PinSpec or PinGang.')
        self._pins = l
    @property
    def silk(self):
        return self._silk
    @silk.setter
    def silk(self, l):
        if l and not min([isinstance(x, Silk) for x in l]):
            raise ValueError('Must be a silk layer art element.')
        self._silk = l
    def reprvals(self):
        return [self.refdes, self.pins, self.silk, self.comments]
    @classmethod
    def parse(cls, footprintname, params, rules, rack, warning_callback):
        raise NotImplementedError('Abstract')
    @classmethod
    def parse_kwargs(cls, params, kwspec = {}):
        "Standarized parser for plug-in parameters."
        par = LinesOf(params)
        plist = []
        tokens = tt.TokenizeAhead(KWParamLexer(par))
        while True:
            # Get keyword token.
            try:
                tkn = next(tokens)
                if tkn.type == 'KW':
                    kw = tkn.value
                else:
                    raise ParamSyntax(
                        ''.join(['Expected keyword, got: ', str(tkn.value)]))
            except StopIteration:
                break
            # Check for '=' and value list.
            vlist = []
            if tokens[0] and tokens[0].type == '=':
                # Pick up value list.
                next(tokens) # Consume the '='.
                while True:
                    vtkn = tokens[0]
                    if vtkn and vtkn.type in ['NUM','STR','KW']:
                        # Treat KW here as an unquotes string.
                        val = vtkn.value
                        next(tokens) # Consume the value.
                    else:
                        break
                    vlist.append(val)
                    if tokens[0] and tokens[0].type == ',':
                        next(tokens) # consume the comma
                    else:
                        break
            plist.append((kw,vlist))
        #print 'plist:',plist
        kw_dict = dict(plist)
        #print 'kw_dict:',kw_dict
        # Now validate the params against kwspec.
        requiredKw = [kw for kw in kwspec if kwspec[kw].req]
        for kw in requiredKw:
            try:
                kw_dict[kw]
            except KeyError:
                raise RequiredKWError(kw)
        for kw in kw_dict:
            try:
                kwspec[kw]
            except KeyError:
                raise InvalidKWError(kw)
        # Normalize floats to expected units.
        for kw in kw_dict:
            kw_dict[kw] = cls._norm_token_vals(kw_dict[kw],kwspec[kw].units)
        # Eliminate redundant value lists.
        for kw in kw_dict:
            if not kwspec[kw].vlist:
                v = kw_dict[kw]
                kw_dict[kw] = v[0] if len(v) else None
        #print 'Final kw_dict:', kw_dict
        return kw_dict
    @classmethod
    def _norm_token_vals(cls, value_list, default_units):
        # If anything has units, and they all match, use that
        # instead of default.
        #print repr(value_list),default_units
        consensus_units = None
        for tkn in value_list:
            try:
                u = tkn.value.du
            except AttributeError:
                pass # Not a Dim().
            else:
                if consensus_units and consensus_units != u:
                    consensus_units = None
                    break # no consensus
                else:
                    consensus_units = u
        u = consensus_units if consensus_units else default_units
        return [Dim.VU(v,u) if default_units and isinstance(v,float) else v \
                for v in value_list]
    @classmethod
    def arg_object(cls, kwargs):
        "Return an ArgObject made from cls.kwspecs and kwargs."
        a = ArgObject()
        for name in cls.kwspecs.keys():
            try:
                setattr(a, name, kwargs[name])
            except KeyError:
                setattr(a, name, None)
        return a        
    @classmethod
    def standard_comments(cls, plugin_name, kw_dict, rules, rule_list):
        "Append a standard set of comments."
        l = []
        l.append('Generated by landmaker ' + str(dt.date.today()))
        try:
            t = rules['copyright']
            l.append(t)
        except RuleNotFound:
            pass
        try:
            t = rules['license']
            l.append(t)
        except RuleNotFound:
            pass
        l.append('Plugin: ' + plugin_name)
        l.append('Parameters: ')
        for kw in kw_dict:
            #units,reqd,isList = kwSpecs[kw]
            v = kw_dict[kw]
            vList = v if isinstance(v,list) else [v]
            dispList = []
            for val in vList:
                dispList.append(str(val))
            disp = ', '.join(dispList)
            l.append('  {0:s}={1:s}'.format(kw, disp))
        l.append('rules:')
        for r in rule_list:
            l.append('  {0:s} = {1:s}'.format(r, str(rules[r])))
        return l
    @classmethod
    def helptext(cls):
        nm = cls.__name__.split('_')[-1]
        yield "No help for " + nm
    @classmethod
    def plugin_name(cls):
        return cls.__name__.split('_')[2]
    @classmethod
    def pin_num_generator(cls, start_num, pin_num_step=1):
        "Generator yielding pin numbers in stepped sequence."
        n = start_num
        while True:
            yield n
            n += pin_num_step
            assert n > 0
    @classmethod   
    def pin_row(cls, p1, p2, num_pins, start_num, pin_num_step=1):
        "Returns list of (pin_num, location) tuples from seed values."
        pitch = p1-p2
        pin_num = cls.pin_num_generator(start_num, pin_num_step)
        return [(next(pin_num),p1+pitch*i) for i in range(num_pins)]
    @classmethod
    def dil_geometry(cls, num_pins, width_oc, pitch_oc, left_geo,
                     right_geo=None, pad1_geo=None):
        x_left, x_right, y_top = cls._dil_alt_setup(num_pins, width_oc, pitch_oc)
        p1,p2 = Pt(x_left, y_top), Pt(x_left, y_top+pitch_oc)
        left_pin_locs = cls.pin_row(p1, p2, num_pins/2, 1)
        p1,p2 = Pt(x_right, y_top), Pt(x_right, y_top+pitch_oc)
        right_pin_locs = cls.pin_row(p1, p2, num_pins/2, num_pins, -1)
        return cls._dil_alt_final(left_geo, right_geo, pad1_geo,
                                  left_pin_locs, right_pin_locs)
    @classmethod
    def alternating_geometry(cls, num_pins, width_oc, pitch_oc, left_geo,
                     right_geo=None, pad1_geo=None):
        x_left, x_right, y_top = cls._dil_alt_setup(num_pins, width_oc, pitch_oc)
        p1, p2 = Pt(x_left, y_top), Pt(x_left, y_top+pitch_oc)
        left_pin_locs = cls.pin_row(p1, p2, num_pins/2, 1, 2)
        p2, p2 = Pt(x_right, y_top), Pt(x_right, y_top + pitch_oc)
        right_pin_locs = cls.pin_row(p1, p2, num_pins/2, 2, 2)
        return cls._dil_alt_final(left_geo, right_geo, pad1_geo,
                                  left_pin_locs, right_pin_locs)
    @classmethod
    def _dil_alt_setup(cls, num_pins, width_oc, pitch_oc):
        if num_pins % 2:
            raise ParamValueError('Must have even number of pins.')
        x_right = width_oc/2.0
        x_left = -x_right
        y_top = ((num_pins/2) - 1) * pitch_oc/2.0
        return (x_left, x_right, y_top)
    @classmethod
    def _dil_alt_final(cls, left_geo, right_geo, pad1_geo,
                       left_pin_locs, right_pin_locs):
        left_geo.mustbe(PinGeometry)
        right_geo = right_geo.mustbe(PinGeometry) if right_geo else left_geo
        pad1_geo = pad1_geo.mustbe(PinGeometry) if pad1_geo else left_geo
        # Making the assumption that pin #1 is first in left_pin_locs
        pin1,left_pin_locs = left_pin_locs[0],left_pin_locs[1:]
        pins = [cls.pinSpec(pin1[1], pin1[0], pad1_geo)]
        pins.extend([cls.pinSpec(loc, n, left_geo)
                     for n, loc in left_pin_locs])
        pins.extend([cls.pinSpec(loc, n, right_geo)
                     for n, loc in right_pin_locs])
        return pins
    def rendering(self, warning_callback):
        raise NotImplementedError('Abstract')

# FIXME: Document standard rule names.
# FIXME: Complete the default rules.
_defaultRules = RulesDictionary([
    ('minspace',   Dim.MIL(8)),
    ('minannulus', Dim.MIL(10)),
    ('mindrill',   Dim.INCH(0.020)),
    ('maskrelief', Dim.MIL(4)),
    ('minsilk',    Dim.MIL(10)),
    ('refdessize', Dim.MIL(40)),
])

_defaultRack = DrillRack(
    [
        Dim.INCH(0.020),
        Dim.INCH(0.025),
        Dim.INCH(0.035),
        Dim.INCH(0.038),
        Dim.INCH(0.042),
        Dim.INCH(0.052),
        Dim.INCH(0.060),
        Dim.INCH(0.086),
        Dim.INCH(0.125),
        Dim.INCH(0.152),
    ],
    {
        'machscrew6':Dim.INCH(0.152),
    }
)

############################################################
# Exported variables and functions.

## rules = RulesDictionary()

ruleSets = {'default':_defaultRules}
drillRacks = {'none':NoRack(), 'default':_defaultRack}


############################################################
# Load and activate plugins.
#
# Plugins must follow strict naming conventions:
# 1. The module fp_<plugin_verb>.py defines the plugin.
# 2. fp_<plugin_verb>.py defines the class FP_<plugin_verb>,
#    derived from Footprint.
# 3. The rendering module defines some base rendering class <rc>.
# 4. The rendering module is assigned a naming <prefix>, by convention
#    indicating the target CAD system.
# 5. Rendering classes are named <prefix>_FP_<plugin_verb>.
#
#    The function deriveRenderingClasses() will automatically generate
#    a declaration for rendering classes, equivalent to:
#        class <prefix>_FP_<plugin_verb>(<rc>,FP_<plugin_verb>):
#            pass
#    Since <rc> occurs first in the multiple inheritence list, it
#    will be searched first when resolving property lookups.
#    This means that lookups to find primitive classes will bind
#    to class variables of <rc> before binding to definitions in
#    Footprint.
#    In cases where the automatically generated rendering class
#    <prefix>_FP_<plugin_verb> does not work, simply declare it in
#    the renderer module before calling deriveRenderingClasses().
#    Automatic generation is suppressed for already-defined classes.
#

# Renderer module structure:
# 1. Import footprintcore
# 2. Derive specialized footprint primitives, if desired.
# 3. Derive a specialized class from Footprint.  References to
#    specialized primitive classes must be provided by overloading
#    the appropriate class variables. This class must implement the
#    rendering() method.
# 4. Connect to the plugins:
#    4.1. call reconnoiterPlugins()
#    4.2. call importPlugins()
#    4.3. (optional) define special case <prefix>_FP_<plugin_verb> classes
#    4.4. call deriveRenderingClasses() for ordinary cases
#    4.5. set the global variable 'fp_plugins' to the return value from
#         collectPlugins()

def reconnoiterPlugins():
    "Return dictionary of module names that look like plugins."
    found = {}
    # Plugins should be in same directory as this file.  If __file__ is
    # not set, bail out.
    try:
        thisFile = __file__
    except NameError:
        print 'Can not identify path to installed plugins.'
        return found
    # List the directory.
    installedPluginDir = os.path.dirname(thisFile)
    ls = os.listdir(installedPluginDir)
    # Look for files named fp_<somename>.py
    moduleNames = [f.split('.')[0] for f in ls if f[0:3] == 'fp_' and f[-3:] == '.py']
    for moduleName in moduleNames:
        puName = moduleName.split('_')[1]
        found[puName] = [moduleName, 'FP_' + puName]
    return found

def importPlugins(plugins, callerGlobals, callerLocals):
    "From each plugin module import the plugin class. Keep reference to module."
    for puName in plugins:
        moduleName, puClass = plugins[puName]
        pluginModule = __import__(moduleName, callerGlobals, callerLocals, [puClass], -1)
        plugins[puName].append(pluginModule)
        
def deriveRenderingClasses(plugins, prefix, renderBase, callerGlobals):
    "Create a rendering class that inherits from the classes: (renderBase, pluginClass)"
    global fpbase
    fpbase = renderBase
    for verb in plugins:
        moduleName, puClass, module = plugins[verb]
        renderClassName = '_'.join([prefix, puClass])
        if renderClassName in callerGlobals:
            # Already defined -- presumably to handle some special case,
            # so don't overwrite that with an automatically generated class.
            continue
        # type() parameters: newClassName, (base classes tuple), dict
        renderClass = \
            type(renderClassName, (renderBase, module.__dict__[puClass]),{})
        callerGlobals[renderClassName] = renderClass
        
def collectPlugins(aModuleDict):
    plugins = {}
    for key in aModuleDict.keys():
        try:
            cadsystem, fp, plugname = key.split('_')
            if fp == 'FP':
                plugins[plugname] = aModuleDict[key]
        except ValueError:
            pass
    return plugins

if __name__ == '__main__':
    pass
    

