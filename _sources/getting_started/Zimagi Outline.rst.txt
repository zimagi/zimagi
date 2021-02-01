Part 1: What Need Does Zimagi Serve/Fulfill?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What is Zimagi?
^^^^^^^^^^^^^^^

-  Emphasis that Zimagi can abstract data from any type of source, like
   FEC, into a useful common model.

-  Can unify data originating from multiple sources/different formats
   through the use of common keys.

-  Can be installed anywhere, doesn’t require dedicated server--built
   using open-source libraries and languages, no need to learn a
   proprietary system

-  Distributed data imaging and distribution platform, intended to be
   small/modular and extensible, for the satisfaction of different
   business needs

-  Zimagi ecosystem

-  Two sets of users
-  Module Developers and Module Users

How Zimagi is Different?
^^^^^^^^^^^^^^^^^^^^^^^^

-  Clarify how Zimagi is different from extent services like Luigi,
   Airflow, and Jenkins

-  A Tabular Comparison of what it is and what it is not.

1.5 (Possible Section) -- For Regular End Users:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    * Can Just Pip Install Zimagi
    * How to use for basic operations

Part 2: Zimagi Components
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Briefly explain about the components of Zimagi and their
   characteristics:
-  Modules
-  Environment
-  Config
-  Specification
-  Database
-  Plugins

Part 3: Zimagi CLI Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Briefly explain CLI Commands:
-  Environment Commands
-  Database Commands
-  Scheduler Commands
-  Data import Commands, etc.

Part 4: Using your Zimagi Modules (Look at an example Zimagi app, i.e. the FEC module.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Briefly discuss messiness of source data (make a case for using
   Zimagi)

How to Launch:
^^^^^^^^^^^^^^

-  Vagrant used to configure development environment:

   -  Clone repository and install core
   -  Spin up Vagrant instance, then Vagrant SSH

-  User Docker Container to ready dev environment for use:

   -  Core of Zimagi is a project workspace/environment. You can create
      new environments for business needs.

   -  CLI runs Docker container, which contains all environments.

   -  Every module has Zimagi YAML file at root, which definces what
      libraries it uses and what to install.

   -  Final step of dev environment setup is building container and
      installing everything from Docker image:

   -- At initial setup, Docker instance contains only Zimagi core and
   Python instances.

   -- Docker Image is built and saved. Thereafter, Zimagi relies on
   local image, not Docker hub image.

   -- ``image get`` sets up basic configuration setting for the
   environment, enables interaction, and creates an initial database.

   -- When running database in CLI mode, SQLite is used as DB platform
   by default, and it's opened/closed on demand.

   -- PostGres DB can be installed.

Perform Useful Queries as Examples:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Into to the command and data APIs:

   -  Compatible REST data access system, carries out querying and
      downloading in JSON data format.

-  Queries as commands:

   -  To import parts of dataset use ``zimagi import`` and specify name
      of desired slice (ex. "offices", "parties")
   -  Names are defined under "specs/import".
   -  After setup, Zimagi interacts with API to download data. Can
      define things like URLs in the "utility" Python script.

-  Queries as RESTful API Calls:

   -  Interact with URLs, DataAPIRouter makes API endpoints accessible.
   -  Can leverage API to view dataset with different filters and get
      data returned in various formats.

-  Scheduling data acquisition/updates:

   -  Intro to schedule module

   -  Demonstrate examples of scheduling

   ​ -- Every single command (like ``import``) can be scheduled using
   date-times and arguments like ``begin`` and ``end`` dates. You can
   also see all schedules with ``schedule list``.

More Advanced Topics/Customization:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Adding modules and extending system:

   -  Add modules to extend the system. You can add modules by providing
      GitHub repo, default branch is master.
   -  Reboot system after installing modules

-  How to control data imports and data collection:

   -  In specifications, import specs let you control how is imported
      (specify subsets, entries, validators, types, etc.)
   -  Plugins/source lets you specify variable types, which can be used
      to slice data as you like.

Part 5: Building Your First Zimagi Module 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pull current weather data using module https://github.com/zimagi/module-noaa-stations.

What YAML files need to be touched?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Everything important to data retrieval is defined under "plugins"
   with the YAML files. Zimagi will check under “models” for
   corresponding named Python script.
-  Starts with a generic base provider as a parent that is changed with
   the child (extending utility class), adding logic for things like
   pagination, etc.

What are the keys/values that needed to be created in the mapping?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Base Data models should define relationships between keys and vals.
-  Define key properties for access and use specs to control how values
   are handled (formatted with plugins and providers)

Publishing a Created Module
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wishlist of Documentation:
^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Need a boilerplate: zimagi.yml in the repository or a command to
   initialize the zimagi.yml file.

