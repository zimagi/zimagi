Creating a module
=================

This tutorial will demonstrate how you can develop a Zimagi module.

As an example, we will create a module that obtains data from a public
data source provided by the United States National Oceanic and
Atmospheric Administration (NOAA).

We'll be creating a copy of the module available at the following public
GitHub repository:

https://github.com/zimagi/module-noaa-stations

Our module development will be performed locally, giving us an
interactive environment for enhancing and testing feature as they are
added.

The example we will work through utilizes a large collection of
standardized CSV files. At a particular URL, years are used as
subdirectories and within each of those subdirectories are many
individual CSV files, each containing information about data from one
weather station during that year.

Each row in these CSV files contains a mixture of information about the
station itself, such as its name, altitude and latitude, and information
about the observation, such as temperature, humidity, visibility,
precipitation, etc.

Initializing Zimagi
===================

The first thing that we need to do is clone the Zimagi repository itself
onto your local system. This repository is available at:

https://github.com/zimagi/zimagi

Choose a directory to clone the repository to (such as
``$HOME/git/zimagi``). We'll refer to the install directory as
``$ZDIR``.

If you want to edit the environment settings, can copy
``$ZDIR/vagrant/config.default.yml`` to
``$ZDIR/vagrant/config.yml``\ and modify the new file. In most cases,
the default settings will be fine, and this is not necessary.

We'll use a shell prompt showing the leaf of the working directory to
help us orient the path we might be working in. Within ``$ZDIR`` you
simply need to launch the Vagrant configuration, i.e.:

`(zimagi)$ vagrant up`

This will take a few minutes to setup.

Afterwards:

`(zimagi)$ vagrant ssh`

This will put you inside a Vagrant hosted Zimagi console where you may
run commands.

Creating a module skeleton
--------------------------

After logging into the Zimagi console, we can create the skeleton for
our custom Zimagi module.

The goal here is to create a local clone of the module we're developing
underneath the ``$ZDIR`` directory, but the module needs to exist in a
basic, skeleton form first. In other words, before making a module
available within Zimagi, we first need to create a GitHub repository
that contains the skeleton for the module.

All that your module strictly needs is a file called ``zimagi.yml`` at
its root. This file, in its minimal version, only has to define a name
for the module. For example, within our demonstration module:: 

​	(module-noaa-stations)$ cat zimagi.yml `

​	name: "noaa-stations"`

Now we are ready to load the module into Zimagi and enhance it.

Adding a module to Zimagi
-------------------------

Once the skeleton of the module has been defined, we can add it to our
Zimagi instance. We can add the module skeleton with the following
command::

(vagrant) zimagi module add
https://github.com/zimagi/module-noaa-stations.git

Adjust the GitHub URL as needed to point to your repository. Notice that
at this point we are only using the ``https://`` URL rather than the
``git@`` URL since the Vagrant shell does not have SSH credentials
configured. This is not a problem, and we will enhance the connection
below.

Within the Vagrant shell, there's a command we can use to verify that
any changes or configurations we want to make have actually been made::

​	(vagrant) zimagi env get

We'll use this to check and make sure that the module has actually been
added to Zimagi.

Within your local terminal, we can use the following commands to see
where the module has been cloned::

​	(zimagi)$ cd lib/modules/default/ 

​	(default)$ ls noaa-stations

In the minimal version, this will contain only the ``zimagi.yml``, shown
above, but you may have created a ``LICENSE`` or a ``README`` or other
repository contents.

Creating a local remote
-----------------------

We now need to add a local remote connection to the working Zimagi repo.
We assume the system you are working on has established SSH credentials
with GitHub, and that you are able to run authenticated commands. You
can add a local remote with the following commands in your terminal
shell::

​	(zimagi) git remote add noaagit@github.com:zimagi/module-noaa-stations.git 

​	(zimagi) git push noaa #Nothing has changed yet, but this will now work

Whenever you have new functionalities you want to integrate into Zimagi,
you need to run the following commands in the Zimagi Vagrant shell::

​	(vagrant) # Pull changes from GitHub: 

​	(vagrant) zimagi module save noaa-stations 

​	(vagrant) zimagi makemigrations

From this point forward, you can (and probably should) work within the
module clone that is located at``$ZDIR/lib/modules/default/noaa-stations`` 

