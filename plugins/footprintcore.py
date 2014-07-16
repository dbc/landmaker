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

debug = ''

from inspect import stack,getframeinfo
def trace(name, globalVars, localVars=None):
    callerFrameRecord = stack()[1]
    info = getframeinfo(callerFrameRecord[0])
    try:
        v = localVars[name]
    except (TypeError,KeyError):
        v = globalVars[name]
    print '{0:s} = {1:s} ({info.filename}:{info.function}@{info.lineno})'.format(name, repr(v),info=info)


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
        s = self.__class__.__name__ + '('
        s += ','.join([repr(x) for x in self.reprvals()])
        s += ')'
        return s
    def reprvals(self):
        return []

#
# Dim -- linear dimension with prefered diplay units
#
class Dim(FPCoreObj):
    "Linear dimension carrying along prefered display units."
    mmPerMil = 0.0254
    validDisplayUnits = frozenset(['mm','mil','inch'])
    def __init__(self, mmValue, displayUnits=None):
        if displayUnits:
            self._v = float(mmValue)
            self.du = displayUnits
        else:
            if isinstance(mmValue,str):
                t = self.__class__.fromStr(mmValue)
                self._v = t._v
                self.du = t.du
            elif isinstance(mmValue,Dim):
                self._v = mmValue._v
                self.du = mmValue.du
            elif mmValue == None:
                return None # FIXME: add unit test
            else:
                raise ValueError(' '.join(['Can not convert',repr(mmValue),repr(displayUnits),'to Dim.']))
