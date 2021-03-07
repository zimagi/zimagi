####################
Components of Zimagi
####################

Zimagi comprises a number of interrelated components.

As a user of Zimagi, you’ll be concerned with six core components.
You’ll interact with these components and customize them to collect,
query, and manipulate your data. These components are:

-  Databases
-  Execution Environment
-  Specifications
-  Plugins
-  Parsers
-  Modules

The Module Developer Guide provides a walk through approach to developing your
own custom capabilities.

Databases
---------

The primary purpose of Zimagi is collecting data from a source or multiple
sources, storing that data in a database, and then letting the user query and
manipulate the data. A relational database is required to define, store, and
access data models. SQLite, PostgreSQL, and MySQL are supported.

A user interacts with a database using the Data API, which lets them import the
data, filter the data, and retrieve slices of the data as they see fit.

Execution Environment
---------------------

An execution environment is where workers operate. After pulling a command from
the command queue, a worker executes the command in the execution environment.
The execution environment is a parallel environment that allows the efficient
execution of jobs, taking advantage of multiple processors or nodes.  Workers
can be scaled across the execution environment in accordance with demand.

Zimagi uses two execution environments: a local environment, and an API-based
execution environment. The execution environments are abstracted away by an
internal framework. This means no matter how commands are given, with the CLI
or the remote API, the same commands will work and be carried out in the
execution environment.

Specifications
--------------

Specifications are used to control how different components of Zimagi’s
subsystems are defined. Zimagi’s management layer relies on specifications to
handle data models, local and API-based commands, and plugins.

Command specifications
~~~~~~~~~~~~~~~~~~~~~~

Commands are defined using both specifications and Python class definitions.
The specifications used to create commands fall into one of three different
categories: Base commands, mixins, and "Command" executables.

Command executables are what actually carry out a command after they are called
by the management layer. Base commands are extended by command executables. The
base commands specify meta-attributes of the commands, such as which roles can
execute the command. To put that another way, base commands give the executable
commands the basic attributes they need to function. This includes queues,
parsers, tables, warning messages and more.

Mixins are used to customize commands for certain desired purposes, and they
can link commands to defined data models, facilitating easier work with those
models.

Data Specifications
-------------------

The Manager uses specs to dynamically build data models. The data model
specifications must include: a source, a validator, and plugins/providers that
control the data formatting.

Like Command specifications, there are three types of data specifications: Base
models, mixins, and data models.

The data models themselves are the actual data types that Zimagi uses to pull,
validate, format, and store data, and they can extend base models.  Base models
define default values for parameters like data name, scope, and relation.

Data models have field definitions which are defined with specifications. A
data model mixin defines multiple fields, and these definitions can be applied
to multiple data models. This lets the user re-use field definitions without
having to explicitly redefine them.  Text fields can be altered through the use
of data specs, but if no specifications are defined, then the default fields
specified by the base models will be used.

Plugin Specifications
---------------------

Specifications are also used for plugins, covered more below. Two types of
specifications are used to implement plugins: the plugin objects and plugin
mixins.

Plugins themselves are used to define method interfaces. Plugin specifications
define a method of interfacing with Zimagi, along with all parameters that the
interface method supports.

Plugins
-------

Zimagi makes use of a plugin system that lets users define swappable methods of
interfacing with the program. Plugins let the user customize how data models
are structured, control how data is imported, and change how commands are
executed.

Plugins can interface with any of Zimagi’s core services. For example, the user
could use a data plugin to change which profiles have access to which data
models, or use an import plugin to alter how imported data is validated.

There are two types of specifications related to plugins: one for plugins
themselves and plugin mixins.

The plugin specifications are used to define a type of interface, as well as
both required and optional parameters. The plugin specifications also contains
specs for how the provider should be interacted with, detailing optional and
required params. Plugin mixins can extend other types of mixins, and they also
take required and optional params.

Parsers
-------

Zimagi uses a collection of data parsers to interface with and manipulate data.
Parsers are used to carry out translations or lookups on input data, returning
the data that results. Zimagi parsers let you filter collected data to find
just the data you want. There are five types of parsers that can currently be
used, all of which parse strings:

-  Conditional value parser. Takes condition, true values and false
   value. Returns data matching conditions.

   (*?> conditional expression ? true expression : false expression*):

-  Configuration (*@configuration_name*): Takes configuration name and
   returns value.

-  State *($state_variable_name*): Takes a state variable name. Returns
   value.

-  Token (*%%state_variable_name:length*): Takes a string used to
   generate a random token that will be stored as a state value, which
   is returned when the state exists.

-  Reference
   (*&data_model([scope_field=value[;..]]):key_field_name[*]:result_field*):

-  Take a query string, returns matching fields for data model.

Modules
-------

Modules are version controlled Git projects that can be used to extend almost
every component of Zimagi. Modules interface with Zimagi’s core services,
extending the components of the Data API, Scheduler, and Command API. You can
use a module to extend plugins, providers, commands, data models, and profiles.
Modules can also be used to extend Django settings or runtime dependencies.

Modules are high-level components that contain customized lower-level
components like plugins and parsers.

Putting It All Together
-----------------------

Zimagi’s Management Layer brings all the different system components together.
It contains default components like data models, plugins, parsers, commands,
and tasks. These basic structures can be extended by user created Modules,
which customize components (defined with specifications) by altering the type
of data that is collected, how the data is parsed, what tasks are carried out,
etc. Regardless of which modules are being used, the management layer and
processor always interacts with the job queue and databases, while data and
feedback about jobs are returned with the Data and Command APIs.
