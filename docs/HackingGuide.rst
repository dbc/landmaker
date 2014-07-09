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
- commands/commandcore.py -- Command definition, command interpreter.
- plugins/plugincore.py -- Base classes for plugins.
- plugins/fp_<some name>.py -- A footprint generator plugin.
- plugins/gedarenderer.py -- pcb rendering back-end.
- plugins/kicadrenderer.py -- KiCAD rendering back-end.

Implementing a Plug-in
----------------------

Plug-ins *must* be a Python module named fp_<name>.py.
The module *must* define a class FP_<name> which is derived 
from the class footprintcore.Footprint.
The FP_<name> class *must* implement the ``@classmethod`` ``parse()``
which is a constructor for FP_<name> that interprets a single
string and returns an instance of FP_<name>.  
The Footprint class defines a generic parameter parsing method as a
convenience function that FP_<name> may use, or it can parse
the string itself however it wants.

The instance of FP_<name> returned by ``parse()`` *must* be
a complete, valid footprint ready to be rendered.
The footprint *must* be composed only of primitives defined
in footprintcore.py.
The primitives *must* be instantiated by using reference 
variables inherited from base classes, and not instantiated
directly.  This allows the rendering back-end to sub-class
the primitives.

A plug-in *should* define the constructor ``@classmethod fromKwargs()``
which is exported via the scripting interface in addition to
``parse()``.
In most cases, this is easily accomplished by letting ``parse()``
return via ``fromKwargs()`` after turning the parameter string
into a validated keyword argument dictionary.


Implementing a Renderer
-----------------------

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
  be created explicitly; the plug-in loader only supplies missing
  definitions.)

Using the Scripting Interface
-----------------------------

TBW -- probably needs it's own document.