##        if isinstance(mmValue,Dim):
##            displayUnits = mmValue.du
##        elif isinstance(mmValue, str):
##            return self.__class__.parse(mmValue)
##        # canonical value is millimeters.
##        self._v = float(mmValue)
##        self.du = displayUnits
    def reprvals(self):
        return [self._v, self.du]
    @property
    def du(self):
        return self._du
    @du.setter
    def du(self, displayUnits):
        if not displayUnits in self.validDisplayUnits:
            raise ValueError (str(displayUnits) + ' not a valid display unit.')
        self._du = displayUnits
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
        return cls(float(v) * cls.mmPerMil, 'mil')
    @classmethod
    def INCH(cls,v):
        "Construct from inches."
        return cls(float(v) * cls.mmPerMil * 1000.0, 'inch')
    @classmethod
    def DRILL(cls,v):
        "Construct from #nn drill number."
        # Look up via DrillRack class method.
        try:
            return DrillRack.number[v]
        except:
            raise ValueError(v + ' drill size not found.')
    @classmethod
    def VU(cls, v, displayUnits):
        "Construct from display units specified in variable."
        if displayUnits in ['mil','thou']:
            return cls.MIL(v)
        if displayUnits == 'mm':
            return cls.MM(v)
        if displayUnits in ['inch','in']:
            return cls.INCH(v)
        raise ValueError(repr(displayUnits) + ' is not a valid display unit.')
    @classmethod
    def fromStr(cls, s, defaultUnits=None):
        "Construct from string consisting of number and unit keyword."
        mo = re.match(r'([0-9.]+)(\s*)(mm|mil|inch|in)?\Z', s.strip())
        if mo:
            v = float(mo.group(1))
            du = mo.group(3) if mo.group(3) else defaultUnits
            return cls.VU(v,du)
        elif s.startswith('#'):
            return cls.DRILL(s)
        else:
            raise ValueError(s + ' not convertable to Dim().')
    @classmethod
    def guessDu(cls, dimList, du):
        "Try to extract display units from a list of objects that might be Dim()'s."
        for d in dimList:
            try:
                return d.du
            except AttributeError:
                pass
        return du
    @classmethod
    def OrZero(cls, v, du):
        "Make sure v is a Dim(), or turn a zero into a Dim."
        return v if isinstance(v, cls) else cls(0, du)
    @classmethod
    def OrNone(cls, v):
        "Make sure v is either a Dim() or None."
        if isinstance(v, cls) or v == None:
            return v
        raise TypeError('Expected Dim() or None.')
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
        return self._v / self.mmPerMil
    @mil.setter
    def mil(self, v):
        self._v = float(v) * self.mmPerMil
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
            # try to unpack an iterable, let exception bubble up.
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
    def spansOrg(self, other):
        "True if rectangle defined by self,other contains Pt(0,0)."
        p1,p2 = self.rectify(other)
        org = Pt.MM(0,0)
        return p1 < org and org < p2
    def leftOf(self, other):
        return self.x < other.x
    def rightOf(self, other):
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
    def onAxis(self):
        "True if on either X or Y axis."
        # FIXME: write unit test
        return self.x == 0.0 or self.y == 0.0
    @property
    def reflox(self):
        "Reflect over X axis."
        return Pt(self.x, -self.y)
    @property
    def refloy(self):
        "Reflect over Y axis."
        return Pt(-self.x, self.y)
    def minSpan(self, other):
        a,b = self.rectify(other)
        return Dim(min([b.x-a.x, b.y-a.y]), self.x.du)
    def rotate(self, other, pivot=None):
        raise NotImplementedError('FIXME')
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
        return Pt(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Pt(self.x - other.x, self.y - other.y)
    def __neg__(self):
        return Pt(-self.x, -self.y)
    def __pos__(self):
        return Pt(self.x, self.y)
    # Multiply/divide point by a scalar (float or Dim)
    def __mul__(self, other):
        m = float(other)
        return Pt(self.x*m, self.y*m)
    def __rmul__(self, other):
        return self.__mul__(other)
    def __div__(self, other):
        m = float(other)
        return Pt(self.x/m, self.y/m)
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
    def __init__(self, drillList = [], symbolic={}):
        self._dl = sorted(drillList)
        self._symb = symbolic
    def drills(self):
        return self._dl[:]
    def symbolics(self):
        return self._symb.copy()
    def reprvals(self):
        return [self._dl, self._symb]
    def addDrill(self, aDrill):
        if not isinstance(aDrill, Dim):
            raise TypeError("Drills must be specified as Dim()'s")
        existing = self[aDrill]
        if existing == aDrill: return # Avoid adding redundant drills.
        self._dl.append(aDrill)
        self._dl = sorted(self._dl)
    def addSymbolic(self, aName, aDrill):
        if not isinstance(aName, str): raise TypeError('Expected string.')
        if not isinstance(aDrill, Dim): raise TypeError('Drills must be Dim().')
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
        if not isinstance(v, Dim): raise TypeError('Drills must be Dim().')
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
    def addDrill(self, aDrill):
        print "Can't add to drill rack 'none'."
    def addSymbolic(self, aName, aDrill):
        print "Can't add to drill rack 'none'."

#
# Footprint primitives.
#
class Primitive(FPCoreObj):
    "Footprints must consist entirely of primitives."
    def __init__(self, loc):
        self.loc = loc
    def reprvals(self):
        return [self._loc]
    @property
    def loc(self):
        return self._loc
    @loc.setter
    def loc(self, v):
        # FIXME: Perhasps should just call Pt() constructor, let it throw exception.
        if not isinstance(v,Pt):
            raise TypeError('Location must be a Pt().')
        self._loc = v

class Pad(FPCoreObj):
    "Pads are sub-prititives of the PinGeometry sub-primitive."
    def __init__(self, clearance, maskRelief):
        self.clearance = clearance
        self.maskRelief = maskRelief
    def reprvals(self):
        return [self.clearance, self.maskRelief]
    @property
    def clearance(self):
        return self._clearance
    @clearance.setter
    def clearance(self, v):
        dv = Dim(v)
        if dv < 0:
            raise ValueError('Clearance must be >= zero.')
        self._clearance = dv
    @property
    def maskRelief(self):
        return self._relief
    @maskRelief.setter
    def maskRelief(self, v):
        dv = Dim(v)
        if dv < 0:
            # FIXME: What about tenting??? Maybe should allow
            # relief down to -dia/2 -- will need to delgate check to subclasses.
            # or add a lower-limit property to subclass -- but have an __init__()
            # order issue in that case.
            raise ValueError('Mask relief must be >= zero.')
        self._relief = dv
    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.clearance == other.clearance \
               and self.maskRelief == other.maskRelief
    def covers(self, other):
        "Returns True if self covers other pad."
        raise NotImplementedError('Abstract')
    def extents(self):
        "Returns list of Pt()'s to be checked by cover()."
        raise NotImplementedError('Abstract')
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        raise NotImplementedError('Abstract')
    def validAnnulus(self, aDrill, rules):
        "Pad size minus drill size must be >= minannulus."
        return self.annulus(aDrill) >= rules['minannulus']
        

class RoundPad(Pad):
    def __init__(self, diameter, clearance, maskRelief):
        Pad.__init__(self, clearance, maskRelief)
        self.dia = diameter
    @property
    def dia(self):
        return self._dia
    @dia.setter
    def dia(self, v):
        dv = Dim(v)
        if dv <= 0.0:
            raise ValueError ('Diameter must be > 0.')
        self._dia = dv        
    def reprvals(self):
        return [self.dia, self.clearance, self.maskRelief]
    def __eq__(self, other):
        return super(RoundPad,self).__eq__(other) \
               and self.dia == other.dia
    def extents(self):
        # Aproximate the extents by 8 points around the circle.
        w2 = self.dia/2.0
        du = w2.du
        l = [Pt(w2,Dim(0,du)), Pt(-w2, Dim(0,du)),
             Pt(Dim(0,du), w2), Pt(Dim(0,du),-w2)]
        r = w2 * 0.707
        l.extend([Pt(r,r),Pt(r,-r),Pt(-r,r),Pt(-r,-r)])
        return l
    def covers(self, other):
        if isinstance(other, RoundPad):
            return self.dia >= other.dia
        r = self.dia / 2.0
        for p in other.extents():
            if len(p) > r:
                return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return (self.dia - aDrill)/2.0

class SquarePad(Pad):
    def __init__(self, width, clearance, maskRelief):
        Pad.__init__(self, clearance, maskRelief)
        self.width = width
    def reprvals(self):
        return [self.width, self.clearance, self.maskRelief]
    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, v):
        w = Dim(v)
        if w < 0.0:
            raise ValueError('Width must be > 0.')
        self._width = w
    @property
    def dia(self):
        # symnonym for width
        return self.width
    def __eq__(self, other):
        return super(SquarePad,self).__eq__(other) \
               and self.width == other.width
    def extents(self):
        w2 = self.width/2.0
        return [Pt(-w2,-w2), Pt(w2,-w2), Pt(-w2, w2), Pt(w2,w2)]
    def covers(self, other):
        if isinstance(other, SquarePad):
            return self.width >= other.width
        if isinstance(other, RoundPad):
            return self.width >= other.dia
        w2 = self.width/2.0
        ll,ur = Pt(-w2,-w2),Pt(w2,w2)
        for p in other.extents():
            if p.leftOf(ll) or p.below(ll) or p.rightOf(ur) or p.above(ur):
                return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return (self.width - aDrill)/2.0
        

