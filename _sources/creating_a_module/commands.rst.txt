=================
Defining commands
=================

The final step in being able to actually *use* the data objects we have 
configured is define Zimagi commands to import their data and query them.  By
adding a ``station`` command, we automatically add a collection of subcommands
associated with querying data.  

As elsewhere, we often wish to define a reusable ``command_base`` that might be
utilized by various commands to avoid repetition.  In this module, we define the
following::

  command_base:
    # Define a base command with settings
    # Same name as data model by convention, not requirement
    station_base:
      class: StationCommandBase
      mixins: [station]
      # Accessible via the API
      server_enabled: true
      # Only these groups can use 'station' commands
      groups_allowed: [noaa-admin]
      
The particular name we chose for this command base is anything we might wish, 
but ``station_base`` seems like an obvious choice.  It has an (optional)
internal class name in the generated code, and it uses the mixin we discussed
earlier.  The two elements where we actually make design decisions are in that
we wish to expose commands based on this within the RESTful JSON API (i.e. for
web requrests), and that we want the role ``noaa-admin`` to be able to use it.

We gave the base an (optional) internal class name in the generated code, and
it uses the mixin we discussed earlier. The only elements where we actually
make design decisions are ``server_enabled`` and ``groups_allowed``.

We set ``server_enabled`` to ``true`` to expose commands within the RESTful
JSON API (i.e. for web requests). We also give the ``groups_allowed`` key the
role that we want to be able to use: ``noaa-admin``.

We need an actual command here.  To show that the names of the commands are
chosen by use, rather than constrained by the name of the data object or by
mixins, we defined too almost-synonyms.  Both ``station`` subcommands and 
``bahnhof`` subcommands will do the same thing ("Bahnhof" is simply a German
word for "station")::

  command:
    station:
      # Maps back to data object
      resource: station
      base: station_base
      # Show later than core commands
      priority: 99
      groups_allowed: [noaa-admin, admin]

    # Alternate command (does same thing to demonstrate)
    bahnhof:
      # Maps back to data object
      resource: station
      base: station_base
      # Tie into object type (to match prefix for mixin)
      # I.e. match ref mixin_name
      base_name: station
      # Show later than core commands
      priority: 98

The only differences here, other than the obvious spelling, is that we 
demonstrate that a command may override its base; in this case we redefine
``groups_allowed`` for the ``station`` command.  This is not a real change in
behavior since *admin* is always allowed to do everything anyway.  We also 
choose slightly different ``priority`` values for the two spellings, which will
cause ``bahnhof`` to appear earlier than ``station`` when you run::

  vagrant@zimagi-noaa:~$ zimagi help

Inside the Vagrant shell.  As the module is configured now, the ``observation``
priority is even higher (105), so appears after both.

Import commands
---------------

We have provided a ``station`` (or ``bahnhof``) command as a place to put 
subcommands we use in querying data.  But we need to define an ``import`` 
subcommand to load the data from our remote source(s) into the local RDBMS.

For this module, we define that inside 
``$ZDIR/lib/modules/default/noaa-stations/spec/import/station_observations.yml``.

This YAML file includes a new YAML feature we have not seen before.  Using 
mixins and bases for commands and data models is a way of providing templates
for reuse.  

As well, YAML itself has a feature for literal transclusion of boilerplate.
This distinction is very similar to the difference between an ``#include``
directive in languages like C/C++ and *inheritance* of classes in languages
like Python (or C++, or Java, etc).  For better or worse, because ``import`` is
a built-in Zimagi command, we can define subcommands but not new bases or
mixins for it.

The YAML feature we see is called *anchors* and *aliases*.  They always occur
in the same physical file, so are somewhat different from C-style ``#include`` 
directives in that respect.  Let us look first at the anchor we use::

  _observation: &observation
    source: noaa_stations
    data:
      station: 
        map:
          # "number" as defined in spec/data/station.yml
          number: 
            # "station_id" as defined in plugins/source/noaa_stations.py
            column: station_id
          name:
            column: station_name
          lat:
            column: latitude
          lon:
            column: longitude
          elevation:
            column: elevation

      observation:
        relations: 
          station_id: 
            # Mapping back to "station" as defined in spec/data/station.yml
            data: station
            # Mapping back to plugins/source/noaa_stations.py
            column: station_id
            required: true
        map:
          date: 
            column: date
          temp:
            column: temperature
          temp_attrs: 
            column: temperature_attrs
            
This anchor is something we are likely to use as we develop more commands.  It
has an anchor name ``&observation``, but as we will see, when we *alias* it
we will spell that as ``*observation`` (these spelling are loosely inspired by
references and pointers in C/C++ family languages).  The name of the key with 
a leading underscore, ``_observation`` is irrelevant—you can use any identifier
name you like, and it is not used again elsewhere; something merely needs to 
occur there syntactically.

We indicate the source in terms of a *provider*. Recall the definition in 
``spec/plugins/source.yml`` that was discussed above; this is where the spelling
``noaa_stations`` comes from.  Given that source, we define ``data`` import 
elements ``station`` and ``observation``.  These each have a ``map`` key that 
maps database table column names to names used within the Zimagi shell and 
API.  They might also have a ``relations`` key that defines a foreign-key
relationship.

The final component of our (simple) module is define an actual ``import`` 
subcommand.  We can do that as follows::

  import:
    test:
      # Identical to including the body of _observation here
      <<: *observation
      # In concept we could override definition from reference, e.g.
      # source: something_else
      tags: [observations]
      min_year: 1929
      max_year: 1931
      station_ids: ["03005099999", "99006199999"]

The special key ``<<`` is the one that indicates an alias back to the anchor
defined above.  It is exactly as if we had typed the entire body of 
``_observation`` at that same point in the file

The key ``tags`` indicates **[TODO]**.

For this simple subcommand ``test`` we give a fixed value for a ``min_year`` and
``max_year``, and also a specific list of ``station_ids`` that we will import
from the NOAA website.  In a more flexible command, you would indicate these
elements using switches to a command, but this demonstrates the general pattern.

At this point—perhaps after running ``zimagi module save noaa-stations`` again, 
if needed, we can run::

  vagrant@zimagi-noaa:~$  zimagi import test

Data is available locally to be queried from the Vagrant shell or the API now.

