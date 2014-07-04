======================
landmaker User's Guide
======================

Invocation
----------

landmaker is invoked from the command line and has three basic modes of operation:

- The --fp option dispatches a single ``fp`` command to a footprint plugin.
  Example: ::

    landmaker --fp 'th2pad spacing = 300 desc="through-hole, 2 pad" drill=.02 dia=35 artwidth=200'

- If a file is specfied, it is interepreted as a script full of landmaker commands.
- If no file is specified, landmaker drops into interactive mode.

landmaker.rc
------------

The optional rc file is named ``landmaker.rc``.  
If an rc file is present in the current working directory, it is executed before
any other scripts or commands.
If there is no rc file file in the current working directory, landmaker looks
in $HOME/.landmaker/landmaker.rc for an rc file.

The rc file can be used to set up your favorite defaults and rule sets.

Commands
--------

- drill <size> - add a drill to the current rack
- drillrack [<name>] - select/show current rack, create new
- fp <filename> <plug-in> <parameters> - create a footprint
- help [<command>] - more help
- include <filename> - include a landmaker script
- quit
- rule <rule name>  = <value> - define a rule in the current set
- ruleset [ <name> ] - select/show current rule set