(or whatever leaf path corresponds to the name you gave to your module). 

Notice that this directory matches the ``name`` key defined inside the module's
``zimagi.yml`` file rather than the repository name itself.

In this example, the repository is named ``module-noaa-stations`` while the module name is ``noaa-stations``; but either name can be whatever you like.

Developing module functionality
===============================

The Zimagi system scans a number of YAML configuration files to enable a
module's defined capabilities. Most of the requirements for these
capabilities are driven by the various keys inside these YAML files, but
it's helpful to organize directories and filenames according to the YAML
files definitions, as it helps identify the location of a given
definition.

Configurations will live inside the ``spec/`` directory of the module
repository.

Defining roles
--------------

We would like to define roles for differing kinds of users who have
different capabilities within the system. We'll place these role
definitions in ``spec/roles.yml``, for example::

(noaa-stations) cat spec/roles/yml 

roles: 

​	noaa-admin: Administer NOAA
​	weather data viewer: User who can view weather data

We will use these roles later on to control what actions a given named
role may perform. We can define as many roles as we like and name them
however we like. However, names with dashes or underscores are generally
easier to enter into other configuration files, since quoting is not
needed when spaces are not used.

Data mixins
-----------

Zimagi allows you to configure "mixins" which are a kind of boilerplate
that lets you avoid needing to redefine objects used in multiple places.
Zimagi uses both ``data_mixins`` or ``command_mixins``.

Here's how we can define a ``data_mixin``. The same name (in this case
``station``) is used at several levels, but with somewhat different
meanings in the different positions. Let us look at an example defined
within ``spec/data/station.yml``::

data\_mixins: 

​	station: 

​		class: StationMixin 

​		fields: 

​			station: 

​				type: "@django.ForeignKey" 

​				relation: station 

​				options: 

​				"null": true 

​				on\_delete: "@django.PROTECT" 

​				editable: false

At the highest level, the mixin definition is a database column
possessing various attributes. This definition is used in multiple
places to cerate a foreign key relationship. The initial mention of
``station`` is the name of our database column, and below it we define
the class and the fields that class contains, the primary field being a
different use of ``station``.

The Django data type identifies the relationship, with YAML keys
``type`` and ``relation`` indicating the primary table. The ``options``
values correspond to database table properties in a straightforward way.

Explicitly specifying a ``class`` name, as is done above, is optional
(and is not used for any real externally-facing purposes, only in code
generation). Mixins may also have inheritance relationships by
specifying a ``base``, although we don't specify one here.

Command mixins
--------------

Much like how you can define a mixin for Data, you can also create a
Command mixin. Here's how we can create a command mixin::

command\_mixins: 

​		#Generate methods on other classes station: class:
​		StationCommandMixin 

​		meta: 

​		#Name used in commands (not required to be
same as table) #Ref: mixin\_name 

​			station: 

​			#Link back to dynamic class station 

​			data: station 

​			#Positive integer (lowest is highest priority)
​			priority: 1

Once again, the initial mention of ``station`` is the column in our
database that we want to reference. The second use of ``station``
indicates a meta attribute we want to create. The key elements for this
attribute are data and priority, with data referencing the data source
(``station``) and priority expressing the order in which commands are
shown when ``help`` is called.

Defining a data model
=====================

For a module to do something useful, we need to configure its *data
model*. The data model uses a Django-style template to define a
relational database table, where the data will actually be stored.

For this example project, there are two data types used; this is very
similar to the way you might define multiple tables in an RDBMS (and in
fact maps to exactly that "under the hood"). The two data types are:
``stations`` and ``observations``. The data types are defined at the
following file locations:

-  ``$ZDIR/lib/modules/default/noaa-stations/station.yml``
-  ``$ZDIR/lib/modules/default/noaa-stations/observations.yml``

The file path follows a natural pattern, although it isn't required to
use this pattern. We could put the definitions in any files we wanted,
as long as they live in the module's directory hierarchy and have the
extension ``.yml``. The structure of these two files is very similar,
although ``station.yml`` defines more attributes of the database
than\ ``observations.yml`` does. This is because some mixins and
**bases** (more on that soon) are defined in ``station.yml`` and hence
don't need to be duplicated in ``observations.yml``.

Within a data model, we typically define a top-level key ``data_base``
and another under the key ``data``.

