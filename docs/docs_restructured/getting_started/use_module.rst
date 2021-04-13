====================
Using Zimagi Modules
====================

Once you understand the basics of Zimagi's structure and components, it is easy
to use a module developed by other users/developers.  The module we will clone
and install here is the one documented in ``module-noaa-stations`` (which is
discussed in *Creating a module*).  This module acquires and queries weather
station data provided by the National Oceanic and Atmospheric Administration.

Installing Zimagi
-----------------

Cloning the Zimagi Repo
^^^^^^^^^^^^^^^^^^^^^^^

To begin, we install the main Zimagi system.  We do this by cloning the `Zimagi
repo <https://github.com/zimagi/zimagi.git>`_

Using the command line, navigate to a directory you wish to use, and then run
``git clone https://github.com/zimagi/zimagi.git``.


Configuring the environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Change directory into the ``zimagi`` folder and then use Vagrant to
configure the development environment. Use ``vagrant up`` to initialize
the Vagrant instance and then use ``vagrant ssh`` to set up the
environment and ready Docker for use.

``vagrant up``

This will start the provisioning process. After provisioning has been
completed, all the necessary components will be installed, including the
core OS packages, core dependencies, development tools, Redis CLI, and
Docker. Finally, the application is built. We can then use
``vagrant ssh`` to connect to the system.

``vagrant ssh``

Now that we’ve finished installing the dependencies and tools, we can
finish configuring the development environment for use. The first thing
we want to do is make sure all modules are updated and environment
defaults set. To do this, we’ll use ``zimagi env get``.

``zimagi env get``

We can use the ``docker-compose up`` command to build the Docker
container, which will install everything using the Docker image. We’ll
use ``-d`` to daemonize the install process and let in run in the
background.

``docker-compose up -d``

You can check the status of the environment to see which containers are
currently installed and running. We want to be sure all Zimagi systems
components are running, including the entrypoints for PostGres and
Redis, zimagi-command, zimagi-scheduler, and zimagi-worker. The Docker
instance should contain the Zimagi core, which we can confirm by using
``zimagi env get`` again.

After the setup process is complete, we need to set some environment
variables to ready Zimagi for use. First, we want to set the host for
the Zimagi environment.

We use the ``host save`` command to define a host. Here we’ll set the
host to the localhost. ``zimagi host save host=localhost``

Using ``zimagi env get`` will display that a host is now assigned to the
environment. By default, the active user of a Zimagi environment is
“admin”. You can see all current users and their status (active or
non-active) by using the ``zimagi user list`` command.

``zimagi user list``

You may wish to update the admin account’s attributes by using the
``user save`` command and updating the user’s name, email, and password.
To do this, use the ``user save`` command along with the appropriate
field: ``zimagi user save admin first_name=”First”``

\`\ ``zimagi user save admin last_name=”Last"``

``zimagi user save admin email=”[testemail@address.com]"``

******************
Installing Modules
******************

Now that we have finished setting up the Zimagi environment we can install a module into the system. 

We have to do several things when installing a module:

* Add the module to the Docker instance

* Restart the Docker instance

* Set module environment settings

* Get most current data 

* Install any module requirements

To begin with, we’ll add the module to the Docker instance. We do this by using the `module add` command, followed by the URL of the module that we want to add to the environment.

`zimagi module add https://github.com/zimagi/module-noaa-stations.git`

After adding the module to the Zimagi system, we need to reset the Docker instance.

`docker-compose restart`

Now we can check to see that the module install was successful by using the `zimagi module list`command. This will show a list of all modules. 

`zimagi module list`

We want to make sure all modules share the same environment settings, and we can do this by using the `zimagi module sync` command.

`zimagi module sync`


We’ll use the `zimagi env get` command again to make sure that all modules contain the most current data from their sources and install any module requirements.

After installing and syncing the module, we can begin interacting with
the module.

We can learn which commands are available to us by using the ``help``
command, allowing us to see which commands can be used for the installed
module.

``zimagi --help``

We’ll begin by importing some data to query. We’ll use the ``import``
command to import some data, which in this instance is the data defined
by the ``test`` specification.

``zimagi import test``

**************
Making Queries
**************

Data points in this module are referred to as “observations”, as defined
in the specifications. Calling ``help`` on the module lets us see that
``observation`` is a command we can use that lets us view and manage
station observations. We can use ``observation list`` to see all
observations in the imported data.

``zimagi observation list``

If we want to see just some of the fields associated with the
observations, we can pass in those fields as arguments. We can see which
fields are available to us by typing ``--help`` after
``observation list``.

``zimagi observation list --help``

We can also filter them with any filtering criteria we want. Let’s say
we want to focus on the ``temp_attrs`` field and limit it to just the
first 24 entries. We can do this by appending the ``temp_attrs`` field
followed by ``.lt=24``.

``zimagi observation list temp_attrs.lt=24``

Now let’s say that we want to limit the returned fields to only ``date``
and ``temp``. We can accomplish this by adding the ``--fields`` argument
, followed by the fields we want to visualize.

``zimagi observation list temp_attrs.lt=24 --fields=date,temp``

We can also use search for data points that match specific values. Let's
say we want to get the records where the temperature is equal to 50.5.
All we have to do is append ``temp=50.5`` to the query.

``zimagi observation list temp_attrs.lt=24 temp=50.5``
