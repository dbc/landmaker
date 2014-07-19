=======================
landmaker Hacking Guide
=======================

landmaker creates printed circuit board footprints.
Plug-in modules implement footprint creation, typically one family of footprints per plug-in.
Footprints are modelled internally using CAD-system-agnostic modelling primitives.
Rendering methods are factored out so that rendering can be delegated to methods that
are responsible for converting the internal model to the CAD-system-specific file format. 

Modules
-------

- landmaker -- The driver script.
- landmaker/commandcore.py -- Command definition, command interpreter.
- landmaker/plugincore.py -- Base classes for plugins.
- landmaker/fp_<some name>.py -- A footprint generator plugin.
- landmaker/gedarenderer.py -- pcb rendering back-end.
- landmaker/kicadrenderer.py -- KiCAD rendering back-end.
- landmaker/gedascripting.py -- Python scripting interface for gEAD/PCB.
- landmaker/kicadscripting.py -- Python scripting interface for Kicad.

Coding Conventions
------------------

Coding conventions followed in the landmaker source code base.

Naming Conventions
..................

Mostly PEP8, with a few additions as follows:

- aFoo -- lowercase a + Uppercase letter staring a name which is
  ususally a type tame, is often used for formal parameter names in 
  functions and methods.  Example: When a parameter is expected to
  be an instance of Pad, the parameter name my be aPad.
- fooBarBaz -- camel-case name with no underscores, starting with
  a lower case letter and is spelled identically to a class name that
  starts with an upper case letter.  
  This is used for variables that hold a referecne to the class.
- Constructor classmethods of classes that take dimensioned
  arguments have classmethods with the names: MM, MIL, INCH, DRILL,
  VU.  Appoligies that this looks like a constant.  
  The Dim() class has setter/getters of name mm/mil/inch that do
  units conversion.  All-uppercase for the constructor seems like a 
  reasonable name.
- Constructors for KWToken()'s in the keyword parser of Footprint class.
  type_FOO -- being the all-caps constant string that is the type
  created by the constructor.

How To Implement a Plug-in
--------------------------

The plug-in name must not collide with an existing plugin.
The plug-in name is refered to below as <name>.

Plug-ins *must* be a Python module named fp_<name>.py.
The module *must* define a class FP_<name> which is derived 
from the class footprintcore.Footprint.

The FP_<name> class *must* implement these classmethods:

- from_kwargs()
- parse()

and *should* implement:

- helptext()

The method ``from_kwargs`` *must* conform to the prototype: ::

    @classmethod
    def from_kwargs(cls, footprintname, rules, rack, warning_callback, **kw):

The method ``from_kwargs`` *must* return an instance of ``FP_<name>``
that is complete, valid, and ready to be rendered.

The FP_<name> class *must* implement the ``@classmethod`` ``parse()``
which is a constructor for FP_<name> that interprets a single
string and returns a complete, valid, ready to render  instance of FP_<name>.  
The usual approach is to parse the parameter string into keyword
arguments and then simply return the result of ``from_kwargs()``.

The Footprint class defines a generic parameter parsing method as a
convenience function that FP_<name> may use, or it can parse
the string itself however it wants.
If the plugin uses the generic parameter parser, it *should* make
``kwspecs`` a class variable, which allows the readline command
completer to pick up the plug-in's interactive keywords.
Note that there is no requirement that interactive keywords
be the same as the from_kwargs keyword arguments.

The footprint *must* be composed only of primitives defined
in footprintcore.py.
The primitives *must* be instantiated by using reference 
variables inherited from base classes, and not instantiated
directly.  This allows the rendering back-end to sub-class
the primitives.

The class FP_<name> *should* implement ``helptext()`` as
a generator yielding strings to be printed as interactive
help. 

The file landmaker/skeleton_fp.py is an empty footprint
plug in, commented with TODO tasks. 
You may copy this into landmaker/fp_<name>.py and edit it
into a plug in. 

How To Implement a Renderer
---------------------------

A renderer is responsible for interpreting the contents of
an instance of Footprint and yielding the text that defines
the footprint.

Short form how-to:

- Import footprintcore.
- Derive specializations of footprint primitives where convenient.
- Derive a specialization of Footprint that implements the ``rendering()`` 
  method as an interator yielding strings.
  Any specialized primitive classes *must* be referenced by 
  class variables so that plug-ins instantiate the specialized
  primitives.
- Invoke the plug-in loading machinery. 
  The plug-in loader will automatically create classes that
  inherit from both FP_<name> and the specialization of Footprint
  provided here. (If necessary, the rendering-FP_<name> class can
  be created explicitly. Since the plug-in loader only supplies missing
  definitions there will not be conflicts.)

Using the Scripting Interface
-----------------------------

TBW -- probably needs it's own document.


