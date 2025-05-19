# Zimagi   Overview

*****************

.. image:: ./kix.7ft3utqvnd8j.png



1. Zimagi   Role Specifications

*********************************

1.1.   Role  (key:  roles )
===========================

+--------+
| {name} |
+--------+

+----------------------------------------------------------------------------------------+
| Role description text                                                                  |
+----------------------------------------------------------------------------------------+
| Role names will be a dash (-) separated string that represents a user group internally |
+----------------------------------------------------------------------------------------+

2.   Zimagi   Data Specifications

*********************************

.. image:: ./kix.u09pexpvp3a8.png


2.1.   Model Mixin  (key:  data_mixins )
========================================

+--------+
| {name} |
+--------+

+--------+------------+----------+----------------------------------------------------------------------------+
| Spec   | Type       | Value    | Description                                                                |
+--------+------------+----------+----------------------------------------------------------------------------+
| class  | str        | optional | Allows explicit specification of generated class names                     |
|        |            |          | (Pascal Case class name)                                                   |
+--------+------------+----------+----------------------------------------------------------------------------+
| base   | str        | optional | Base mixin class from available mixins or default base mixin class if not  |
|        |            |          | Specified (as spec name)                                                   |
+--------+------------+----------+----------------------------------------------------------------------------+
| mixins | str        | optional | Parent model mixin classes (as spec names)                                 |
|        | list <str> |          |                                                                            |
+--------+------------+----------+----------------------------------------------------------------------------+
| fields | dict       | optional | Collection of named field objects.  See “Field” section below              |
+--------+------------+----------+----------------------------------------------------------------------------+



2.2.   Base Model  (key:  data_base )
=====================================

+--------+
| {name} |
+--------+

+-----------+------------+----------+--------------------------------------------------------------------+
| Spec      | Type       | Value    | Description                                                        |
+-----------+------------+----------+--------------------------------------------------------------------+
| class     | str        | optional | Allows explicit specification of generated class names             |
|           |            |          | (Pascal Case class name)                                           |
+-----------+------------+----------+--------------------------------------------------------------------+
| base      | str        | optional | Base model class from available base models or default base        |
|           |            |          | model class if not specified (as spec name)                        |
+-----------+------------+----------+--------------------------------------------------------------------+
| mixins    | str        | optional | Parent model mixin classes (as spec names)                         |
|           | list <str> |          |                                                                    |
+-----------+------------+----------+--------------------------------------------------------------------+
| roles     | dict       | optional | Permissions for model:                                             |
|           |            |          | (keyword “public” can be used for anonymous access)                |
|           |            |          | view: specification defined roles who can access and               |
|           |            |          | search for model instances                                         |
|           |            |          | edit: specification defined roles who can create, edit,            |
|           |            |          | and remove model instances                                         |
+-----------+------------+----------+--------------------------------------------------------------------+
| fields    | dict       | optional | Collection of named field objects.  See “Field” section below      |
+-----------+------------+----------+--------------------------------------------------------------------+
| meta      | dict       | optional | Meta properties for model.  See “Meta” section below               |
+-----------+------------+----------+--------------------------------------------------------------------+
| id        | str        | optional | Idenfier field name if autogenerated primary key value is not used |
|           |            |          | A time + hex digest is used for differentiation by default         |
+-----------+------------+----------+--------------------------------------------------------------------+
| id_fields | str        | optional | Field names whose values are used to generate the default hex      |
|           | list <str> |          | digest for the model primary key                                   |
+-----------+------------+----------+--------------------------------------------------------------------+
| key       | str        | optional | Scoped access key field name.  This is the primary reference field |
|           |            |          | in the system (normally “name” by default)                         |
+-----------+------------+----------+--------------------------------------------------------------------+
| packages  | str        | optional | Package names used to group models together for deployment         |
|           | list <str> |          | and synchronization                                                |
+-----------+------------+----------+--------------------------------------------------------------------+
| triggers  | dict       | optional | State variable names of triggers who execute model initialization  |
|           |            |          | procedures on updates (used for application startup)               |
|           |            |          | check: state variables checked and cleared on startup              |
|           |            |          | save: state variables set on model updates                         |
+-----------+------------+----------+--------------------------------------------------------------------+


