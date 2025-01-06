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

The new run of `zimagi env get` should show that the module has been added
to Zimagi.

Adjust the GitHub URL as needed to point to your repository.  Notice that at
this point we are only using the ``https://`` URL rather than the ``git@`` URL
since the Vagrant shell does not have SSH credentials configured.  This is not
a problem, and we will enhance the connection just below.

Within your local terminal, you can now see where the module has been cloned::

  (zimagi)$ cd lib/default/modules/
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

Whenever you have created new functionality you want to integrate into Zimagi,
you should run the following within the Zimagi Vagrant shell::

  (vagrant) # Pull changes from GitHub:
  (vagrant) zimagi module save noaa-stations
  (vagrant) zimagi makemigrations

From this point forward, you can (and probably should) work within the module
clone that is located at ``$ZDIR/lib/default/modules/noaa-stations`` (or whatever
leaf path corresponds to the name you gave to your module.  Notice that this
directory matches the ``name`` key defined inside the module's ``zimagi.yml``
file rather than the repository name itself.

In this example, the repository is named ``module-noaa-stations`` while the
module name is ``noaa-stations``; but either name can be whatever you like.