class RectPad(Pad):
    def __init__(self, p1, p2, clearance, maskRelief):
        Pad.__init__(self, clearance, maskRelief)
        # FIXME: Should call Pt() constructors? or type check?
        if p1.spansOrg(p2):
            self.ll,self.ur = p1.rectify(p2)
        else:
            raise ValueError('Pad must surround (0,0).')
    @classmethod
    def fromLWO(cls, length, width, clearance, maskRelief, orientation = 'h'):
        "Construct from length, width, and orientation."
        l = Dim(length)
        w = Dim(width)
        if orientation not in 'hv':
            raise ValueError("Orientation must be 'h' or 'v'.")
        x,y = (l/2,w/2) if orientation == 'h' else (w/2,l/2)
        return cls(Pt(-x,-y),Pt(x,y), clearance, maskRelief)
    @classmethod
    def fromPad(cls, aPad):
        "Construct RectPad from a SquarePad."
        w = aPad.width
        p1,p2 = Pt(-w,-w),Pt(w,w)
        return cls(p1, p2, aPad.clearance, aPad.maskRelief)
    def stretch(self, amount,  direction): 
        "Stretch the pad in given direction."
        try:
            amt = abs(Dim(amount) )
        except ValueError:
            # Hmmm... well... get a bigger hammer and try again.
            amt = abs(Dim(float(amount), self.loc.du))
        zero = amt.u0
        if direction in ['x', '+x']:
            self.ur += Pt(amt, zero)
        elif direction == '-x':
            self.ll -= Pt(amt, zero)
        elif direction in ['y', '+y']:
            self.ur += Pt(zero, amt)
        elif direction == '-y':
            self.ll -= Pt(zero, amt)
        else:
            raise ValueError('Stretch direction must be one of: x,+x,-x,y,+y,-y')
    def reprvals(self):
        return [self.ll, self.ur , self.clearance, self.maskRelief]
    def __eq__(self, other):
        return super(RectPad,self).__eq__(other) \
               and self.ll == other.ll \
               and self.ur == other.ur
    def extents(self):
        return [self.ll, self.ur,
                pt(self.ll.x, self.ur.y), pt(self.ur.x, self.ll.y)]
    def covers(self, other):
        for p in other.extents():
            if p.leftOf(self.ll): return False
            if p.below(self.ll): return False
            if p.rightOf(self.ur): return False
            if p.above(self.ur): return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return min([abs(self.ll.x), abs(self.ll.y), abs(self.ur.x), abs(self.ur.y)]) \
               - aDrill/2.0
