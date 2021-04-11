=====================
Defining a data model
=====================

For a module to do something useful, we need to configure its *data model*.  
This expresses, in a somewhat Django-centric way, a mapping onto relational 
database tables where the data is actually stored.

For this example project, there are two data types used; this is very similar
to the way you might define multiple tables in an RDBMS (and in fact maps to 
exactly that "under the hood").  We have ``stations`` and ``observations``.
The definitions of these kinds of data are contained in the files:

 * ``$ZDIR/lib/modules/default/noaa-stations/data/station.yml``
 * ``$ZDIR/lib/modules/default/noaa-stations/data/observations.yml``
 
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
 
We are declaring in the ``data_base`` that the combination of ``number`` and 
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
``data_base`` object ``station``, inheriting ``station``'s attributes.  Let us
look at (almost) the entire definition for the ``station`` object::

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

The crucial element in defining a data element is the fields it will contain
and use.  The key ``fields`` lets us list these,  along with data types and
properties.  Fields can have whatever names are convenient for us; we will see
later how they are translated from whatever names are used in the underlying
data sources (quite likely, those underlying data sources use a variety of
different names, and Zimagi will present a more unified interface to the data).

Data types are provided using Django data definition types, quoted.  For example, 
latitude (named ``lat`` by us) is a ``@django.FloatField`` type.  Within each
field, we may define a few constrains, such as its NULL-ability and, for a 
string, its maximum length.

We may define a few special attributes of the data object.  For example, by 
default, queries of this data will be sorted by elevation then by (station)
number.  This is again chosen for illustration, not any specific business need
within this particular module; in other cases, an order may be relevant.  Search
fields allows for substring search within Zimagi queries.

