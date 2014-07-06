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

class Dim(FPCoreObj):
    "Linear dimension carrying along prefered display units."
    mmPerMil = 0.0254
    validDisplayUnits = frozenset(['mm','mil','inch'])
    def __init__(self, mmValue, displayUnits):
        # canonical value is millimeters.
        self._v = float(mmValue)
        self.du = displayUnits
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
        raise ValueError(str(displayUnits) + ' is not a valid display unit.')
    @classmethod
    def fromStr(cls, s, defaultUnits):
        "Construct from string consisting of number and unit keyword."
        mo = re.match(r'([0-9.]+)(\s*)(mm|mil|inch|in)?\Z', s.strip())
        if mo:
            v = mo.group(1)
            du = mo.group(3) if mo.group(3) != None else defaultUnits
            return cls.VU(v,du)
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
    # Arithmetic operators can take two Dim() instances, or
    # one Dim() and one float()'able operand.  Display units are
    # taken from the left-hand operand in the case of two Dim()'s.
    # Arithmetic doesn't need scaling, since everything is stored
    # in millimeters as the canonical representation.
    def __int__(self):
        return int(self._v)
    def __float__(self):
        return self._v
    def __add__(self, other):
        return self.__class__(self._v + float(other), self.du)
    def __radd__(self, other):
        return self.__add__(other)
    def __sub__(self, other):
        return self.__class__(self._v - float(other), self.du)
    def __rsub__(self, other):
        return self.__class__(float(other)-self._v, self.du)
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
        return self._v < float(other)
    def __ge__(self, other):
        return self._v >= float(other)
    def __le__(self, other):
        return self._v <= float(other)
    def __gt__(self, other):
        return self._v > float(other)
    def __eq__(self, other):
        if other==None: return False
        return self._v == float(other)
    def __ne__(self, other):
        if other==None: return True
        return self._v != float(other)
    def __abs__(self):
        return Dim(abs(self._v), self.du)
        
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
    def __init__(self, x, y, displayUnits=None):
        du = Dim.guessDu([x,y],displayUnits)
        self.x = Dim.OrZero(x,du)
        self.y = Dim.OrZero(y,du)
    def reprvals(self):
        return [self.x, self.y]

class Pad(FPCoreObj):
    "Pads are sub-prititives of the PinGeometry sub-primitive."
    def __init__(self, clearance, maskRelief, displayUnits=None):
        du = Dim.guessDu([clearance, maskRelief], displayUnits)
        self.clearance = Dim.OrZero(clearance,du)
        self.relief = Dim.OrZero(maskRelief,du)
    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.clearance == other.clearance \
               and self.relief == other.relief
    def covers(self, other):
        "Returns True if self covers other pad."
        raise NotImplementedError('Abstract')
    def extents(self):
        "Returns list of (x,y) tuples to be checked by cover()."
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
        if not (isinstance(diameter, Dim)): 
            raise TypeError ('Expected Dim().')
        if diameter <= 0.0:
            raise ValueError ('Diameter must be > 0.')
        self.dia = diameter
    def reprvals(self):
        return [self.dia, self.clearance, self.relief]
    def __eq__(self, other):
        return super(RoundPad,self).__eq__(other) \
               and self.dia == other.dia
    def extents(self):
        # Aproximate the extents by 8 points around the circle.
        w2 = self.dia/2.0
        l = [(w2,0), (-w2, 0), (0, w2), (0,-w2)]
        r = w2 * 0.707
        l.extend([(r,r),(r,-r),(-r,r),(-r,-r)])
        return l
    def covers(self, other):
        if isinstance(other, RoundPad):
            return self.dia >= other.dia
        r = self.dia / 2.0
        for x,y in other.extents():
            if m.sqrt(x**2.0 + y**2.0) > r:
                return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return self.dia - aDrill