2.3.   Model  (key:  data )
===========================

+--------+
| {name} |
+--------+

+-----------+------------+----------+--------------------------------------------------------------------+
| Spec      | Type       | Value    | Description                                                        |
+-----------+------------+----------+--------------------------------------------------------------------+
| class     | str        | optional | Allows explicit specification of generated class names             |
|           |            |          | (Pascal Case class name)                                           |
+-----------+------------+----------+--------------------------------------------------------------------+
| base      | str        | optional | Base model class from available base models or default base        |
|           |            |          | model class if not specified (as spec name)                        |
+-----------+------------+----------+--------------------------------------------------------------------+
| mixins    | str        | optional | Parent model mixin classes (as spec names)                         |
|           | list <str> |          |                                                                    |
+-----------+------------+----------+--------------------------------------------------------------------+
| roles     | dict       | optional | Permissions for model:                                             |
|           |            |          | (keyword “public” can be used for anonymous access)                |
|           |            |          | view: specification defined roles who can access and               |
|           |            |          | search for model instances                                         |
|           |            |          | edit: specification defined roles who can create, edit,            |
|           |            |          | and remove model instances                                         |
+-----------+------------+----------+--------------------------------------------------------------------+
| fields    | dict       | optional | Collection of named field objects.  See “Field” section below      |
+-----------+------------+----------+--------------------------------------------------------------------+
| meta      | dict       | optional | Meta properties for model.  See “Meta” section below               |
+-----------+------------+----------+--------------------------------------------------------------------+
| id        | str        | optional | Idenfier field name if autogenerated primary key value is not used |
|           |            |          | A time + hex digest is used for differentiation by default         |
+-----------+------------+----------+--------------------------------------------------------------------+
| id_fields | str        | optional | Field names whose values are used to generate the default hex      |
|           | list <str> |          | digest for the model primary key                                   |
+-----------+------------+----------+--------------------------------------------------------------------+
| key       | str        | optional | Scoped access key field name.  This is the primary reference field |
|           |            |          | in the system (normally “name” by default)                         |
+-----------+------------+----------+--------------------------------------------------------------------+
| packages  | str        | optional | Package names used to group models together for deployment         |
|           | list <str> |          | and synchronization                                                |
+-----------+------------+----------+--------------------------------------------------------------------+
| triggers  | dict       | optional | State variable names of triggers who execute model initialization  |
|           |            |          | procedures on updates (used for application startup)               |
|           |            |          | check: state variables checked and cleared on startup              |
|           |            |          | save: state variables set on model updates                         |
+-----------+------------+----------+--------------------------------------------------------------------+


2.4.   Field  (embedded)
========================

+--------+
| {name} |
+--------+

