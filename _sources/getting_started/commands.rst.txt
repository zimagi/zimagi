==========================
The Command Line Interface
==========================

The CLI is one of the primary ways you can interact with Zimagi, with
the other method of interaction being the APIs. You will use the CLI to
establish your hosts and desired users. You can also use the CLI to
control your environments, import and manipulate data, and schedule
commands. You’ll provide the CLI with your chosen command any any
accompanying argument.

When a Zimagi environment is first started, commands are dynamically
generated based on specs. User commands and host commands are always run
locally, while all other commands are exposed to API. While you can use
Zimagi as either a CLI tool or an API tool, this section will focus on
using the CLI, which is the primary way you'll interact with Zimagi at
first.

Let’s take a look at the most common and important commands that you
need to know about to begin using Zimagi.

Config Commands
---------------

The config command is responsible for managing all the configurations
for the current active environment.

``list``

Returns information for all currently defined configurations in the
active environment. Data is returned as a series of key-value pairs.
Included in the return is the ``Name`` of the config, the
``Value Type``, the currently assigned ``Value``, and the ``Groups`` the
configuration belongs to.

``get``

Returns key-value pairs for a single provided configuration. Required
arguments: ``config _name``- the name of a single configuration.

``save``

Assigns provided value to specified configuration. Used for both
creating and updating configurations. Required arguments:
``config_name`` - name of the configuration to save, ``config_value`` -
the value for the specified configuration.

``remove``

Removes an existing environment configuration. Required arguments:
``config_name`` - name of the configuration to save.

``clear``

Clears all existing configurations in the current environment.

Environment Commands
--------------------

Environments commands are used to control and activate environments.

``set``

Sets the currently active environment. Required arguments:
``environment_name`` - The name of a valid Zimagi environment.

``get``

Gets the currently active environment, returning details about the
environment such as the environment’s status, base image, runtime image,
attached hosts, and included modules.

``save``

Assigns and saves attributes of the current environment. Required
arguments: ``field=Value``, where ``field``\ s are one of the following:
``repo``, ``base_image``, ``runtime_image``, and ``Value`` is a string.

``remove``

Removes the current environment from the Zimagi installation.

Database Commands
-----------------

Database commands lets the user install databases on clients and
servers, as well as start and stop database instances.

``pull``

Downloads and installs a database from a remote environment onto the
client machine. Required arguments: ``db_packages`` - the names of one
or more database packages.

``push``

Transfers a copy of a database from its local environment to a server,
installing the database on the server. Required arguments:
``db_packages`` - the names of one or more database packages.

``start``

Starts up a PostGreSQL service on the host machine, enabling the
database service to be used for local connections.

``stop``

Stops the running containerized PostGreSQL service on the host machine.
Used to reset a database connection.

Schedule Commands
-----------------

Schedule commands let the user set commands to be carried out by
workers, as well as remove commands and see all existing commands.

``list``

Lists commands schedules defined in the current environment. Arguments:
``field`` ``subfield`` -- a list of fields and subfields to display.

``get``

Returns the command schedule for the active environment. Required
arguments: ``scheduled_task_name`` - the name of the scheduled tasks.

``remove``

Removes an existing command schedule from the active environment.
Required arguments: ``scheduled_task_name`` - the name of the scheduled
task to be removed.

``clear``

Clears all of the existing command schedules in the environment.

Data Import Commands
--------------------

``import``

Makes all data objects defined by provided specifications available.
Required arguments: ``import_names`` - The names of one or more
specifications.

**Host Commands**

Host commands let interact with hosts tied to the current environment.
Using host commands, you can find active hosts, modify hosts, and remove
hosts.

``list``

Returns a list of all hosts mapped to the current local environment.
Arguments: One or more search queries.\ ``get`` Get information about a
specific host in the current environment. Arguments: ``host_name`` - The
name of a host in the environment. If none is provided, defaults to
``@host_name|default.``

``save```

Add and save a new environment host. Arguments: ``field=Value`` -
Key-value pairs specifying host configurations. Required: Key-value pair
for ``host=URL``. Optional Key-value pairs: ``port``, ``user``,
``token``.

``remove``

Remove a host from the current environment.

``clear``

Remove all hosts from the current environment. Arguments: one or more
search queries.

User
----

``rotate``

Rotates credentials for the active user, activates user for remote
environment. Requires remote environment be specified. Arguments:
``user_name`` - Name of user to rotate.

``list``

Returns list of systems users. Arguments: One or more search queries.

``get``

Returns information for a given user. Arguments: ``user_name`` - The
name of a user to retrieve information for.

``save``

Add/save a system user and user attributes. Arguments: ``user_name`` -
Key-value pair containing the name of a user to add or update. Optional
Key-value pairs: ``email``, ``first_name``, ``last_name``,
``is_active``.

``remove``

Remove an existing user from the system. Arguments: ``user_name`` - The
name of a user to remove.

``clear``

Clears all users from the system, resetting the system to its default
state. Arguments: One or more search queries.