class SquarePad(Pad):
    def __init__(self, width, clearance, maskRelief):
        Pad.__init__(self, clearance, maskRelief)
        if not (isinstance(width, Dim)):
            raise TypeError('Expected Dim().')
        if width <= 0.0:
            raise ValueError('Width must be > 0.')
        self.width = width
    def reprvals(self):
        return [self.width, self.clearance, self.relief]
    def __eq__(self, other):
        return super(SquarePad,self).__eq__(other) \
               and self.width == other.width
    def extents(self):
        w2 = self.width/2.0
        return [(w2,w2), (w2,-w2), (-w2, w2), (-w2,-w2)]
    def covers(self, other):
        if isinstance(other, SquarePad):
            return self.width >= other.width
        if isinstance(other, RoundPad):
            return self.width >= other.dia
        w2 = self.width/2.0
        xmin, xmax, ymin, ymax = -w2, w2, -w2, w2
        for x,y in other.extents():
            if x < xmin: return False
            if x > xmax: return False
            if y < ymin: return False
            if y > ymin: return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return self.width - aDrill
        

class RectPad(Pad):
    def __init__(self, x1, y1, x2, y2, clearance, maskRelief, displayUnits=None):
        du = Dim.guessDu([x1,y1,x2,y2,clearance,maskRelief],displayUnits)
        Pad.__init__(self, clearance, maskRelief)
        # extents() and covers() depend on canonicalizing value orders.
        xmin = min([x1, x2])
        xmax = max([x1, x2])
        ymin = min([y1, y2])
        ymax = max([y1, y2])
        if xmin >= 0.0 or xmax <= 0.0 or ymin >= 0.0 or ymax <= 0.0:
            raise ValueError('Pad must surround (0,0).')
        self.x1 = xmin
        self.y1 = ymin
        self.x2 = xmax
        self.y2 = ymax
    @classmethod
    def stretch(cls, aPad, xAmount, yAmount):
        "Constructor, make RectPad by stretching a SquarePad."
        r = aPad.width/2.0
        return cls._stretch(r, xAmount, yAmount, aPad.clearance, aPad.relief)
    @classmethod
    def _stretch(cls, radius, xAmount, yAmount, clearance, relief):
        "Implement stretching."
        assert radius > 0.0
        if xAmount != 0.0 and yAmount != 0.0:
            raise InternalError('Can only stretch in one dimension.')
        if xAmount != 0.0:
            x1 = -radius + xAmount if xAmount < 0.0 else -radius
            x2 = radius + xAmount if xAmount > 0.0 else radius
        else:
            x1 = -radius
            x2 = radius
        y1 = -radius + yAmount if yAmount < 0.0 else -radius
        y2 = radius + yAmount if yAmount > 0.0 else radius
        return cls(x1, y1, x2, y2, clearance, relief)
    def reprvals(self):
        return [self.x1, self.y1, self.x2, self.y2, self.clearance, self.relief]
    def __eq__(self, other):
        return super(RectPad,self).__eq__(other) \
               and self.x1 == other.x1 \
               and self.x2 == other.x2 \
               and self.y1 == other.y1 \
               and self.y2 == other.y2
    def extents(self):
        return [(self.x1, self.y1), (self.x1, self.y2),
                (self.x2, self.y1), (self.x2, self.y2)]
    def covers(self, other):
        for x,y in other.extents():
            if x < self.x1: return False
            if x > self.x2: return False
            if y < self.y1: return False
            if y > self.y2: return False
        return True
    def annulus(self, aDrill):
        "Return minimum copper width if drilled at (0,0) by aDrill."
        return min([abs(self.x1), abs(self.x2), abs(self.y1), abs(self.y2)]) \
               - aDrill
    @property
    def roundEnds(self):
        return False
        

class RoundedRectPad(RectPad):
    # FIXME: implement specialized extents(), covers(), annulus()
    @classmethod
    def stretch(cls, aPad, xAmount, yAmount):
        "Constructor, make RoundedRectPad by stretching a RoundPad."
        r = aPad.dia/2.0
        return cls._stretch(r, xAmount, yAmount, aPad.clearance, aPad.relief)
    @property
    def roundEnds(self):
        return True
        
class PinGeometry(FPCoreObj):
    "PinGeometry is a sub-primitive of the PinSpec primitive."
    #FIXME: Be sure compPad==None and solderPad==Pad() works, otherwise
    # won't be able to do double-sided edge connectors correctly.
    def __init__(self, compPad, drill=None, solderPad=None, innerPad=None):
        self.drill = drill
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
        if aPad == None or aPad == self.compPad:
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
    def reprvals(self):
        l = [self.compPad]
        if drill != None or solderPad != None or innerPad != None:
            l.append(self.drill)
        if solderPad != None or innerPad != None:
            l.append(self._solderPad)
        if innerPad != None:
            l.append(self.innerPad)
        return l
    def valid(self, rules):
        if not self.compPad.validAnnulus(self.drill, rules): return False
        if not (self.symmetric or self.compPad.validAnnulus(self.drill, rules)): return False
        if self.drill < rules['mindrill']: return False        