+----------+------+----------+---------------------------------------------------------------------------------------------------------------+
| Spec     | Type | Value    | Description                                                                                                   |
+----------+------+----------+---------------------------------------------------------------------------------------------------------------+
| type     | str  | optional | Django field class reference (starting with an @ (lookup))                                                    |
|          |      |          | “django” shortcut available for core Django fields                                                            |
|          |      |          | BinaryField                                                                                                   |
|          |      |          | IntegerField                                                                                                  |
|          |      |          | SmallIntegerField                                                                                             |
|          |      |          | BigIntegerField                                                                                               |
|          |      |          | PositiveIntegerField                                                                                          |
|          |      |          | PositiveSmallIntegerField                                                                                     |
|          |      |          | DecimalField                                                                                                  |
|          |      |          | FloatField                                                                                                    |
|          |      |          | BooleanField                                                                                                  |
|          |      |          | NullBooleanField                                                                                              |
|          |      |          | CharField                                                                                                     |
|          |      |          | TextField                                                                                                     |
|          |      |          | DateField                                                                                                     |
|          |      |          | DateTimeField                                                                                                 |
|          |      |          | TimeField                                                                                                     |
|          |      |          | DurationField                                                                                                 |
|          |      |          | EmailField                                                                                                    |
|          |      |          | FileField                                                                                                     |
|          |      |          | FilePathField                                                                                                 |
|          |      |          | ImageField                                                                                                    |
|          |      |          | GenericIPAddressField                                                                                         |
|          |      |          | URLField                                                                                                      |
|          |      |          | SlugField                                                                                                     |
|          |      |          | ForeignKey (requires “relation” specification)                                                                |
|          |      |          | ManyToManyField (requires “relation” specification)                                                           |
|          |      |          | “fields” shortcut available for core ZImagi fields                                                            |
+----------+------+----------+---------------------------------------------------------------------------------------------------------------+
| relation | str  | optional | If field type is foreign key or many to many relationship, this is set to                                     |
|          |      |          | the name of the data model referenced by the field                                                            |
+----------+------+----------+---------------------------------------------------------------------------------------------------------------+
| color    | str  | optional | Color type of the field.  Can be: key, value, dynamic,                                             |
|          |      |          | or relation                                                                                                   |
|          |      |          | “key” is automatically applied on model identifier fields                                                     |
|          |      |          | “dynamic” is automatically applied on dynamic field values                                                    |
|          |      |          | “relation” is automatically applied to model relationships                                                    |
+----------+------+----------+---------------------------------------------------------------------------------------------------------------+
| options  | dict | optional | Django field options, depending on field class specified.                                                     |
|          |      |          | See more information here: https://docs.djangoproject.com/en/5.2/ref/models/fields/#field-attribute-reference |
+----------+------+----------+---------------------------------------------------------------------------------------------------------------+


2.5.   Meta  (embedded)
=======================

+--------+
| {name} |
+--------+

+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| Spec                | Type              | Value    | Description                                                                              |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| verbose_name        | str               | optional | Singular display name of model                                                           |
|                     |                   |          | Autogenerated if not specified                                                           |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| verbose_name_plural | str               | optional | Plural display name of model                                                             |
|                     |                   |          | Autogenerated if not specified                                                           |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| unique_together     | list <str>        | optional | Combinations of field names that are unique                                              |
|                     | list <list <str>> |          | together in the database                                                                 |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| scope               | str               | optional | Field names that are immediate parents of model                                          |
|                     | list <str>        |          | Enables scoped access in commands and orchestration                                      |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| relation            | str               | optional | Field names that are parents of model but not considered                                 |
|                     |                   |          | scoped access fields.  Used to generate command options                                  |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| dynamic_fields      | str               | optional | Model field names that are dynamically calculated and not                                |
|                     | list <str>        |          | stored in the database                                                                   |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| ordering            | str               | optional | Default ordering fields.  Prefixing with a “~”                                           |
|                     | list <str>        |          | reverses the ordering of the field                                                       |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| provider_name       | str               | optional | Provider name reference in the format:                                                   |
|                     |                   |          | <plugin name>[:<subtype>]                                                                |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+
| command_base        | str               | optional | Base command name if different from the                                                  |
|                     |                   |          | model specification name                                                                 |
+---------------------+-------------------+----------+------------------------------------------------------------------------------------------+


2.6.  Core  Data Models
=======================

.. image:: ./kix.6og5zbx0ctt.png





3. Zimagi   Command Specifications

************************************

.. image:: ./kix.fws49h5c5sbl.png






3.1.   Command Mixin  (key:  command_mixins )
=============================================

+--------+
| {name} |
+--------+