In the case of this module's organization, both ``station.yml`` and
``observations.yml`` have their own top level keys. For example, we
currently have the module's data types organized like this::

#in station.yml

data: 

​	station:

​		#... more info ...

#in observations.yml

data: 

​	observation:

​		#... more info ...

The module's data type architecture is decided by the module developer,
and we could very easily put all of the definitions in the same file if
we wanted to. For example, a different module could have the data types
defined like this::

#in data-model.yml (not a file in this module)

data: 

​	station:

​	#... more info ...

 	observation:

​	#... more info ...

Defining data\_base objects
---------------------------

In this module, the "abstract" base object ``station`` is used by
concrete data objects (including one called ``station``). Let us look at
that definition, here contained in ``station.yml`` (but again, it could
live elsewhere if you prefer)::

data\_base: 

​	station:

 		#Every model (usually) based on resource

​		class: StationBase  

​		base: resource  

​		mixins: [station]  

​		id\_fields: [number]  

​		meta:

 			#Number alone is probably unique, demonstrate compound key

 			unique\_together: [number, name]

 			#Updates must define station

 			scope: station

This definition has several notable elements. The field named ``number``
is specific to the data we're working with. The NOAA data defines a CSV
column called ``STATION`` which is a special number weather services use
for identification, and also a column called ``NAME`` that is a verbose
description of the weather station. We've called these attributes
``number`` and ``name`` in the module, but we are free to use any names
whatsoever.

Now we'll see how to define a compound key. We create a compound key by
giving the name of the key followed by its values in brackets.

``key_name``:``[value_1, value_2]``

We are declaring in the ``data_base`` that the combination of
``number``\ and ``name`` will define a unique identifier. We define this
as a compound key and map it to the ``unique_together`` attribute.
Despite the station object now having a ``unique_together`` attribute,
only ``number`` is used as the ID for queries. Odds are that only the
``number`` attribute will be truly unique and the ``name`` descriptions
could change over time. We've created the ``unique_together`` key just
as an example of how to create compound keys.

Defining data objects
---------------------

With the scaffolding in place, we can define an actual data object. Let
us quickly notice something about the ``observation`` object before
presenting the full ``station`` object::

#Inside observation.yml

data: 

​	observation: 

​		class: Observation

 		#Observation extends Station base data model

 		base: station

Because an observation represents a "child table", it is based on the
parent ``data_base`` object ``station``, inheriting ``station``'s
attributes. Let us look at (almost) the entire definition for the
``station`` object::

data:

#Actual data models turned into tables

#Fields 'name', 'id', 'updated', 'created' implicitly

#created by base resource (id/updated/created internal)

 	station:  

​		class: Station

​			#Environment extends resource in Zimagi core

​			base: environment

​			#Primary key (not necessarily externally facing)

​			id\_fields: [number, name]

​			#Unique identifier within the scope

​			key: number  

​			roles:

​				#Redundant to specify 'admin'

​				edit: [noaa-admin, admin]

​				#Editors are automatically viewers

​				#Public does not require authentication

​				#(viewer will authenticate if public were not listed)

​				view: [viewer, public]  

​			fields:  

​				number:  

​					type: "@django.CharField"

​					options:  

​							"null": false  

​							max\_length: 255

​							#editable is default (not specified)

​				lat:

 					#In degrees

​					type: "@django.FloatField"  

​					options:  

​						"null": true

​				#'lon' and 'elevation' defined in same manner as 'lat'

​				meta:  

​					unique\_together: [number, name]

​					#Display ordered by elevation and number

​					ordering: [elevation, number]

​					#Fuzzy string search

​					search\_fields: [number, name]

A number of things are happening in this definition. First, we create an
actual ``station`` object, with a corresponding RDBMS table. The table
will not yet have a way to be populated with this definition, but this
determines its schema and Zimagi will create the empty table based on
this table schema.

We can define a primary key as ``id_fields`` and an access identifier as
``key``. These may often be the same, but need not be, as the example
illustrates.

| We can also define access permissions to this data object by setting
the ``roles`` key and its values. These ``roles`` correspond to those we
created earlier. The special roles *admin* and *public* are always
available, but any other strings may be used to define various
permissions (assuming they are defined as roles).
| The role *admin* will always have all permissions, but we list it here
to illustrate its existence.

