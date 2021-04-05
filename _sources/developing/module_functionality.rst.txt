===============================
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

  (noaa-stations) cat spec/roles.yml
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

The initial mention of ``station`` is the name of our database column, and
below it we define the class and the fields that class contains, the primary
field being a different use of ``station``.

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

The initial mention of ``station`` is the column in our database that we want
to reference. The second use of ``station`` indicates a meta attribute we want
to create. The key elements for this attribute are data and priority, with data
referencing the data source (``station``) and priority expressing the order in
which commands are shown when ``help`` is called.


* :ref:`search`