+------------+------------+----------+---------------------------------------------------------------+
| Spec       | Type       | Value    | Description                                                   |
+------------+------------+----------+---------------------------------------------------------------+
| class      | str        | optional | Allows explicit specification of generated class names        |
|            |            |          | (Pascal Case class name)                                      |
+------------+------------+----------+---------------------------------------------------------------+
| base       | str        | optional | Base mixin class from available mixins or default base mixin  |
|            |            |          | class if not specified (as spec name)                         |
+------------+------------+----------+---------------------------------------------------------------+
| mixins     | str        | optional | Parent command mixin classes (as spec names)                  |
|            | list <str> |          |                                                               |
+------------+------------+----------+---------------------------------------------------------------+
| meta       | dict       | optional | Autogeneration schema for command attributes and              |
|            |            |          | methods.  See “Meta” section below                            |
+------------+------------+----------+---------------------------------------------------------------+
| parameters | dict       | optional | Collection of named parameter objects.                        |
|            |            |          | See “Parameter” section below                                 |
+------------+------------+----------+---------------------------------------------------------------+


3.2.   Base Command   (key:  command_base )
===========================================

+--------+
| {name} |
+--------+

+---------------------+------------+----------+----------------------------------------------------------+
| Spec                | Type       | Value    | Description                                              |
+---------------------+------------+----------+----------------------------------------------------------+
| class               | str        | optional | Allows explicit specification of generated class names   |
|                     |            |          | (Pascal Case class name)                                 |
+---------------------+------------+----------+----------------------------------------------------------+
| base                | str        | optional | Base mixin class from available mixins or default base   |
|                     |            |          | mixin class if not specified (as spec name)              |
+---------------------+------------+----------+----------------------------------------------------------+
| mixins              | str        | optional | Parent command mixin classes (as spec names)             |
|                     | list <str> |          |                                                          |
+---------------------+------------+----------+----------------------------------------------------------+
| parameters          | dict       | optional | Collection of named parameter objects.                   |
|                     |            |          | See “Parameter” section below                            |
+---------------------+------------+----------+----------------------------------------------------------+
| parse_passthrough   | bool       | optional | Whether or not to pass all parameters given to           |
|                     |            |          | Command straight through in an “args” option             |
|                     |            |          | bypassing all preprocessing                              |
+---------------------+------------+----------+----------------------------------------------------------+
| parse               | str        | optional | Parameters to parse during initialization for the        |
|                     | list <str> |          | command                                                  |
|                     | dict       |          | If string is given, a single parameter with no           |
|                     |            |          | options is parsed                                        |
|                     |            |          | If a list is given, the all parameters are parsed        |
|                     |            |          | with no options                                          |
|                     |            |          | If a dictionary is given, the parameter names            |
|                     |            |          | are keyed with options, which can be nothing,            |
|                     |            |          | a single argument, a list of arguments, or a             |
|                     |            |          | dictionary or keyword arguments                          |
+---------------------+------------+----------+----------------------------------------------------------+
| interpolate_options | bool       | optional | Whether or not to interpolate command options with       |
|                     |            |          | available parsers when executing command                 |
|                     |            |          | Current parsers:                                         |
|                     |            |          | Configurations                                           |
|                     |            |          | State variables                                          |
|                     |            |          | Reference queries                                        |
|                     |            |          | Variable length tokens                                   |
+---------------------+------------+----------+----------------------------------------------------------+
| priority            | int        | optional | Priority in command listing and execution. Lower         |
|                     |            |          | numbers are higher priority                              |
+---------------------+------------+----------+----------------------------------------------------------+
| api_enabled         | bool       | optional | Whether or not to expose this command through the        |
|                     |            |          | streaming API                                            |
+---------------------+------------+----------+----------------------------------------------------------+
| groups_allowed      | str        | optional | User group access.  Users must be a member of the        |
|                     | list <str> |          | specified groups to execute commands                     |
|                     |            |          | If set to “false”, access check is disabled.             |
|                     |            |          | See “task” command for example                           |
|                     |            |          | If empty list is given only admin group can              |
|                     |            |          | access                                                   |
+---------------------+------------+----------+----------------------------------------------------------+
| confirm             | bool       | optional | Whether or not to display a confirmation prompt when     |
|                     |            |          | executing                                                |
+---------------------+------------+----------+----------------------------------------------------------+
| display_header      | bool       | optional | Whether or not to display the standard command output    |
|                     |            |          | header message before command output                     |
+---------------------+------------+----------+----------------------------------------------------------+