When defining a data element it's crucial to define the fields that
element will contain and use. The key ``fields`` lets us list these,
along with data types and properties. Fields can have whatever names are
convenient for us; we will see later how they are translated from the
names being used in the underlying data sources (those underlying data
sources probably use a variety of different names, and Zimagi will
present a more unified interface to the data).

Data types are provided using Django data definition types, surrounded
by quotes. For example, latitude (named ``lat`` by us) is a
``@django.FloatField`` type. Within each field, we may define a few
constraints, such as its NULL-ability and, for a string, its maximum
length.

We may define a few special attributes of the data object. For example,
by default, queries of this data will be sorted by elevation then by
(station) number. This is again chosen for illustration, not any
specific business need within this particular module; in other cases, an
order may be relevant. Search fields allows for substring search within
Zimagi queries.

Defining data importation
=========================

In order to import data into Zimagi, we also have to define commands
within the YAML configuration files, but it's worth looking at the
Python code needed to do the actual data acquisition first.

The means by which we do this is defined in the code located here:
``$ZDIR/lib/modules/default/noaa-stations/plugins/source/noaa_stations.py``

We use the following file to indicate the ``noaa_stations`` file (minus
the ``.py`` in the file name):

``$ZDIR/lib/modules/default/noaa-stations/spec/plugins/source.yml``

Let's take a look at the ``.yml`` file that references ``noaa_stations``::

plugin: 

​	source:

​	#Identify providers across modules

​	providers:  

​		noaa\_stations:  

​			requirement:  

​				min\_year:  

​					type: int 
​					help: The beginning year to query  

​				max\_year:  

​					type: int  

​					help: The end year to query  

​			option:  

​				station\_ids:  

​					type: list  

​					help: A list of station IDs to include  

​					default: null

Within this configuration we indicate the Python file to incorporate,
and also define both the required and optional fields that should be
available to that Python code. In this example, the Python code will
*always* have access to the integer values for ``min_year`` and
``max_year`` and *might* have access to a list value named
``station_ids``. Field names must be spelled as valid Python
identifiers.

While some Python code is needed here, it mostly follows a fairly
strictly stereotyped pattern. Obviously, the code needed will vary based
on the data format of the source and any authentication system that
might be required to access it. For this module example, we chose data
that is publicly available and is contained in a fairly straightforward
CSV format.

The bulk of this data importer is a class called ``Provider``. It needs
to define three methods: ``.item_columns()``, ``.load_items()``, and
``.load_item()``.

Exactly what other Python libraries you might use are very specific to
the nature of the data source. The Zimagi runtime environment **will**
make available *Pandas* and *requests*, but you are free to use other
libraries for the handling of the data source as you see fit.

If you need to utilize other libraries, such as database adapters or
data format readers you will need to add them to the Zimagi runtime by
**[TODO]**.

Python import code
------------------

Let's take a look at ``noaa_stations.py`` file::

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

We do not have to use *requests*, *pandas*, *logging*, or *io*, but they
are useful in the methods below. All we really need is to define the
class ``Provider`` which has a funny dynamic parent class defined by
passing names to the system class ``BaseProvider``. You don't need to
understand the metaclass magic underneath this, just copy the pattern
and be sure to include "source" and the name you defined in
``source.yml`` as strings passed to\ ``BaseProvider`` (in this case
"noaa\_stations").

Now let's look at the methods we need::

    def item_columns(self):
        # Return a list of header column names for source dataframe
        return ["station_id", "station_name", "date",
                "temperature", "temperature_attrs",
                "latitude", "longitude", "elevation"]

This one is very simple. All it does is return a list of string names
for fields, as we wish to spell them within Zimagi command line or API
access.

Now let's look at the ``load_item()`` method next::

    def load_item(self, row, context):
        # Dataframe iterrows passes tuple of (index, object)
        row = row[1]
        # Return values list that maps to header elements in item_columns()
        return [row.STATION, row.NAME, row.DATE,
                None if row.TEMP == 9999.9 else row.TEMP, row.TEMP_ATTRIBUTES,
                row.LATITUDE, row.LONGITUDE, row.ELEVATION]