##    @property
##    def roundEnds(self):
##        return False
        

class RoundedRectPad(RectPad):
    def __init__(self, p1, p2, clearance, maskRelief, radius=None):
        RectPad.__init__(self, p1, p2, clearance, maskRelief)
        self.radius = radius
    # FIXME: needs constructor LWRO
    # FIXME: implement specialized extents(), covers(), annulus()
    @classmethod
    def fromPad(cls, aPad):
        radius = aPad.dia/2.0
        p = Pt(radius, radius)
        return cls(p,  -p,  aPad.clearance,  aPad.maskRelief, radius)
    @classmethod
    def fromRectPad(cls,  rectPad, radius=None):
        return cls(rectPad.ll, rectPad.ur, rectPad.clearance,
                   rectPad.maskRelief, radius)
##    @classmethod
##    def stretch(cls, aPad, stretch):
##        "Constructor, make RoundedRectPad by stretching a RoundPad."
##        t = RectPad.stretch(cls, aPad, stretch)
##        t.radius = aPad.dia/2.0
##        return t
    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, v):
        r = Dim(v)
        halfSpan = self.ll.minSpan(self.ur)/2.0
        if r and r > halfSpan:
            raise ValueError('Radius larger than 1/2 width.')
        self._radius = r
##    @property
##    def roundEnds(self):
##        return True
        
class PinGeometry(FPCoreObj):
    "PinGeometry is a sub-primitive of the PinSpec primitive."
    #FIXME: Be sure compPad==None and solderPad==Pad() works, otherwise
    # won't be able to do double-sided edge connectors correctly.
    def __init__(self, compPad, drill=None, solderPad=None, innerPad=None):
        self.compPad = compPad
        self.drill = drill
        self.solderPad = solderPad
        self.innerPad = innerPad
    @property
    def compPad(self):
        return self._compPad
    @compPad.setter
    def compPad(self, aPad):
        if not isinstance(aPad, Pad):
            raise TypeError('Expected Pad().')
        try:
            if self._solderPad == '=':
                # Trap case where breaking symmetry.
                self._solderPad = self._compPad
            # FIXME: if setting compPad equal to solderPad, should
            # check symmetry and set '=' if necessary.
        except AttributeError:
            pass # _solderPad not yet set.
        self._compPad = aPad
    @property
    def drill(self):
        return self._drill
    @drill.setter
    def drill(self, aDrill):
        if not (aDrill == None or isinstance(aDrill, Dim)):
            raise TypeError('Expected Dim() or None.')
        self._drill = aDrill
    @property
    def solderPad(self):
        return self._compPad if self._solderPad == '=' else self._solderPad
    @solderPad.setter
    def solderPad(self, aPad):
        if not(aPad == None or aPad == '=' or isinstance(aPad,Pad)):
            raise ValueError("Solder pad must be None, '=', or Pad().")
        #if aPad == None or aPad == self.compPad:
        if aPad == self.compPad:
            # Trap redundant solderPad value and force to symmetric.
            self._solderPad = '='
        else:
            self._solderPad = aPad
        if 'p' in debug:
            print '_solderPad:',self._solderPad, self.solderPad
    @property
    def symmetric(self):
        return self._solderPad == '=' or self._compPad == self._solderPad
    @property
    def innerPad(self):
        return self._innerPad
    @innerPad.setter
    def innerPad(self, aPad):
        if aPad != None: raise NotImplementedError('Inner pads not yet supported.')
        self._innerPad = aPad
    def reprvals(self):
        l = [self.compPad]
        if self.drill != None or self.solderPad != None or self.innerPad != None:
            l.append(self.drill)
        if self.solderPad != None or self.innerPad != None:
            l.append(self._solderPad)
        if self.innerPad != None:
            l.append(self.innerPad)
        return l
    def valid(self, rules):
        if not self.compPad.validAnnulus(self.drill, rules): return False
        if not (self.symmetric or self.compPad.validAnnulus(self.drill, rules)): return False
        if self.drill < rules['mindrill']: return False        