3.3.   Command   (key:  command[:{parent}:...] )
================================================

+--------+
| {name} |
+--------+

+---------------------+------------+----------+----------------------------------------------------------+
| Spec                | Type       | Value    | Description                                              |
+---------------------+------------+----------+----------------------------------------------------------+
| class               | str        | optional | Allows explicit specification of generated class names   |
|                     |            |          | (Pascal Case class name)                                 |
+---------------------+------------+----------+----------------------------------------------------------+
| base                | str        | optional | Base mixin class from available mixins or default base   |
|                     |            |          | mixin class if not specified (as spec name)              |
+---------------------+------------+----------+----------------------------------------------------------+
| mixins              | str        | optional | Parent command mixin classes (as spec names)             |
|                     | list <str> |          |                                                          |
+---------------------+------------+----------+----------------------------------------------------------+
| resource            | str        | optional | Data model specification name ro generate a resource     |
|                     |            |          | command set at current location in command tree          |
+---------------------+------------+----------+----------------------------------------------------------+
| parameters          | dict       | optional | Collection of named parameter objects.                   |
|                     |            |          | See “Parameter” section below                            |
+---------------------+------------+----------+----------------------------------------------------------+
| parse_passthrough   | bool       | optional | Whether or not to pass all parameters given to           |
|                     |            |          | Command straight through in an “args” option             |
|                     |            |          | bypassing all preprocessing                              |
+---------------------+------------+----------+----------------------------------------------------------+
| parse               | str        | optional | Parameters to parse during initialization for the        |
|                     | list <str> |          | command                                                  |
|                     | dict       |          | If string is given, a single parameter with no           |
|                     |            |          | options is parsed                                        |
|                     |            |          | If a list is given, the all parameters are parsed        |
|                     |            |          | with no options                                          |
|                     |            |          | If a dictionary is given, the parameter names            |
|                     |            |          | are keyed with options, which can be nothing,            |
|                     |            |          | a single argument, a list of arguments, or a             |
|                     |            |          | dictionary or keyword arguments                          |
+---------------------+------------+----------+----------------------------------------------------------+
| interpolate_options | bool       | optional | Whether or not to interpolate command options with       |
|                     |            |          | available parsers when executing command                 |
|                     |            |          | Current parsers:                                         |
|                     |            |          | Configurations                                           |
|                     |            |          | State variables                                          |
|                     |            |          | Reference queries                                        |
|                     |            |          | Variable length tokens                                   |
+---------------------+------------+----------+----------------------------------------------------------+
| priority            | int        | optional | Priority in command listing and execution. Lower         |
|                     |            |          | numbers are higher priority                              |
+---------------------+------------+----------+----------------------------------------------------------+
| api_enabled         | bool       | optional | Whether or not to expose this command through the        |
|                     |            |          | streaming API                                            |
+---------------------+------------+----------+----------------------------------------------------------+
| groups_allowed      | str        | optional | User group access.  Users must be a member of the        |
|                     | list <str> |          | specified groups to execute commands                     |
|                     |            |          | If set to “false”, access check is disabled.             |
|                     |            |          | See “task” command for example                           |
|                     |            |          | If empty list is given only admin group can              |
|                     |            |          | access                                                   |
+---------------------+------------+----------+----------------------------------------------------------+
| confirm             | bool       | optional | Whether or not to display a confirmation prompt when     |
|                     |            |          | executing                                                |
+---------------------+------------+----------+----------------------------------------------------------+
| display_header      | bool       | optional | Whether or not to display the standard command output    |
|                     |            |          | header message before command output                     |
+---------------------+------------+----------+----------------------------------------------------------+