This method takes a single ``row`` object and return a list of values.
The ``row`` object can be anything, as long as it lets us figure out
which collection of values match up with the column names returned
by\ ``item_columns``. In this specific example, the object received is a
tuple containing an index and a Pandas Series (as we will see). The
index into the underlying Pandas DataFrame is irrelevant to us, but the
Series has everything we care about.

To return a Python list of values, we mostly just access each record in
the Series, which at this point have names corresponding to the column
names in the source CSV files. You can see that those are spelled a bit
differently than the names we prefer to use in our module (if nothing
else, we do not want the names in ALLCAPS), but the translation is
obvious enough from their spelling.

We can line up the index positions of the column names we used with the
items returned by the method. As an example of the kinds of
transformations we can apply to the data, we'll do some minor data
cleanup by marking the "missing data" sentinel of 9999.9 as explicitly
None (i.e. the Python ``None``, which gets represented as ``NULL`` in
the RDBMS). We could do whatever other calculation or substitution we
wished to within this method.

Loading items
-------------

The heavy lifting of the data import ``Provider`` class is performed in
the method ``.load_items()``.

Python let's us define whatever other methods might be useful to us
within this class, as long as they do not use these few reserved names::

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

The implementation shown here is partial. It only accepts the case where
station IDs are explicitly provided. We have yet to implement the common
case where we load "all stations matching the years given." To do that,
we will have to program a little bit of web scraping to read the
directory at the base URL and figure out which CSV files exist.

Bracketing the part not fleshed out, we see everything that is
functionally needed in the first ``else:`` block. We start at a base URL
which we know, by examination and by the documentation of the data
source, contains subdirectories named after years. Moreover, we have
indicated, in the ``source.yml`` file discussed above, that the fields
named ``min_year`` and ``max_year`` are required and must be integers.
To use them within the Python code, we prefix their names with
``field_``.

This code loops over years matching the range defined by the fields,
then uses the *requests* module to determine whether a corresponding CSV
URL exists. We also log the status of what was done, which is useful but
not required.

The essential operation of the ``.load_items()`` method is that it
yields each individual ``row`` object of the sort that ``.load_item()``
will consume. That's all the Python code needed for this module. Now we
just need to configure the commands that the Zimagi runtime will employ
to utilize this Python code (once combined with base scaffolding code
behind the scenes).

Defining commands
=================

The final step in being able to actually *use* the data objects we have
configured is to define the Zimagi commands that import their data and
query them. By adding a ``station`` command, we automatically add a
collection of subcommands associated with querying data.

When creating our ``station`` command, we can define a reusable
``command_base`` that might be utilized by various commands to avoid
repetition. In this module, we define the ``command_base`` like this::

command\_base:

 	#Define a base command with settings

 	#Same name as data model by convention, not requirement

 	station\_base:  

​		class: StationCommandBase  

​		mixins: [station]

​		#Accessible via the API

​		server\_enabled: true

​		#Only these groups can use 'station' commands

​		groups\_allowed: [noaa-admin] 

We can choose any name we want for the command base, but
``station_name`` is an obvious choice.

We gave the base an (optional) internal class name in the generated
code, and it uses the mixin we discussed earlier. The only elements
where we actually make design decisions are ``server_enabled`` and
``groups_allowed``.

We set ``server_enabled`` to ``true`` to expose commands within the
RESTful JSON API (i.e. for web requests). We also give the
``groups_allowed`` key the role that we want to be able to use:
``noaa-admin``.

We've create the command base, but now we need to set up the actual
command. The names of the commands are defined by by us and they way
that they are used defines them. This means that the command names
aren't constrained by the name of the data object or by mixins.

To demonstrate this, we'll create two different subcommands that carry
out the same tasks but have different names. One we will call
``station`` and the other we will call ``bahnhof``. ("Bahnhof" is simply
a German word for "station")::

command: 

​	station:

​	#Maps back to data object

​		resource: station  

​		base: station\_base

​		#Show later than core commands

​		priority: 99 

​		groups\_allowed: [noaa-admin, admin]

#Alternate command (does same thing to demonstrate)

​	bahnhof:

​	#Maps back to data object

​	resource: station

​	base: station_base

​	#Tie into object type (to match prefix for mixin)

​	#I.e. match ref mixin_name

​	base_name: station

​	#Show later than core commands

​	priority: 98

