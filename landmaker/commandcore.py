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
import re

debug = ''

class CommandSyntaxError(Exception):
    # Error messgage will be in args[0].
    pass

class Command(object):
    "Base class for all command verbs."
    def execute(self, s, warning_callback):
        raise NotImplementedError('Abstract')
    def helptext(self, longhelp = ''):
        c,v = self.__class__.__name__.split('_')
        yield 'No help for ' + v

class Cmd_quit(Command):
    def execute(self, s, warning_callback):
        raise StopIteration
    def helptext(self, longhelp=''):
        yield 'quit'
        if longhelp:
            yield '  exits landmaker'
    
class Cmd_help(Command):
    def execute(self, s, warning_callback):
        if s == '':
            v = verbs.keys()
            v.sort()
            for verb in v:
                for ln in verbs[verb].helptext():
                    print ln
        else:
            t = s.strip().split(' ',1)
            try:
                verb = verbs[t[0]]
                #subverb = t[1:] if len(t) > 1 else True
                subverb = t[1] if len(t) > 1 else True
                for ln in verb.helptext(subverb):
                    print ln         
            except KeyError:
                print 'Unknown command:',s
    def helptext(self, longhelp = ''):
        yield "help [<command>]"
        if longhelp:
            yield "  help ; Print help summary for each command."
            yield "  help <command> ; Print long help for <command>."
            yield "  help fp <plug-in> ; Print help for footprint <plug-in>."
            yield "  help fp ? ; Print list of available footprint plug-ins."
            
class Cmd_include(Command):
    breadcrumbs = set()
    def execute(self, s, warning_callback):
        "s : <filename>"
        s = s.strip()
        if s == '':
            raise CommandSyntaxError('No include file specified.')
        filename = s.split(' ')[0]
        if not os.path.isfile(filename):
            raise CommandSyntaxError(filename + ' is not a file.')
        if filename in self.breadcrumbs:
            raise CommandSyntaxError('Recursive include encountered.')
        self.breadcrumbs.add(filename)
        if 'i' in debug:
            print 'from:',filename
        with open(filename) as f:
            for ln in f:
                if 'i' in debug:
                    print 'including:',ln
                try:
                    dispatchCommand(ln, warning_callback)
                except CommandSyntaxError as e:
                    print 'Error in batch file {0:s}:'.format(filename)
                    print e.args[0]
                    break
        self.breadcrumbs.remove(filename)  
    def helptext(self, longhelp = ''):
        yield "include <filename>"
        if longhelp:
            yield "  Execute commands from <filename>."
    
class Cmd_drillrack(Command):
    "Set/inspect drill rack."
    def execute(self, s, warning_callback):
        "s : [ <rack name> ]"
        if s == '':
            print 'Available drill racks:'
            for name in self.drillRacks:
                print '*' if name == self.currentRack else ' ',name
        elif s == '?':
            print 'Drills in {0:s}:'.format(self.currentRack)
            rk = self.drillRacks[self.currentRack]
            for drl in rk.drills():
                print str(drl)
            sym = rk.symbolics()
            if len(sym) > 0:
                print 'Symbolic drills:'
            for drl,sz in sym.items():
                print drl,'=',str(sz)
        else:
            spl = s.split(' ')
            newRack, oldRack = spl[0],spl[1] if len(spl) > 1 else None
            if newRack in self.drillRacks:
                self.currentRack = newRack
            else:
                print 'Creating drill rack:',newRack
                if oldRack != None:
                    try:
                        ork = self.drillRacks[oldRack]
                    except KeyError:
                        raise CommandSyntaxError (oldRack + " doesn't exist.")
                    rk = self.rackClass(ork.drills(), ork.symbolics())
                else:
                    rk = self.rackClass()
                self.currentRack = newRack
                self.drillRacks[self.currentRack] = rk
            global rack
            rack = self.drillRacks[self.currentRack]
    def helptext(self, longhelp = ''):
        yield "drillrack [<name>]"
        if longhelp:
            yield "  drillrack ; show current drill rack and available racks."
            yield "  drillrack <name> ; set current drill rack to <name>."
            yield "  drillrack ? ; show drills in current rack."
            yield "  drillrack <newname> <oldname> ; create new rack from old."