3.4.   Meta  (embedded)
=======================

+--------+
| {name} |
+--------+

+-----------------+------+----------+------------------------------------------------------------------------+
| Spec            | Type | Value    | Description                                                            |
+-----------------+------+----------+------------------------------------------------------------------------+
| data            | str  | optional | Specification name for referenced data model, used to autogenerate     |
|                 |      |          | attributes and methods on the command for working with the data model  |
|                 |      |          | If “null” is given, then no data model related autogeneration          |
+-----------------+------+----------+------------------------------------------------------------------------+
| provider        | bool | optional | Whether or not to generate provider related attributes and methods for |
|                 |      |          | this data model on the command                                         |
+-----------------+------+----------+------------------------------------------------------------------------+
| priority        | int  | optional | Priority in command model facade initialization. Lower numbers are     |
|                 |      |          | higher priority                                                        |
+-----------------+------+----------+------------------------------------------------------------------------+
| name_default    | str  | optional | Default data model name command attribute used when name is not        |
|                 |      |          | explicitly specified                                                   |
+-----------------+------+----------+------------------------------------------------------------------------+
| default         | str  | optional | Plugin provider default when not explicitly specified                  |
+-----------------+------+----------+------------------------------------------------------------------------+


3.5.   Parameter  (embedded)
============================

+--------+
| {name} |
+--------+

+------------------+------------+----------+-------------------------------------------------------------------------+
| Spec             | Type       | Value    | Description                                                             |
+------------------+------------+----------+-------------------------------------------------------------------------+
| parser           | str        | optional | Parameter parser.  Can be: flag, variable, variables, or fields         |
|                  |            |          | (key value pairs)                                                       |
+------------------+------------+----------+-------------------------------------------------------------------------+
| type             | str        | optional | Internal data type.  Can be: str, int, float, or bool                   |
+------------------+------------+----------+-------------------------------------------------------------------------+
| optional         | str        | optional | Whether or not this parameter is optional to the command.               |
|                  | bool       |          | If “true”, then parameter is added as an optional argument              |
|                  |            |          | If “false”, then parameter is required as an argument                   |
|                  |            |          | If a dashed identifier, parameter is added as optional                  |
+------------------+------------+----------+-------------------------------------------------------------------------+
| choices          | list <str> | optional | Available choices for the parameter                                     |
|                  | dict       |          | If list given then elements are both values and labels                  |
|                  |            |          | If dictionary given, keys are values and values are labels              |
+------------------+------------+----------+-------------------------------------------------------------------------+
| default          | *          | optional | Default parameter value if not specified                                |
+------------------+------------+----------+-------------------------------------------------------------------------+
| default_callback | str        | optional | Command method callback to execute instead of specifying default.       |
|                  |            |          | Allows for dynamic default variables depending on state                 |
+------------------+------------+----------+-------------------------------------------------------------------------+
| help             | str        | optional | Parameter help message.  Internally combined with default to get        |
|                  |            |          | final rendered form                                                     |
+------------------+------------+----------+-------------------------------------------------------------------------+
| value_label      | str        | optional | Value label for use with variable and variables parsers in help         |
|                  |            |          | information                                                             |
+------------------+------------+----------+-------------------------------------------------------------------------+
| help_callback    | str        | optional | Command method callback to generate help string                         |
|                  |            |          | This is only valid on the “fields” parameter parser                     |
+------------------+------------+----------+-------------------------------------------------------------------------+
| callback_args    | list <*>   | optional | Argument list to pass to the parameter help callback if specified       |
+------------------+------------+----------+-------------------------------------------------------------------------+
| callback_options | dict       | optional | Keyword parameters to pass to the parameter help callback if specified  |
+------------------+------------+----------+-------------------------------------------------------------------------+
| data             | str        | optional | Data specification name for related model to generate provider related  |
|                  |            |          | Help information for “fields” parameter parser.                         |
|                  |            |          | This should pretty much never need to be used                           |
+------------------+------------+----------+-------------------------------------------------------------------------+


