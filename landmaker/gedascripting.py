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

import sys
import landmaker.gedarenderer as r
from landmaker.footprintcore import Dim, DrillRack, RulesDictionary

for name, cls in r.fp_plugins.items():
    setattr(sys.modules[__name__], name, cls)

d = r.fc.Dim

del name
del cls
del r