class PinInfo(Primitive):
    # FIXME: Refactor pin number and pin name down here.
    # although, PinGang should not reach num and name down here.
    pass

class PinSpec(PinInfo):
    def __init__(self, loc, pinNumber, pinGeometry, rotation = 0, pinName = None):
        super(PinSpec, self).__init__(loc)
        self.num = int(pinNumber)
        if not isinstance(pinGeometry, PinGeometry):
            raise TypeError('Expected PinGeometry().')
        self.geo = pinGeometry
        self.rot = rotation
        if pinName is not None:
            self._name = str(pinName)
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
        
class PinGang(PinInfo):
    def __init__(self, gangMaskRelief, pinList):
        self.relief = gangMaskRelief # Mask relief at the extents of extreme pads.
        self.pins = pinList # List of PinSpec() instances.
    def reprvals(self):
        return [self.relief, self.pins]
    @property
    def relief(self):
        return self._relief
    @relief.setter
    def relief(self, v):
        if not isinstance(v, Dim): raise TypeError('Gang mask relief must be Dim().')
        self._relief = v
    @property
    def pins(self):
        return self._pins
    @pins.setter
    def pins(self, l):
        # Raise TypeError if not all elements of list l are PinSpec.
        if not min([isinstance(x, PinSpec) for x in l]):
            raise TypeError("List must contain PinSpec()'s.")
        self._silk = l

class ThermalSink(PinInfo):
    "Primtive defining a thermal sink area."
    def __init__(self, loc, comp_cu, comp_mask, solder_cu, solder_mask, drills,
                 pin_number, pin_name = ''):
        self.loc = loc
        self.num = int(pin_number)
        self.name = pin_name if pin_name else str(pin_number)
        self.comp_cu = self._check_poly(comp_cu)
        self.comp_mask = self._check_mpoly(comp_mask)
        self.solder_cu = self._check_poly(solder_cu)
        self.solder_mask = self._check_mpoly(solder_mask)
        self.drills = self._check_drills(drills)
    def _check_poly(self, gon):
        if not gon:
            return []
        if not min([isinstance(x,Pt) for x in gon]):
            raise ValueError('Polygon must be list of points.')
        if len(gon) < 3:
            raise ValueError('Polygon must contain at least 3 points.')
        return gon
    def _check_mpoly(self, manygons):
        if not manygons:
            return []
        if not isinstance(manygons[0],list):
            manygons = [manygons]
        return [self._check_poly(gons) for gons in manygons]
    def _check_drills(self, drls):
        if not drls:
            return []
        if not min([isinstance(p,Pt) and isinstance(d,Dim) for
                    p,d in drls]):
            raise ValueError('Drill list must be tuples of (Pt(),Dim()).')
        return drls
    
class Silk(Primitive):
    def __init__(self, loc, penWidth):
        super(Silk, self).__init__(loc)
        self.penWidth = penWidth
    @property
    def penWidth(self):
        return self._pw
    @penWidth.setter
    def penWidth(self, v):
        if not isinstance(v, Dim): raise TypeError('Expected Dim().')
        self._pw = v
    
