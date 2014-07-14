#   Copyright 2014 David B. Curtis

# TODO: Add year and your name to copyright.
#   Copyright <year> <your name>

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


import footprintcore as fc
# TODO: Add your other imports here, if any.

# TODO: replace 'foo' with <yourplugin> name.
class FP_foo(fc.Footprint):
    @classmethod
    def helptext(cls):
        # TODO: Write help.
        yield "Yield lines of help text here."
        yield "  They will be displayed by: 'help fp foo'." 
    @classmethod
    def parse(cls, footprintname, params, rules, rack, warningCallback):
        # TODO: Parse the params. parse() must return an instance of
        # FP_foo, usually, by returning via fromKwargs().
        # Consider using the standard parameter parser built into
        # fc.Footprint.
        # TODO: To use the standard parameter parser, set up KWSpec dict.
        # A KWSpec is a three-tuple:
        #   default units, a string
        #   required parameter, boolean
        #   value list, boolean True for list, False for singleton.
        # Example:
        # kwspecs = {
        #   'pad':      fc.KWSpec('mm', True, False),
        #   'drill':    fc.KWSpec(None, False, False),
        #   'screw':    fc.KWSpec(None, False, False),
        #   'fit':      fc.KWSpec(None, False, False),
        #}
        # TODO: Call the parameter parser, if you choose to use it.
        # Otherwise, parse the params string any way you like.
        # kw = cls.parseKwargs(params, kwspecs)
        # Exit via fromKwargs() constructor.
        return cls.fromKwargs(footprintname, rules, rack, warningCallback, **kw)
    @classmethod
    def fromKwargs(cls, footprintname, rules, rack, warningCallback, **kw):
        # TODO: Construct the footprint model entirely from primitives.
        # The footprint primitives must be instantiated by calling
        # the inherited class vectors provided via the plugin manager.
        # All of the actual footprint construction work should be done
        # through fromKwargs() to enable the scripting interface.

        # TODO: Construct description (a string) from parameters.
        # TODO: Construct refdes (primitive instance) from parameters.
        # TODO: Construct pin_specs (list of primitives) from parameters.
        # TODO: Construct silk art (list of primitives) from parameters.
        # TODO: Construct any desired comments (list of primitives).
        #       Consider using the standard_comments() method.
        # TODO: Construct any keep_outs (list of primitives).
        # TODO: Exit via the __init__() method inherited via plugin manager.
        return cls(footprintname, description, refdes, pin_specs, silk,
                   comments, keep_outs)
    # TODO: name your file fp_<yourplugin>.py and leave it
    # laying about in the plugins/ directory where it will be found
    # and loaded by the plug-in manager.

    # Checklist:
    # ____ parse() takes paramater string, returns instance of footprint.
    # ____ from_kwargs() takes keyword dictionary, returns instance of fp.
    # ____ helptext() implemented, matches parse() behavior.
    # ____ All drills passed through drill rack whenever possible.
    # ____ Mask relief and clearance taken from rules whenever possible.
    # ____ Check minimum mask feature rule.
    # ____ Check minimum annulus rule.
    # ____ Check minimum clearance rule.
    # ____ Include standard comments.
    # ____ No silk off mask.
    