3.6.  Core  Commands
====================

.. image:: ./kix.vsnbgztpsc6x.png



4. Provider Mixin

***********************************

.. image:: ./kix.tpls2u9qapt1.png








4.1.   Provider Mixin  (key:  plugin_mixins )
=============================================

+--------+
| {name} |
+--------+

+-------------+------------+----------+---------------------------------------------------------------+
| Spec        | Type       | Value    | Description                                                   |
+-------------+------------+----------+---------------------------------------------------------------+
| class       | str        | optional | Allows explicit specification of generated class names        |
|             |            |          | (Pascal Case class name)                                      |
+-------------+------------+----------+---------------------------------------------------------------+
| base        | str        | optional | Base mixin class from available mixins or default base mixin  |
|             |            |          | class if not specified (as spec name)                         |
+-------------+------------+----------+---------------------------------------------------------------+
| mixins      | str        | optional | Parent provider mixin classes (as spec names)                 |
|             | list <str> |          |                                                               |
+-------------+------------+----------+---------------------------------------------------------------+
| requirement | dict       | optional | Collection of required named configuration objects.           |
|             |            |          | See “Configuration” section below                             |
+-------------+------------+----------+---------------------------------------------------------------+
| option      | dict       | optional | Collection of optional named configuration objects.           |
|             |            |          | See “Configuration” section below                             |
+-------------+------------+----------+---------------------------------------------------------------+
| interface   | dict       | optional | Collection of methods to be implemented by providers of       |
|             |            |          | a base plugin.  See “Method” section below                    |
+-------------+------------+----------+---------------------------------------------------------------+

*IMPORTANT:* **Base mixins can add related specifications**

4.2.   Base Provider  (key:  plugin )
=====================================

+--------+
| {name} |
+--------+

+-------------+------------+----------+---------------------------------------------------------+
| Spec        | Type       | Value    | Description                                             |
+-------------+------------+----------+---------------------------------------------------------+
| base        | str        | optional | Base provider class from available provider or default  |
|             |            |          | base provider class if not specified (as spec name)     |
+-------------+------------+----------+---------------------------------------------------------+
| mixins      | str        | optional | Parent provider mixin classes (as spec names)           |
|             | list <str> |          |                                                         |
+-------------+------------+----------+---------------------------------------------------------+
| requirement | dict       | optional | Collection of required named configuration objects.     |
|             |            |          | See “Configuration” section below                       |
+-------------+------------+----------+---------------------------------------------------------+
| option      | dict       | optional | Collection of optional named configuration objects.     |
|             |            |          | See “Configuration” section below                       |
+-------------+------------+----------+---------------------------------------------------------+
| interface   | dict       | optional | Collection of methods to be implemented by providers of |
|             |            |          | a base plugin.  See “Method” section below              |
+-------------+------------+----------+---------------------------------------------------------+
| data        | str        | optional | Data model specification name when deriving from the    |
|             |            |          | base “data” plugin provider                             |
+-------------+------------+----------+---------------------------------------------------------+
| store_lock  | str        | optional | Database mutex name to use when storing system data.    |
|             |            |          | This prevents multiple saves from happening at the same |
|             |            |          | time across the system                                  |
+-------------+------------+----------+---------------------------------------------------------+
| subtypes    | dict       | optional | Collection of related base provider implementations     |
|             |            |          | See “Base Provider” section (this one right here!)      |
|             |            |          | This specification is only applicable when base         |
|             |            |          | plugin is “meta”                                        |
+-------------+------------+----------+---------------------------------------------------------+
| providers   | dict       | optional | Collection of provider implementations for the plugin.  |
|             |            |          | See “Provider” section below                            |
|             |            |          | If base is “meta”, then the primary key is the          |
|             |            |          | name of the provider with secondary keys for            |
|             |            |          | all defined subtypes under provider                     |
|             |            |          | Provider name may have a value of “null”, in            |
|             |            |          | which casea generic provider is generated               |
+-------------+------------+----------+---------------------------------------------------------+