class SilkText(Silk):
    def __init__(self, loc, rotation, penWidth, text, size):
        super(SilkText, self).__init__(loc, penWidth)
        self.rot = rotation
        self.text = str(text) if text != None else ''
        if not (isinstance(size, Dim)):
            raise TypeError('ExpectedDim()')
        if size <= 0.0:
            raise ValueError('Silk width must be > 0.')
        self.size = size # FIXME: Validate is Positive Dim().
    def reprvals(self):
        #return [self.x, self.y, self.rot, self._pw, self.text, self._sz]
        return [self.loc, self.rot, self.penWidth, self.text, self.size]
##    @property
##    def size(self):
##        return rules[self._sz]
##    @size.setter
##    def size(self, v):
##        if not isinstance(v, Dim): raise ValueError
##        self._sz = v

class RefDes(SilkText):
    pass

class SilkLine(Silk):
    def __init__(self, p1, p2, penWidth):
        super(SilkLine, self).__init__(p1, penWidth)
        self.p2 = Pt(p2)

class SilkArc(Silk):
    "Fixed radius arc."
    def __init__(self, loc, radius, startAngle, arcAngle, penWidth):
        super(SilkArc, self).__init__(loc, penWidth)
        if not isinstance(radius, Dim): raise TypeError ('radius must be Dim().')
        self.radius = radius
        if startAngle < 0.0 or startAngle > 360.0:
            raise ValueError('Angle must be in range 0..360')
        self.start = startAngle
        if arcAngle < 0.0 or arcAngle > 360.0:
            raise ValueError('Arc length must be between 0 and 360.')
        self.arc = arcAngle

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
    def typeKW(cls, s, lexposIgnored):
##        if s in cls.keywords:
##            return cls(cls.keywords[s],s)
        return cls('KW',s)
    @classmethod
    def typePunct(cls, s, lexposIgnored):
        return cls(s,s)
    @classmethod
    def typeNum(cls, s, lexposIgnored):
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
    def typeStr(cls, s, lexposIgnored):
        end = -1 if s[-1] in '"\'' else None
        return cls('STR',s[1:end])
    @classmethod
    def typeBad(cls, s, lexposIgnored):
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
        (r'[a-zA-Z][a-zA-Z0-9_]*', KWToken.typeKW), # Keyword/identifier, etc.
        (r'[0-9]*[\.][0-9]+\s*(mm|mil|inch|in)?', KWToken.typeNum), # Float.
        (r'[0-9]+\s*(mm|mil|inch|in)?', KWToken.typeNum), # Integer.
        (r'#([0-9]+|[A-Z])', KWToken.typeNum), # A number/letter drill.
        (r'".*"', KWToken.typeStr), # Quoted matter using "
        (r"'.*'", KWToken.typeStr), # Quoted matter using '
        (r'".*$', KWToken.typeStr), # Missing close " -- take it all :/
        (r"'.*$", KWToken.typeStr), # Missing close ' -- take it all
        (r'\s*',None), # Ignore white space.
        (r'[=,]', KWToken.typePunct), # Valid punctuation
        (r'.',KWToken.typeBad), # Catch-all
    ]

