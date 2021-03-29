=================
Creating a module
=================

This tutorial will demonstrate to developers how to create a Zimagi module.
As an example, we will create a module that obtains data from a public data
source provided by the United States National Oceanic and Atmospheric 
Administration (NOAA).

This module is available in a public GitHub repository at:

  https://github.com/zimagi/module-noaa-stations

Our module development will be performed locally, which provides an interactive
environment for enhancing and testing feature as they are added.

The example we will work through utilizes a large collection of CSV files, each
of which is regular in form.  At a particular URL, there are subdirectories
named as years, and within each of those directories are many individual CSV 
files, each containing information about data from one weather station during 
that year.

Inside each of these CSV files, rows contain a mixture of information about the
station itself, such as its name, altitude and latitude, and information about 
the observation, such as temperature, humidity, visibility, precipitation, and 
so on.

For comparison, you may want to look at comparisons with a standalone script
written for a similar purpose.


Initializing Zimagi
===================

The very first step you should perform is to clone the Zimagi repository
itself onto your local system.  That repository is available at:

  https://github.com/zimagi/zimagi

Suppose that you have cloned Zimagi itself into ``$HOME/git/zimagi`` on your local 
system.  Let us name this as ``$ZDIR`` for purposes of this tutorial.  You may 
wish to copy ``$ZDIR/vagrant/config.default.yml`` to ``$ZDIR/vagrant/config.yml``
and modify the settings within the new ``config.yml`` file.  In most cases, the
default settings will be fine, and this is not necessary.

In this tutorial, a shell prompt showing the leaf of the working directory is used
to help you orient the path you might be working within.  Within `$ZDIR` you simply 
need to launch the Vagrant configuration, i.e.::

  (zimagi)$ vagrant up  # Will take a few minutes to setup
  (zimagi)$ vagrant ssh

This will put you inside a Vagrant hosted Zimagi console where you may run 
commands.

Creating a module skeleton
--------------------------

Before making a module available within Zimagi, you need to create a GitHub
repository that contains a skeleton for a module.  The goal here will be to
create a local clone of the module you are developing underneath the ``$ZDIR``
directory, but it needs to exist in a basic form first.

All that your module strictly needs is a file called ``zimagi.yml`` at its root.
This file, in its minimal version, only has to define a name for the module.
For example, within our demonstration module::

  (module-noaa-stations)$ cat zimagi.yml
  name: "noaa-stations"

Now we are ready to load the module into Zimagi and enhance it.

Adding a module to Zimagi
-------------------------

Within the Vagrant shell, it is commonly useful to check the environment to
verify that changes and configurations you intend to make have been peformed.::

  (vagrant) zimagi env get

Initially, this will contain only the default environment, but we can now add
the module skeleton we created.  For the example, we can run the following::

  (vagrant) zimagi module add https://github.com/zimagi/module-noaa-stations.git
  (vagrant) zimagi env get

Adjust the GitHub URL as needed to point to your repository.  Notice that at
this point we are only using the ``https://`` URL rather than the ``git@`` URL 
since the Vagrant shell does not have SSH credentials configured.  This is not
a problem, and we will enhance the connection just below.

Within your local terminal, you can now see where the module has been cloned::

  (zimagi)$ cd lib/modules/default/
  (default)$ ls noaa-stations

In the minimal version, this will contain only the ``zimagi.yml``, shown above,
but you may have created a ``LICENSE`` or a ``README`` or other repository 
contents.

Creating a local remote
-----------------------

Add a remote to the working Zimagi repo for the module by running the following.
We assume that the system you are working on has established SSH credentials
with GitHub, and you are able to run authenticated commands.  Within your 
local terminal shell::

  (zimagi) git remote add noaa git@github.com:zimagi/module-noaa-stations.git
  (zimagi) git push noaa  # Nothing has changed yet, but this will now work

Periodically, within the Zimagi Vagrant shell, you will integrate new 
functionality by running::

  (vagrant) # Pull changes from GitHub:
  (vagrant) zimagi module save noaa-stations
  (vagrant) zimagi makemigrations