*IMPORTANT:* **Base providers and mixins can add related specifications**


4.3.   Provider  (embedded)
===========================

+--------+---------------------------------------------------------------------------+
| {name} | Value can be “**null**”, in which the method is generated in generic form |
+--------+---------------------------------------------------------------------------+

+-------------+------------+----------+---------------------------------------------------------+
| Spec        | Type       | Value    | Description                                             |
+-------------+------------+----------+---------------------------------------------------------+
| base        | str        | optional | Base provider class from available provider or default  |
|             |            |          | base provider class if not specified (as spec name)     |
+-------------+------------+----------+---------------------------------------------------------+
| mixins      | str        | optional | Parent provider mixin classes (as spec names)           |
|             | list <str> |          |                                                         |
+-------------+------------+----------+---------------------------------------------------------+
| requirement | dict       | optional | Collection of required named configuration objects.     |
|             |            |          | See “Configuration” section below                       |
+-------------+------------+----------+---------------------------------------------------------+
| option      | dict       | optional | Collection of optional named configuration objects.     |
|             |            |          | See “Configuration” section below                       |
+-------------+------------+----------+---------------------------------------------------------+

*IMPORTANT:* **Base providers and mixins can add related specifications**


4.4.   Configuration  (embedded)
================================

+--------+
| {name} |
+--------+

+-------------+------+----------+--------------------------------------------------------------------------+
| Spec        | Type | Value    | Description                                                              |
+-------------+------+----------+--------------------------------------------------------------------------+
| type        | str  | optional | Configuration data type.  Can be: str, int, float, bool, list, or dict   |
+-------------+------+----------+--------------------------------------------------------------------------+
| default     | *    | optional | Default configuration value if not specified                             |
+-------------+------+----------+--------------------------------------------------------------------------+
| help        | str  | optional | Help text for plugin provider configuration                              |
+-------------+------+----------+--------------------------------------------------------------------------+
| config_name | str  | optional | Configuration name of a default value to use when no value is specified  |
+-------------+------+----------+--------------------------------------------------------------------------+


4.5.   Method  (embedded)
=========================

+--------+---------------------------------------------------------------------------+
| {name} | Value can be “**null**”, in which the method is generated in generic form |
+--------+---------------------------------------------------------------------------+

+---------+------+----------+------------------------------------------------------------------------------------------------------------------------------------------------+
| Spec    | Type | Value    | Description                                                                                                                                    |
+---------+------+----------+------------------------------------------------------------------------------------------------------------------------------------------------+
| params  | dict | optional | Method parameters.  Dictionary keys are the parameter names and the values are the data type, which can be: str, int, float, bool, list, dict, |
|         |      |          | or other referenced classes                                                                                                                    |
|         |      |          | This specification is not currently used, but there are plans to                                                                               |
|         |      |          | use with provider validation                                                                                                                   |
+---------+------+----------+------------------------------------------------------------------------------------------------------------------------------------------------+
| returns | *    | optional | Data type or referenced class returned from the provider method                                                                                |
|         |      |          | This specification is not currently used, but there are plans to                                                                               |
|         |      |          | use with provider validation                                                                                                                   |
+---------+------+----------+------------------------------------------------------------------------------------------------------------------------------------------------+


4.6.  Core  Plugins  and  Providers
===================================

.. image:: ./kix.yk9yetlaxfoj.png