class Footprint(FPCoreObj):
    # Plugins MUST instantiate primitive and sub-primitive classes
    # via these class variables so that rendering classes may
    # provide alternate specializations of them.
    roundPad = RoundPad
    squarePad = SquarePad
    rectPad = RectPad
    roundedRectPad = RoundedRectPad
    pinGeometry = PinGeometry
    pinSpec = PinSpec
    pinGang = PinGang
    silkText = SilkText
    refDes = RefDes
    silkLine = SilkLine
    silkArc = SilkArc
    keepOutRect = KeepOutRect
    thermalSink = ThermalSink
    def __init__(self, name, description, refdes, pins = [], silk = [], \
                 comments = [], keepOuts = []):
        self.name = str(name) if name is not None else ''
        self.desc = str(description) if description is not None else ''
        assert refdes != None
        if isinstance(refdes, str):
            refdes = self.refDes(0,0,0,'textpen',refdes,'refdessize')
        if not isinstance(refdes, RefDes): raise TypeError('Expected RefDes() or str().')
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
    def parse(cls, footprintname, params, rules, rack, warningCallback):
        raise NotImplementedError('Abstract')
    @classmethod
    def parseKwargs(cls, params, kwspec = {}):
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
        kwdict = dict(plist)
        #print 'kwdict:',kwdict
        # Now validate the params against kwspec.
        requiredKw = [kw for kw in kwspec if kwspec[kw].req]
        for kw in requiredKw:
            try:
                kwdict[kw]
            except KeyError:
                raise RequiredKWError(kw)
        for kw in kwdict:
            try:
                kwspec[kw]
            except KeyError:
                raise InvalidKWError(kw)
        # Normalize floats to expected units.
        for kw in kwdict:
            kwdict[kw] = cls._normTokenVals(kwdict[kw],kwspec[kw].units)
        # Eliminate redundant value lists.
        for kw in kwdict:
            if not kwspec[kw].vlist:
                v = kwdict[kw]
                kwdict[kw] = v[0] if len(v) else None
        #print 'Final kwdict:', kwdict
        return kwdict
    @classmethod
    def _normTokenVals(cls, value_list, default_units):
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
    def standardComments(cls, pluginName, kwDict, rules, ruleList):
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
        l.append('Plugin: ' + pluginName)
        l.append('Parameters: ')
        for kw in kwDict:
            #units,reqd,isList = kwSpecs[kw]
            v = kwDict[kw]
            vList = v if isinstance(v,list) else [v]
            dispList = []
            for val in vList:
                dispList.append(str(val))
            disp = ', '.join(dispList)
            l.append('  {0:s}={1:s}'.format(kw, disp))
        l.append('rules:')
        for r in ruleList:
            l.append('  {0:s} = {1:s}'.format(r, str(rules[r])))
        return l
    @classmethod
    def helptext(cls):
        nm = cls.__name__.split('_')[-1]
        yield "No help for " + nm
    @classmethod
    def pluginName(cls):
        return cls.__name__.split('_')[2]
    @classmethod
    def dil_geometry(cls, num_pins, width_oc, pitch_oc, left_geo,
                     right_geo=None, pad1_geo=None):
        x_left, x_right, y_top = cls._dil_alt_setup(num_pins, width_oc, pitch_oc)
        left_pin_locs = [(Pt(x_left, y_top-(pitch_oc*ymult)), n)
                         for ymult, n in
                         enumerate([n+1 for n in range(0,num_pins/2)])]
        right_pin_locs = [(Pt(x_right, y_top-(pitch_oc*ymult)), n)
                         for ymult, n in
                         enumerate([num_pins-n for n in range(0,num_pins/2)])]
        return cls._dil_alt_final(left_geo, right_geo, pad1_geo,
                                  left_pin_locs, right_pin_locs)
    @classmethod
    def alternating_geometry(cls, num_pins, width_oc, pitch_oc, left_geo,
                     right_geo=None, pad1_geo=None):
        x_left, x_right, y_top = cls._dil_alt_setup(num_pins, width_oc, pitch_oc)
        left_pin_locs = [(Pt(x_left, t_top-(pitch_oc*ymult)), n)
                        for ymult, n in
                        enumerate([n+1 for n in range(0, num_pins/2, 2)])]
        right_pin_locs = [(Pt(x_left, t_top-(pitch_oc*ymult)), n)
                        for ymult, n in
                        enumerate([n+2 for n in range(0, num_pins/2, 2)])]
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
        if not isinstance(left_geo, PinGeometry):
            raise ValueError('Expected PinGeometry, got: '+repr(left_geo))
        right_geo = right_geo if right_geo else left_geo
        pad1_geo = pad1_geo if pad1_geo else left_geo
        if not isinstance(right_geo, PinGeometry):
            raise ValueError('Expected PinGeometry, got: '+repr(right_geo))
        if not isinstance(pad1_geo, PinGeometry):
            raise ValueError('Expected PinGeometry, got: '+repr(pad1_geo))
        # Making the assumption that pin #1 is first in left_pin_locs
        pin1,left_pin_locs = left_pin_locs[0],left_pin_locs[1:]
        pins = [cls.pinSpec(pin1[0], pin1[1], pad1_geo)]
        pins.extend([cls.pinSpec(loc, n, left_geo)
                     for loc, n in left_pin_locs])
        pins.extend([cls.pinSpec(loc, n, right_geo)
                     for loc, n in right_pin_locs])
        return pins
    def rendering(self, warningCallback):
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
    