class PinInfo(Primitive):
    pass

class PinSpec(PinInfo):
    def __init__(self, x, y, pinNumber, pinGeometry, rotation = 0, pinName = None):
        super(PinSpec, self).__init__(x,y)
        self.num = int(pinNumber)
        if not isinstance(pinGeometry, PinGeometry):
            raise TypeError('Expected PinGeometry().')
        self.geo = pinGeometry
        self.rot = rotation
        if pinName != None:
            self._name = str(pinName)
    def reprvals(self):
        l = [self.x, self.y, self.num, self.geo]
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
    
class Silk(Primitive):
    def __init__(self, x, y, penWidth):
        super(Silk, self).__init__(x,y)
        self.penWidth = penWidth
    @property
    def penWidth(self):
        return self._pw
    @penWidth.setter
    def penWidth(self, v):
        if not isinstance(v, Dim): raise TypeError('Expected Dim().')
        self._pw = v
    
class SilkText(Silk):
    def __init__(self, x, y, rotation, penWidth, text, size):
        super(SilkText, self).__init__(x,y, penWidth)
        self.rot = rotation
        self.text = str(text) if text != None else ''
        if not (isinstance(size, Dim)):
            raise TypeError('ExpectedDim()')
        if size <= 0.0:
            raise ValueError('Silk width must be > 0.')
        self.size = size # FIXME: Validate is Positive Dim().
    def reprvals(self):
        #return [self.x, self.y, self.rot, self._pw, self.text, self._sz]
        return [self.x, self.y, self.rot, self.penWidth, self.text, self.size]
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
    def __init__(self, x, y, x2, y2, penWidth):
        du = Dim.guessDu([x,y,x2,y2],None)
        super(SilkLine, self).__init__(x,y, penWidth)
        self.x2 = Dim.OrZero(x2,du)
        self.y2 = Dim.OrZero(y2,du)

class SilkArc(Silk):
    "Fixed radius arc."
    def __init__(self, x, y, radius, startAngle, arcAngle, penWidth):
        super(SilkArc, self).__init__(x, y, penWidth)
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
    def __init__(self, x1, y1, x2, y2):
        if not isinstance(x1, Dim) \
           and isinstance(y1, Dim) \
           and isinstance(x2, Dim) \
           and isinstance(y2, Dim):
            raise TypeError('Keep-out dimentions must be Dim().')
        self.x1 = min([x1,x2])
        self.y1 = min([y1,y2])
        self.x2 = max([x1,x2])
        self.y2 = max([y1,y2])

#
# Footprint base classes.
#
class KWToken(FPCoreObj):
    keywords = {'mm':'MM','inch':'INCH', 'in':'INCH','mil':'MIL'}
    units = frozenset(['MIL', 'MM', 'INCH'])
    def __init__(self, ttype, value):
        self.type = ttype
        self.value = value
    def reprvals(self):
        return [self.type, self.value]
    @classmethod
    def typeKW(cls, s, lexposIgnored):
        if s in cls.keywords:
            return cls(cls.keywords[s],s)
        return cls('KW',s)
    @classmethod
    def typePunct(cls, s, lexposIgnored):
        return cls(s,s)
    @classmethod
    def typeNum(cls, s, lexposIgnored):
        try:
            v = float(s)
            return cls('NUM',v)
        except ValueError:
            return cls('BAD',s)
    @classmethod
    def typeDrillNum(cls, s, lexposIgnored):
        d = DrillRack.numberToDim(s)
        if d == None:
            return cls('BAD',s)
        return cls('DIM',d)
    @classmethod
    def typeStr(cls, s, lexposIgnored):
        return cls('STR',s[1:-1])

KWSpec = namedtuple('KWSpec','units req vlist')