class Cmd_drill(Command):
    "Add drills to drill rack."
    def execute(self, s, warning_callback):
        "s : <size>"
        t = s.split(' ')
        if t[0] == '':
            raise CommandSyntaxError('Must specify drill size.')
        while len(t) < 3:
            t.append('')
        if t[0][0] in '0123456789#.':
            size = self._size(t[0], t[1])
            rack.add_drill(size)
        else:
            name = t[0]
            if t[1] == '':
                raise CommandSyntaxError('Must specify drill size.')
            size = self._size(t[1], t[2])
            rack.add_symbolic(name, size)
    def _size(self, val, units):
        if val[0] == '#':
            try:
                #size = Cmd_drillrack.rackClass.number[val]
                size = verbs['drillrack'].rackClass.number[val]
            except KeyError:
                raise CommandSyntaxError(val.join(['Number drill: ',' not known.']))
        else:
            try:
                v = float(val)
            except ValueError:
                raise CommandSyntaxError('Expected a drill size.')
            units = units if units != '' else 'inch'
            try:
                size = dimClass.VU(v, units)
            except ValueError as e:
                raise CommandSyntaxError(e.args[0])
        return size
    def helptext(self, longhelp = ''):
        yield "drill <size>"
        if longhelp:
            yield "  drill <size> <units> ; add drill to current drill rack."
            yield "  drill <size> ; add <size> inch drill to current drill rack."
            yield "  drill #<drl> ; add number or letter drill."
            yield "  drill <name> <size> <units> ; add symbolic drill."
            yield "  drill <name> <size> ; add symbolic inch drill."
            yield "  drill <name> #<drl> ; add symbolic number or letter drill."

class Cmd_ruleset(Command):
    "Set/view design rule set."
    def execute(self, s, warning_callback):
        if s == '':
            print 'Available rulesets:'
            for name in self.ruleSets:
                print '*' if name == self.currentSetName else ' ',name
        elif s == '?':
            print 'Rules in {0:s}:'.format(self.currentSetName)
            rs = self.ruleSets[self.currentSetName]
            for name in rs:
                print '{0:s} = {1:s}'.format(name, str(rs[name]))
        else:
            s = s.split(' ')[0] # Don't allow spaces in name.
            if s in self.ruleSets:
                self.currentSetName = s
            else:
                print 'Creating new ruleset:',s
                rd = self.rulesDictClass()
                self.currentSetName = s
                self.ruleSets[s] = rd
            global rules
            rules = self.ruleSets[self.currentSetName]
    def helptext(self, longhelp = ''):
        yield "ruleset [ <name> ]"
        if longhelp:
            yield "  ruleset ; show current rule set and available sets."
            yield "  ruleset <name> ; set design rules to <name>."
            yield "  ruleset ? ; show current rules and values."
    
class Cmd_rule(Command):
    "Add design rule."
    def execute(self, s, warning_callback):
        "s : <rulename> = <value> <units>"
        try:
            ruleName, setting = [x.strip() for x in s.split('=')]
            m = re.match(r'([0-9.]+)(\s+)?([a-z]+)?',setting)
            if m:
                value, units = m.group(1),m.group(3)
                rules[ruleName] = dimClass.VU(value, units)
            else:
                rules[ruleName] = setting
        except ValueError:
            raise CommandSyntaxError('Rule syntax error.')        
    def helptext(self, longhelp = ''):
        yield "rule <rule name>  = <value>"
        if longhelp:
            yield "  Set <rule name> to <value> in current rule set."

