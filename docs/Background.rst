=============================
PCB Lands Background Material
=============================

This document captures miscelaneous reference material and
analysis of PCB footprint technology.

Category Matrix
---------------

This is a matrix analysis of various types of PCB lands
versus some key characteristics.

The types are:

- Simple through-hole pin
- Simple SMT pad
- Thermal pad
- Gang mask pad group.

+---------------+------------+-------------+-------------+-----------+
|               | Thru pin   | SMT pad     | Thermal     | Gang      |
+===============+============+=============+=============+===========+
| Pad Instances | - comp     | - comp      | - comp      | - many on |
|               | - inner    |             | - maybe     |   comp    |
|               | - solder   |             |   solder    |           |
+---------------+------------+-------------+-------------+-----------+
| Pad Shape     | simple     | may be      | polygon     | may be    |
|               |            | complex     |             | complex   |
+---------------+------------+-------------+-------------+-----------+
| Clearance     | follows    | follows     | follows     | per pad   |
|               | pad shape  | pad shape   | polygon     | following |
+---------------+------------+-------------+-------------+-----------+
| Mask          | follows    | follows     | 0-many per  | one for   |
|               | pad shape  | pad shape   | polygon     | gang      |
+---------------+------------+-------------+-------------+-----------+
| Paste         | None       | follows     | many per    | one per   |
|               |            | pad shape   | polygon     | pad       |
+---------------+------------+-------------+-------------+-----------+
| Drills        | one        | zero        | many        | zero      |
+---------------+------------+-------------+-------------+-----------+
| Signals       | one        | one         | one         | many      |
+---------------+------------+-------------+-------------+-----------+
| gEDA/PCB      | same pad   | complex pad | lame, awful | no direct |
|               | all layers | via overlay | hacks req'd | support   |
+---------------+------------+-------------+-------------+-----------+
