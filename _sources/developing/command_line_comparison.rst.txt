Comparison of ``noaa-stations`` with ``module-noaa-stations``
=============================================================

This document describes differences between an implementation of similar
functionality within a stand-alone command line tool written in Python
and a Zimagi module.

Code required
-------------

This snapshot is NOAA-stations commits `b910e2e
<https://github.com/DavidMertz/NOAA-Stations/tree/b910e2e1a16ac6d66e89c0ba594b65749b06842e>`_
and `76a0dae
<https://github.com/DavidMertz/NOAA-Stations/tree/76a0daee88d10d80c3066dc3ba2bf0eb325d813d>`_
with commit `58d87e6
<https://github.com/zimagi/module-noaa-stations/tree/58d87e6289f227fee35993e98fe4117caab21939>`_
of module-noaa-stations. Lines of code used and features supported may change
in future revisions.

Zimagi module [b]_ [c]_:

::

   module-noaa-stations % cloc .  # 58d87e6
         17 text files.
         17 unique files.
          9 files ignored.

   github.com/AlDanial/cloc v 1.86  T=0.02 s (760.2 files/s, 36315.6 lines/s)
   -------------------------------------------------------------------------------
   Language                     files          blank        comment           code
   -------------------------------------------------------------------------------
   YAML                             8             69             66            272
   Python                           4             26             11            110 (33) 
   Markdown                         1             23              0             44
   -------------------------------------------------------------------------------
   SUM:                            13            118             77            426
   -------------------------------------------------------------------------------

Command-line tool [a]_ [b]_:

::

   NOAA-Stations % cloc .  # b910e2e1
          7 text files.
          7 unique files.
          3 files ignored.

   github.com/AlDanial/cloc v 1.86  T=0.01 s (789.9 files/s, 30489.7 lines/s)
   -------------------------------------------------------------------------------
   Language                     files          blank        comment           code
   -------------------------------------------------------------------------------
   Python                           2             12             34             85
   Markdown                         2             21              0             31
   YAML                             1              0              0             10 
   -------------------------------------------------------------------------------
   SUM:                             5             33             34            126
   -------------------------------------------------------------------------------

Command-line tool (normalized tables) [a]_ [b]_:

::

   NOAA-Stations % cloc .  # 76a0daee 
          7 text files.
          7 unique files.
          3 files ignored.

   github.com/AlDanial/cloc v 1.86  T=0.01 s (680.8 files/s, 43300.6 lines/s)
   -------------------------------------------------------------------------------
   Language                     files          blank        comment           code
   -------------------------------------------------------------------------------
   Markdown                         2             46              0            107
   Python                           2             16             44             95
   YAML                             1              0              0             10 
   -------------------------------------------------------------------------------
   SUM:                             5             62             44            212
   -------------------------------------------------------------------------------

.. [a] The small YAML file in NOAA-Stations is a conda environment
   configuration file. It is only indirectly related to the tool itself,
   but providing the necessary dependencies is reasonable to consider part
   of tool requirements. A pip ``requirements.txt`` would be similar
   length.

.. [b] The Markdown files in both repositories are entirely
   documentation and are not directly related to the functionality of
   either. In the main, the documentation is this file itself.

.. [c] Three of the four Python files in module-noaa-stations are
   auto-generated. The only file written by hand contains **33** code lines
   (and some comments).

Feature comparisons
-------------------

=============================== ============= ============ =============
Feature description             Zimagi module Command-line CL Normalized
=============================== ============= ============ =============
Exposes all source data columns No [f]_       Yes          Yes
Download by year range          Partial [d]_  Yes          Yes
Download by station list        Partial [d]_  Yes          Yes
Download of all stations        No [e]_       Yes          Yes
Flexible querying of local DB   Yes           Yes          Yes
RESTful API to access local DB  Yes           No           Yes
Missing data cleaned            Partial       Yes          Yes
Performs good normalization     Yes           No [g]_      Yes
Provisions for cloud deployment Yes           No [h]_      No [h]_
Supports “pretty” output        Yes           Yes          Yes
Supports CSV export             Yes           Yes          Yes
Supports TSV export             No            Yes          Yes
Supports JSON export            Yes           Yes          Yes
“Code” lines [i]_               305           95           105
=============================== ============= ============ =============

.. [d] Only a ``test`` import subcommand defined currently, but data model
   supports parameters for min year, max year, and station list.

.. [e] Logic for obtaining station list within year currently stubbed out
   but should follow identical logic to that used in command-line tool.

.. [f] Data definitions could be created for columns not currently
   utilized. My estimate is that it would require about 150 additional
   lines of YAML and maybe 20 lines of Python.

.. [g] The initial command-line tool simply used the same table structure
   as the source CSV files. Adding a child table with foreign key would
   require about 6 extra lines of Python, and 8 extra lines of SQL (which
   is currently defined as a Python string rather than separate file).

.. [h] No current code knows about any clouds, but the code that would need
   to be distributed to one is very minimal.

.. [i] YAML or Python code that is functionally required for the system to
   operate. Documentation in Markdown or other formats is very desirable to
   have, but does not change functionality. Auto-generated Python code is
   excluded.


* :ref:`genindex`
* :ref:`search`