class Cmd_fp(Command):
    "Dipatch to footprint plug-in."
    def execute(self, s, warning_callback):
        "s : <footprintname> <fp-plug-in> <parameters>"
        t = s.strip().split(' ',1)
        footprintname = t[0]
        # Error check
        if footprintname == '':
            raise CommandSyntaxError('No footprint name specified.')
        if len(t) < 2:
            raise CommandSyntaxError('No plugin name specified.')
        # Extract filename, if any.
        t = t[1].split('>')
        params, filename = t[0].strip(),t[1].strip() if t[1:] else ''
        footprint = self.dispatchPlugin(footprintname, params, warning_callback)
        if not footprint:
            return # Error messages generated elsewhere -- return silently.
        if filename == '':
            # Render to screen instead for a quick view.
            for ln in footprint.rendering(warning_callback):
                print ln
        else:
            with open(filename,'w') as f:
                for ln in footprint.rendering(warning_callback):
                    f.write(ln)
                    f.write('\n')
    def dispatchPlugin(self, footprintname, params, warning_callback):
        t = params.split(' ',1)
        if len(t) < 2:
            t.append('')
        plugin, puParams = t
        try:
            pu = self.plugins[plugin]
        except KeyError:
            raise CommandSyntaxError(plugin.join(['Plugin ',' not found.']))
        try:
            footprint = pu.parse(footprintname, puParams, rules, rack, warning_callback)
        except FootprintException as e:
            print e.msg
            return None
        return footprint
    def helptext(self, longhelp = ''):
        if longhelp == True:
            yield "fp <footprintname> <plug-in> <parameters> > <filename>"
            yield "  Make footprint using <plug-in> <parameters>, and write to <filename>."
            yield "  To list available plugins: help fp ?"
            yield "  For help on a plug-in: help fp <plug-in name>"
            yield "  fp <footprintname> <plug-in> <parameter> ; renders to screen for quick view."
        elif len(longhelp) > 0:
            pu = longhelp.strip()
            if pu == '?':
                yield "  Available plugins:"
                for pu in sorted(self.plugins.keys()):
                    yield "    " + pu
            else:
                try:
                    self.plugins[pu]
                    for ln in self.plugins[pu].helptext():
                        yield ln
                except KeyError:
                    print 'No plug-in: ',pu
        else:
            yield "fp <footprintname> <plug-in> <parameters> [ > <filename> ]"

def collectVerbs(moduleDict):
    verbs = {}
    for key in moduleDict.keys():
        try:
            pre,verb = key.split('_')
            if pre == 'Cmd':
                verbs[verb] = moduleDict[key]() 
        except ValueError:
            pass
    return verbs

def nullWarningSink(msg):
    pass

def dispatchCommand(s, warningSink=nullWarningSink):
    "Parse and dispatch a command to a verb engine."
    t = s.strip().split(';')[0] # Strip off comments and leading white space.
    t = t.split(' ',1)
    params = t[1] if len(t) > 1 else ''
    if t[0] == '': return
    try:
        verb = verbs[t[0]]
    except KeyError:
        raise CommandSyntaxError(t[0].join(["'","' not a command."]))
    verb.execute(params, warningSink)
    

# Use introspection to load the command dictionary.
verbs = collectVerbs(globals())


#####################
##def init(plugins):
##    global fp_plugins
##    fp_plugins = plugins


#################33
# Command core interp should also understand "here documents" for fp
# commands, or have a form of fp that passes multiple lines to parse.
# fpx <sentinel>
# ...stuff
# <sentinel>

if __name__ == '__main__':
    #print verbs
    for v in verbs:
        print verbs[v].helptext()

    print parseCommand('')
    print parseCommand('abc')
    print parseCommand('abc def ghi; comment')
    print parseCommand('fp so20.fp so 20 300 ; generic so20')

    fpcmd = Cmd_fp()
    print fpcmd.execute('abc def ghi jkl')
    print fpcmd.execute('abc')
    print verbs['fp'].execute('abc def')
    print verbs['fp'].execute('')