The only differences between these two subcommands, other than their
names, is that one command overrides its base. In the case of the
``station`` subcommand, we redefine ``groups_allowed``. (This is not a
real change in behavior since *admin* is always allowed to do everything
anyway. It's just a demonstration of the ability to override command
attributes.)

We also choose slightly different ``priority`` values for the two
spellings, which will cause ``bahnhof`` to appear earlier than
``station`` when you run ``vagrant@zimagi-noaa:~$ zimagi help`` inside
the Vagrant shell.

As the module is configured now, the ``observation``\ priority is even
higher (105), so it appears after both.

Import commands
---------------

We have now defined a ``station`` (or ``bahnhof``) command as a place to
put subcommands we use in querying data. But we need to define an
``import`` subcommand to load the data from our remote source(s) into
the local RDBMS.

For this module, we define that inside
``$ZDIR/lib/modules/default/noaa-stations/spec/import/station_observations.yml``.

This YAML file includes a new YAML feature we have not seen before. In
this file, we use mixins and bases for commands and data models as a way
of providing templates for reuse.

YAML itself has a feature for literal transclusion (the inclusion of
parts of a document into one more other documents) of boilerplate code.

This feature is very similar to the difference between an ``#include``
directive in languages like C/C++ and *inheritance* of classes in
languages like Python (or C++, or Java, etc). For better or worse,
because ``import`` is a built-in Zimagi command, we can define
subcommands but not new bases or mixins for it.

The YAML features we'll use are called *anchors* and *aliases*. They
always occur in the same physical file, so they are somewhat different
from C-style ``#include`` directives in that respect. Let's look first
at the anchor we'll use::

_observation: &observation 

​	source: noaa_stations 

​	data: 

​		station: 

​			map:

​				#"number" as defined in spec/data/station.yml

​			number:

​				#"station\_id" as defined in plugins/source/noaa\_stations.py

​				column: station\_id 

​			name:  

​				column: station\_name  

​			lat:  

​				column: latitude  

​			lon:  

​				column: longitude  

​			elevation:  

​				column: elevation

  	observation:
  		relations: 

​				station_id: 

​				#Mapping back to "station" as defined in spec/data/station.yml

​        		data: station

​				#Mapping back to plugins/source/noaa_stations.py

​        		column: station_id
​        		required: true
​		 map:
​     		date: 
​        		column: date
​     		temp:

​				column: temperature
​    		temp_attrs: 
​				column: temperature_attrs

This anchor is something we'll likely use again as we develop more
commands. The anchor value/name is ``&observation``, but as we will see,
when we *alias* it we will spell that as ``*observation`` (these
spelling are loosely inspired by references and pointers in C/C++ family
languages). The name of the key with a leading underscore,
``_observation`` is irrelevant—you can use any identifier name you like,
and it isn't used again elsewhere. This is just something that needs to
be there syntactically.

We indicate the ``source`` by defining a *provider*. Recall the
definition in ``spec/plugins/source.yml`` that was discussed above; this
is where the spelling ``noaa_stations`` comes from. Given that source,
we define ``data`` import elements ``station`` and ``observation``.
These each have a ``map`` key that maps database table column names to
names used within the Zimagi shell and API. They might also have a
``relations`` key that defines a foreign-key relationship.

The final component of our (simple) module is the definition of an
actual ``import`` subcommand. We can create that subcommand as follows::

import: 

​	test:

​		#Identical to including the body of \_observation here

 		<<: \*observation

​		#In concept we could override definition from reference, e.g.

​		#source: something\_else

​		tags: [observations]  

​		min\_year: 1929  

​		max\_year: 1931 

​		station\_ids: ["03005099999", "99006199999"]

The special key ``<<`` is the one that indicates an alias back to the
anchor defined above. It is exactly as if we had typed the entire body
of ``_observation`` at that same point in the file

The key ``tags`` indicates **[TODO]**.

For this simple subcommand ``test`` we give a fixed value for a
``min_year`` and ``max_year``, and also a specific list of
``station_ids`` that we will import from the NOAA website. In a more
flexible command, you would indicate these elements using switches to a
command, but this demonstrates the general pattern.

At this point—perhaps after running ``zimagi module save noaa-stations``
again, if needed, we can run::

​	vagrant@zimagi-noaa:~$ zimagi import test

Data is available locally to be queries from the Vagrant shell or the
API now.