class KWParamLexer(tt.RegexTokenizer):
    spec = [
        (r'[^.0-9=,"# ][^=," ]*', KWToken.typeKW), # Keyword, identifier, etc.
        (r'[0-9.]+', KWToken.typeNum), # Number. (Expression is over-eager.)
        (r'#([0-9]+|[A-Z])', KWToken.typeDrillNum), # A number/letter drill.
        (r'[=,]', KWToken.typePunct), # Punctuation.
        (r'".*"', KWToken.typeStr), # Quoted matter.
        (r'\s*',None), # Ignore white space.
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
    def __init__(self, description, refdes, pins = [], silk = [], \
                 comments = [], keepOuts = []):
        self.desc = str(description) if description != None else ''
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
    def parse(cls, params, rules, rack, warningCallback):
        raise NotImplementedError('Abstract')
    @classmethod
    def parseKwargs(cls, params, kwspec = {}):
        "Standarized parser for plug-in parameters."
        par = LinesOf(params)
        plist = []
        # FIXME: KWParamLexer should be compiled only once for efficiency.
        tokens = tt.TokenizeAhead(KWParamLexer(par))
        while True:
            # Get keyword token.
            try:
                tkn = next(tokens)
                if tkn.type == 'KW':
                    kw = tkn.value
                else:
                    print 'tkn:',tkn
                    raise ParamSyntax('Expected keyword.')
            except StopIteration:
                break
            # Check for '=' and value list.
            vlist = []
            if tokens[0] != None and tokens[0].type == '=':
                # Pick up value list.
                next(tokens) # Consume the '='.
                while True:
                    vtkn = tokens[0]
                    if vtkn.type == 'STR' or vtkn.type == 'KW':
                        # Treat KW here as an unquoted string.
                        val = vtkn.value
                        next(tokens) # Consume string value.
                    elif vtkn.type == 'NUM':
                        val = vtkn.value
                        next(tokens) # Consume numeric value.
                        vtkn = tokens[0]
                        if vtkn and vtkn.type in KWToken.units:
                            vtkn = next(tokens)
                            units = vtkn.value
                        else:
                            try:
                                units = kwspec[kw].units
                            except KeyError:
                                units = 'mm' # It's an error, but will catch later.
                        if units == 'mil':
                            val = Dim.MIL(val)
                        elif units == 'mm':
                            val = Dim.MM(val)
                        elif units in ['inch','in']:
                            val = Dim.INCH(val)
                        else:
                            raise InternalError('parseKwargs: Can not convert parameter to type: ' + str(units))
                    else:
                        break
                    vlist.append(val)
                    if tokens[0] and tokens[0].type == ',':
                        next(tokens)
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
        # Eliminate redundant value lists.
        for kw in kwdict:
            if not kwspec[kw].vlist:
                v = kwdict[kw]
                kwdict[kw] = v[0] if len(v) > 0 else None
        #print 'Final kwdict:', kwdict
        return kwdict
    @classmethod
    def standardComments(cls, pluginName, kwDict, kwSpecs, rules, ruleList):
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
            units,reqd,isList = kwSpecs[kw]
            vList = kwDict[kw] if isList else [kwDict[kw]]
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
    rd = RulesDictionary()
    rd['foo'] = Dim.MM(7)
    print rd['foo']
##    print rd['bar']
    t = Dim.MIL(30)
    print repr(t)
    print t.gu
    t = Dim.INCH(1)
    print t.mm
    print t.inch
    print repr(t)
    print repr(Dim.MIL('30'))
    print '--drill--'
    dr = DrillRack()
    print dr
    print dr[Dim.INCH(0.044)].mil
    dr.addDrill(Dim.INCH(0.125))
    print dr
    dr.addDrill(Dim.INCH(0.052))
    print dr
    print dr[Dim.INCH(0.044)].mil
    print dr[Dim.INCH(0.25)].mil
    nodr = NoRack()
    print 'nodr:',nodr[Dim.INCH(0.022)],nodr['#76']
    d31 = Dim.DRILL('#31')
    print '#31 drill:',d31
    print '===pads==='
    p1 = RoundPad(Dim.MIL('30'),Dim.MIL('8'),Dim.MIL('4'))
    print p1
    print p1 == p1
    p2 = RoundPad(Dim.MIL('30'),Dim.MIL('8'),Dim.MIL('2'))
    print p2
    print p1 == p2
    p3 = SquarePad(Dim.MIL('30'),Dim.MIL('8'),Dim.MIL('2'))
    print p2 == p3
    print p3.extents()
    
    
    