From this point forward, you can (and probably should) work within the module 
clone that is located at ``$ZDIR/lib/modules/default/noaa-stations`` (or whatever
leaf path corresponds to the name you gave to your module.  Notice that this
directory matches the ``name`` key defined inside the module's ``zimagi.yml`` 
file rather than the repository name itself.  In this example, the repository is 
named ``module-noaa-stations`` while the module name is ``noaa-stations``; but
either name can be whatever you like.


Developing module functionality
===============================

The Zimagi system will scan a number of YAML configuration files to provide 
capabilities within a module.  Most of the requirements are driven by the various
keys inside these YAML files, but an organization into directories and filenames
is helpful for identifying the location of various definitions.

Configurations will live inside the ``spec/`` directory of the module repository.

Defining roles
--------------

We would like to define roles for differing kinds of users who have different
capabilities within the system.  Those are ideally placed in ``spec/roles.yml``,
for example::

  (noaa-stations) cat spec/roles/yml
  roles: 
    noaa-admin: Administer NOAA weather data
    viewer: User who can view weather data

We will use these roles later on to control what actions given named roles may
perform.  As many roles as we like may be defined, and they may be named however
we like.  However, using names with dashes or underscores are generally easier
to enter into other configuration files since quoting is not needed when spaces
are not used.

Data mixins
-----------

Zimagi allows you to configure "mixins" which are a kind of boilerplate that 
avoids repeating the same definitions that are used in multiple places.  Mixins 
might either be ``data_mixins`` or ``command_mixins``.  We can define a 
``data_mixin`` in a fashion similar to this.  The same name (in this case 
"station") is used at several levels, but with somewhat different meanings in 
the different positions.  Let us look at an example defined within 
``spec/data/station.yml``::

  data_mixins:
    station:
      class: StationMixin
      fields:
        station:
          type: "@django.ForeignKey"
          relation: station
          options:
            "null": true
            on_delete: "@django.PROTECT"
            editable: false
  
In essence, what we define in the mixin is a database column that has attributes,
but is used in multiple places to define a foreign key relation.  The Django data
type identifies the relationship, with YAML keys ``type`` and ``relation`` 
indicating the primary table.  The ``options`` values correspond to database
table properties in a straightforward way.

Explicitly specifying a ``class`` name, as is done above, is optional (and is
not used for any real externally-facing purposes, only in code generation).  
Mixins may also have inheritance relationships by specifying a ``base``, but that 
is not used in this example.


Command mixins
--------------

Commands, which we look at below, may also utilize mixins to save repeated 
boilerplate.  For example::

  command_mixins:
    # Generate methods on other classes
    station:
      class: StationCommandMixin
      meta:
        # Name used in commands (not required to be same as table)
        # Ref: mixin_name
        station:
          # Link back to dynamic class station
          data: station
          # Positive integer (lowest is highest priority)
          priority: 1

Again we define a name ``station`` that might be mixed into. ``class`` remains
optional and generally internal.  The key elements is the a data source.  The 
``priority`` given simply expresses the order in which help on commands is shown.


Defining a data model
=====================

For a module to do something useful, we need to configure its *data model*.  
This expresses, in a somewhat Django-centric way, a mapping onto relational 
database tables where the data is actually stored.

For this example project, there are two data types used; this is very similar
to the way you might define multiple tables in an RDBMS (and in fact maps to 
exactly that "under the hood").  We have ``stations`` and ``observations``.
The definitions of these kinds of data are contained in the files:

 * ``$ZDIR/lib/modules/default/noaa-stations/station.yml``
 * ``$ZDIR/lib/modules/default/noaa-stations/observations.yml``
 
This choice follows a natural pattern, but is not required.  We could put the 
definitions in any files we wanted, as long as they live in the module 
directory hierarchy and have the extension ``.yml``.  The structure of these
two files is very similar, although somewhat more is defined within 
``station.yml`` since some mixins and **bases** (more on that soon) are defined
in ``station.yml`` and hence do not need to be duplicated in 
``observations.yml``.
 
Within a data model, we typically define a top-level key ``data_base`` and 
another under the key ``data``.  While as this module is organized, each of 
``station.yml`` and ``observations.yml`` have their own top level keys, we could
perfectly well put all of this in the same file if we preferred.  For example, 
as actually organized, we have::

  # in station.yml
  data:
    station:
      # ... more info ...
      
  # in observations.yml
  data:
    observation:
      # ... more info ...
      
This is a decision of the module developer; a different module might choose
instead, for example, to have::

  # in data-model.yml (not a file in this module)
  data:
    station:
      # ... more info ...
    observation:
      # ... more info ...
    
Defining data_base objects
--------------------------

In this module, the "abstract" base object ``station`` is used by concrete data
objects (including one called ``station``).  Let us look at that definition,
here contained in ``station.yml`` (but again, it could live elsewhere if you
prefer)::

  data_base:
    station:
      # Every model (usually) based on resource
      class: StationBase
      base: resource
      mixins: [station]
      id_fields: [number]
      meta:
        # Number alone is probably unique, demonstrate compound key
        unique_together: [number, name]
        # Updates must define station
        scope: station
  
This has several notable elements.  The field named ``number`` is specific to
the data we are working with.  The NOAA data defines a CSV column called 
``STATION`` which is a special number weather services use for identification,
and also a column called ``NAME`` that is a verbose description of the weather 
station.  We have used names that are more mnemonic for us in calling them 
``number`` and ``name`` in the module, but we are free to use any names
whatsoever.
 

We are declaring in the ``data_base`` that the combination of ``number``and 
``name`` will define a unique identifier, but only ``number`` is used as the ID 
for queries.  In this particular dataset, probably ``number`` alone will be 
unique, and the more verbose description ``name`` might actually change over
multiple years.  However, the ``unique_together`` key is given a list containing
both mostly for illustration of the possibility.

Defining data objects
---------------------

With the scaffolding in place, we can define an actual data object.  Let us 
quickly notice something about the ``observation`` object before presenting the 
full ``station`` object::

  # Inside observation.yml
  data:
    observation:
      class: Observation
      # Observation extends Station base data model
      base: station

Because an observation represents a "child table", it is based on the parent
``data_base`` object ``station``.  Let us look at (almost) the entire definition 
for the ``station`` object::

  data:
    # Actual data models turned into tables
    # Fields 'name', 'id', 'updated', 'created' implicitly
    # created by base resource (id/updated/created internal)
    station:
      class: Station
      # Environment extends resource in Zimagi core
      base: environment
      # Primary key (not necessarily externally facing)
      id_fields: [number, name]
      # Unique identifier within the scope
      key: number
      roles:
        # Redundant to specify 'admin'
        edit: [noaa-admin, admin]
        # Editors are automatically viewers
        # Public does not require authentication
        # (viewer will authenticate if public were not listed)
        view: [viewer, public]
      fields:
        number:
          type: "@django.CharField"
          options:
            "null": false
            max_length: 255
            # editable is default (not specified)
        lat:
          # In degrees
          type: "@django.FloatField"
          options:
            "null": true
        # 'lon' and 'elevation' defined in same manner as 'lat'
        meta:
          unique_together: [number, name]
          # Display ordered by elevation and number
          ordering: [elevation, number]
          # Fuzzy string search
          search_fields: [number, name]

A number of things are happening in this definition.  We create an actual 
``station`` object, with a corresponding RDBMS table.  The table will not yet
have a way to be populated with this definition, but this determines its schema
and Zimagi will create the empty table based on this.

We can define a primary key as ``id_fields`` and an access identifier as 
``key``. These may often be the same, but need not be, as the example 
illustrates.  

A crucial element is that this is where we can define access permissions to this 
data object.  These ``roles`` correspond to those we created earlier.  The 
special roles *admin* and *public* are always available, but any other strings
may be used to define various permissions (assuming they are defined as roles).  
The role *admin* will always have all permissions, but we list it here to 
illustrate its existence.

The crucial element in defining a data element is the fields it will contain.  
The key ``fields`` lets us list these,  along with data types and properties.
Fields can have whatever names are convenient for us; we will see later how they
are translated from whatever names are used in the underlying data sources 
(quite likely, those underlying data sources use a variety of different names, 
and Zimagi will present a more unified interface to the data).

Data types are provided using Django data definition types, quoted.  For example, 
latitude (named ``lat`` by us) is a ``@django.FloatField`` type.  Within each
field, we may define a few constrains, such as its NULL-ability and, for a 
string, its maximum length.

We may define a few special attributes of the data object.  For example, by 
default, queries of this data will be sorted by elevation then by (station)
number.  This is again chosen for illustration, not any specific business need
within this particular module; in other cases, an order may be relevant.  Search
fields allows for substring search within Zimagi queries.


Defining data importation
=========================

To perform import of data within Zimagi, we will also have to define commands 
within the YAML configuration files, but it is worth looking at the Python code 
needed to do the concrete data acquisition first.

The means by which we do this is defined in the code 
``$ZDIR/lib/modules/default/noaa-stations/plugins/source/noaa_stations.py``.
This name—minus the ``.py`` part, is indicated in the file
``$ZDIR/lib/modules/default/noaa-stations/spec/plugins/source.yml``::

  plugin:
    source:
      # Identify providers across modules
      providers:
        noaa_stations:
          requirement:
            min_year:
              type: int
              help: The beginning year to query
            max_year:
              type: int
              help: The end year to query
          option:
            station_ids:
              type: list
              help: A list of station IDs to include
              default: null

Within this configuration, beyond indicating what Python file to incorporate,
we define required and optional fields to make available to that Python code.
In this example, the Python code will *always* have access to integer values for 
``min_year`` and ``max_year`` and *might* have access to a list value named
``station_ids``.  Field names must be spelled as valid Python identifiers.

While some Python code is needed here, it mostly follows a fairly strictly 
stereotyped pattern.  Obviously, the code needed will vary based on the data 
format of the source and any authentication system that might be required to 
access it.  For this module example, we chose data that is publicly available 
and is contained in a fairly straightforward CSV format.

The bulk of this importer is a class called ``Provider`` that needs to define 
three methods, ``.item_columns()``, ``.load_items()``, and ``.load_item()``.
Exactly what other Python libraries you might use are very specific to the 
nature of the data source.  The Zimagi runtime environment **will** make 
available *Pandas* and *requests*, which are certainly two of those that you 
will use very often.

If you need to utilize other libraries, such as database adapters or data format
readers you will need to add them to the Zimagi runtime by **[TODO]**.

Python import code
------------------

Let us look at ``noaa_stations.py`` in a few steps::

    # filename matches name given in plugins data definition
    from systems.plugins.index import BaseProvider
    import requests
    import logging
    import pandas as pd
    import io

    logger = logging.getLogger(__name__)

    class Provider(BaseProvider("source", "noaa_stations")):
	      # Generate a parent class based on 'source' and plugin definition
	      # Three interface methods required: item_columns, load_items, load_item

We do not have to use *requests*, *pandas*, *logging*, or *io*, but they are
particular modules that are useful in the methods below.  All we really need is
to define the class ``Provider`` which has a funny dynamic parent class defined
by passing names to the system class ``BaseProvider``.  You need not think about
the metaclass magic underneath this, just copy the pattern.  Always include 
"source" and the name you defined in ``source.yml`` as strings passed to
``BaseProvider``.

Now let us look at the methods we need::

    def item_columns(self):
        # Return a list of header column names for source dataframe
        return ["station_id", "station_name", "date",
                "temperature", "temperature_attrs",
                "latitude", "longitude", "elevation"]

This one is very simple.  All it does is return a list of string names for 
fields, as we wish to spell them within Zimagi command line or API access.
Continuing, let us look at the simpler ``load_item()`` method next::

    def load_item(self, row, context):
        # Dataframe iterrows passes tuple of (index, object)
        row = row[1]
        # Return values list that maps to header elements in item_columns()
        return [row.STATION, row.NAME, row.DATE,
                None if row.TEMP == 9999.9 else row.TEMP, row.TEMP_ATTRIBUTES,
                row.LATITUDE, row.LONGITUDE, row.ELEVATION]

The task of this method is to take a single ``row`` object and return a list of
values.  The ``row`` object can be anything whatsoever, as long as it lets us
figure out a collection of values to match up with the column names returned by
``item_columns``.  In this specific example, the object received is a tuple 
containing an index and a Pandas Series (as we will see).  The index into the 
underlying Pandas DataFrame is irrelevant to us, but the Series has everything
we care about.

To return a Python list of values, we mostly just access each record in the 
Series, which at this point have names corresponding to the column names in the
source CSV files.  You can see that those are spelled a bit differently than
the names we prefer to use in our module (if nothing else, we do not want the 
names in ALLCAPS), but the translation is obvious enough from their spelling.
We can also, of course, line up the index positions of the column names we used
with the items returned by the method.  In one case, we do some minor data 
cleanup by marking the "missing data" sentinel of 9999.9 as explicitly None 
(i.e. the Python ``None``, which gets represented as ``NULL`` in the RDBMS). In
concept though, we could do whatever other calculation or substitution we wished
to within this method.

Loading items
-------------

The heavy lifting of this data import ``Provider`` class is performed in the
method ``.load_items()``.  Of course, being Python code, we are free to define
whatever other methods might be useful to us within this class, as long as they
do not use these few reserved names::

    def load_items(self, context):
        base_url = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"
        for year in range(self.field_min_year, self.field_max_year+1):
            year_url = f"{base_url}/{year}"
            if not self.field_station_ids:
                # Want all files for this year
                pass
            else:
                # Only pull the list of station_ids given
                for station_id in self.field_station_ids:
                    station_url = f"{year_url}/{station_id}.csv"
                    self.command.info(f"Fetching data from {station_url}")
                    resp = requests.get(station_url)
                    if resp.status_code == 200:
                        logger.info(f"Pulled {station_url}")
                        df = pd.read_csv(io.StringIO(resp.text))
                        yield from df.iterrows()
                    else:
                        logger.info(f"Station {station_id} not present for {year}")

The implementation shown here is partial.  It only accepts the case where 
station IDs are explicitly provided.  We have yet to implement the common case 
where we load "all stations matching the years given."  To do that, we will have
to program a little bit of web scraping to read the directory at the base URL
and figure out which CSV files exist.

Bracketing the part not fleshed out, we see everything that is functionally 
needed in the ``else:`` block.  We start at a base URL which we know, by 
examination and by the documentation of the data source, contains subdirectories
named after years.  Moreover, we have indicated, in the ``source.yml`` file
discussed above, that the fields named ``min_year`` and ``max_year`` are 
required to be present, and to be integers.  To use them within the Python code,
we prefix their names with ``field_``.  

This code loops over years matching the range defined by the fields, then uses
the *requests* module to determine whether a corresponding CSV URL exists. We
also log the status of what was done, which is useful but not required.

The essential operation of the ``.load_items()`` method is that it yields each 
individual ``row`` object of the sort that ``.load_item()`` will consume.  That
concludes the Python code needed for this module.  What remains is entirely to 
configure commands that the Zimagi runtime will use to utilize this Python code
(once combined with base scaffolding code behind the scenes).


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
for reuse.  As well, YAML itself has a feature for literal transclusion of
boilerplate.  This distinction is very similar to the difference between an 
``#include`` directive in languages like C/C++ and *inheritance* of classes in
languages like Python (or C++, or Java, etc).  For better or worse, because 
``import`` is a built-in Zimagi command, we can define subcommands but not new
bases or mixins for it.

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

Data is available locally to be queries from the Vagrant shell or the API now.




