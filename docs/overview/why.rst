##############################
What Need Does Zimagi Fulfill?
##############################

Unify data sources
------------------

In a Zimagi module, data can be obtained from many different data sources,
potentially from many different providers and using many different formats.
In general, any kind of data format can be read with Python code, and placed
into a unified data model.  Zimagi provides components for processing many
common data formats, but with a small amount of developer effort, custom
readers can by created to read any formats or sources, including those
requiring providing credentials for access to data.

Once obtained, all acquired data lives in a local database, and can be updated
flexibly and as needed.


Normalization of relations among data entities
----------------------------------------------

The **data model** of a particular module defines how all the different entities
are connected to each other.  This concept will be generally familiar to users
of relational database management systems (RDBMSs), but Zimagi expresses
relationships and data attributes using a higher-level configuration syntax
than that used in database administration and management (behind the scenes,
the data store is indeed an RDBMS).


For example, suppose you wished to create a service for realtors that had
information on houses and the towns and regions they are in.  Some of the data
you wish to provide might be tax records provided by individual U.S. states,
perhaps only obtainable using an interactive API that requires login
credentials.  Some of the data you with to provide might concern the weather in
those regions, which can be obtained as HDF5 files provided by agencies like
NOAA.  Yet other demographic data might come from the U.S. Census Bureau, and
require downloading CSV files for information.  Yet other information might
come from the realty company you work for that predicts housing price trends,
and should only be accessible to a limited collection of users (e.g. to agents
at your company but not to the potential buyers).

As long as you can identify a commonality by which to connect these entities
(e.g. which city or town has the various attributes), Zimagi can provide a
unified and queryable view into all the aspects of the data.  Optionally,
different user types might be able to view different parts of the data).


Flexible and universal service hosting
--------------------------------------

Zimagi and modules running within it can run locally, or run on cloud services
with no change to the base platform or modules used.  Running Zimagi on a local
or in-house server is as simple as launching a Vagrant instance.  However,
hosting on services like AWS, Google Cloud Platform, or Azure, are also single
commands to install and launch all components needed.  Both locally and within
the cloud, configuration of required resources is simple and flexbile.  For
example, if a particular module requires many processor cores, a large amount
of memory, larger hard disk space, or other resources, this can easily be
declared in a configuration file, and the relevant resources will be
provisioned when the Zimagi instance is created.


Both schedulable and user launchable actions
--------------------------------------------

Commands within Zimagi can be run either using command-line interfaces or via
RESTful JSON requests over HTTPS.  Moreover, however, commands can also be
scheduled to run on a recurring basis in a highly configurable way.

Scheduled commands **may** consist of regularly refreshed data acquisition
steps, but they may also perform computational, or any arbitrary, actions.  For
example, if you need to retrain a machine learning model based on new data
becoming available, this can be scheduled as a background action.  A task
**can** be triggered by a data acquisition step, but may also be scheduled on a
completely independent schedule.


Types of Zimagi users
---------------------

Very broadly, the users of Zimagi consists of module **users** and module
**developers**.  The former group need not understand even the configuration
files used within a module, but only need to learn either a simple command-line
interface, or can be provided with friendly web-based front-ends that
internally talk with the Zimagi API.  In some cases, a Zimagi interface may
consist solely of automatically generated filtered and unified data that is
simply updated in local storage for the user.  For this last class of module
user, all they need to see is that a current version of e.g. a spreadsheet file
is always available to them.

At the other end, are module **developers**.  These users will need to have
some conception of data sources, data models, and data cleanliness.  However,
for these users, most of the creation steps for a module consist of definining
the data models in configuration files, with only small amounts of Python code
development needed (possibly passed on to dedicated coders who only need to
provide isolated components).


Zimagi versus Luigi, Airflow, and Jenkins
-----------------------------------------

The open source workflow tools Luigi and Airflow provide capabilities similar
to what Zimagi does.  All of these are able to automate scheduled tasks and the
dependencies among them.  Zimagi stands out from those in two principal ways:

* Zimagi is forcused on data models that represent acquired data and present it
  with a uniform query interface.  While Luigi and Airflow are both capable of
  containing such models, the actual configuration and development of those
  models is necessarily new and non-standardized for each project.  In
  contrast, task dependencies can certainly be programmed in Zimagi, but it is
  symmetrically individual to a project/module rather than part of the
  framework per se.

* Zimagi contains tools to automatically and easily "stand up" an instance.
  Luigi and Airflow are not necessarily **difficult** to install and launch,
  but they do not handle their own provisioning as Zimagi does.

Jenkins is another popular open source tool for automation of sheduled or
launchable actions.  Like Luigi and Airflow, it provides APIs for programming
it, but not "low-code" as a goal per se.  In concept, Jenkens can be used for
any kind of automation (much like Zimagi), but it is especially focused on
software development projects rather than data-oriented projects.

For those who are familiar with Jenkins (or similar tools like CircleCI or
Travis CI), thinking of Zimagi as "Jenkins for data" is not too far wrong.


A Tabular Comparison of what Zimagi is and is not
-------------------------------------------------
