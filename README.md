<p align="center">
  <img width="460" height="150" src="docs/_static/images/zimagi-logo.png">
</p>
<hr/>

| Branch   | CircleCI Status                                                                                                               |
| :------- | :---------------------------------------------------------------------------------------------------------------------------- |
| **Main** | [![CircleCI](https://circleci.com/gh/zimagi/zimagi/tree/main.svg?style=svg)](https://circleci.com/gh/zimagi/zimagi/tree/main) |

<br/>

# Zimagi overview

**Open Source Distributed Data Processing Platform**

Zimagi is a fast and powerful open source distributed data processing platform that empowers developers to implement powerful production-ready data pipelines with less code.

<br/>

## The Goal

Make it fast and easy to create powerful, scalable production ready APIs and distributed data processing services:

- Ready for our data
- In minutes or hours, not weeks, months, or years
- At a fraction of the cost of traditional development services or proprietary API platforms
- That are completely extensible and customizable, built on popular open source software

In short; **Go from concept and architecture to production data services in no time with little to no code**

<br/>

## Major Features

- Modular database driven API and processing platform built on Python, Django, Celery, and other popular open source technologies
- Auto-generated code base from architectural specifications _(production ready data, imports, and APIs with little or no code required)_
- Hosted API and / or CLI _(no server required to use or get started)_
- Micro-service APIs out of the box:
  - Secure and flexible streaming RPC command API for data updates and system management
  - Fast and secure OpenAPI compatible REST API for searchable data access
- Pluggable architecture for extreme extensibility with version controlled modules
- Powerful, layered data centric orchestration language with query capabilities for advanced data processing workflows across clusters of machines
- Multi user role based management and access with command logging and auditing
- Integrated real-time, queued, and scheduled command execution
- Configurable user email notifications on command execution and failure

<br/>

# Architecture

## Services

The Zimagi platform is composed of four Dockerized micro-services that each collaboratively perform vital services to ingesting, processing, and distributing data through the system.

<p align="center">
  <img width="700" src="docs/_static/images/zimagi-flow.png">
</p>

These include:

### Command API

The command API service provides a streaming RPC "remote operating system" for performing actions through the platform. Commands each have their own endpoints in a command tree and accepted POSTed parameters and return a series of JSON messages back to the client as they are executing.

It is possible to create commands that terminate when the client breaks the connection or continue processing until done regardless if the user is still connected. It is also possible to push command executions to a backend queue for worker processing, or schedule them to run at intervals or a certain date and time.

_Command API services can easily scale across cluster nodes with demand_

### Data API

The data API service provides an OpenAPI compatible REST data access system that allows for easy querying and downloading of data in JSON form.

The data API can currently return lists of data objects that can be searched across nested relationships with special GET parameters and it can return single data objects specified with an instance key.

_Data API services can easily scale across cluster nodes with demand_

### Scheduler

The scheduler service provides the ability to schedule commands that are queued and workers then run on a particular date and time or during regular intervals.

There are three modes of scheduling in the system:

- Run a command at a specific date and time _(ex; **Dec 25th, 2020**)_
- Run a command at an interval _(ex; **every hour**)_
- Run a command according to a crontab spec _(format; **Month Hour DayOfMonth MonthOfYear DayOfWeek**)_

_Scheduler services can run across cluster nodes for high availability, but only a single scheduler is active at a given time_

### Worker

The worker service provides a queued execution ability of commands in the background that are logged in the system, just like commands executed in real-time.

Workers pull tasks from a central Redis queue and process in a first come basis until all command jobs are completed. This gives us the ability to easily distribute data processing processes across a small or large number of processors, giving us an easily parallel execution environment that can reduce the time to complete larger data driven tasks.

_Worker services can easily scale across cluster nodes with demand_

### Background Data Services

The Zimagi platform requires two data stored running in the background to operate. These allow Zimagi to store and access persistent data across cluster nodes and store and process parallel jobs

#### Relational Database

A relational database is required to define, store, and access data models. So far **SQLLite3**, **PostgreSQL**, and **MySQL variants** are supported.

#### Job Queue

A Redis queue is required to store and retrieve background commands to execute by worker nodes. Both the **command API** and the **scheduler** add jobs to this queue.

<br/>

## Framework

<p align="center">
  <img width="700" src="docs/_static/images/zimagi-components.png">
</p>

The Zimagi core framework is built on the Django web framework in Python.

**Python** was chosen as the language of the platform because it is:

- Popular with people first learning programming and used heavily in educational courses from Universities and other educational outlets

- The most popular data science language, which contains many statistical processing and AI libraries used in a myriad of research endeavors

- A very popular language used in the management of cloud and on-premis infrastructure systems

- Popular as a backend API language for headless application development

**Django** was chosen as a foundational web framework because:

- It is the most powerful, popular, and heavily developed web framework for Python

- Is has a very consistent and easy to learn architecture that can be applied across projects, so work on Zimagi can help with learning skills that apply to other web projects

- It focuses on security and performance

- It allows us the freedom to evolve the way we want _(such as with meta programming code generation based on architectural specifications)_

## Manager

At the core of Zimagi there is a management layer that stitches together all of the other components and provides an integrated access point for working with all of the subsystems.

The manager initializes the runtime on startup, loads all of the module extensions, builds the specifications as dynamic classes, and provides indexes to dynamically generated classes.

The manager can easily be accessed from any subsystem in the Zimagi platform.

### Data

All data models in the Zimagi platform are dynamically generated from specifications, and require no code to design and develop.

There are three main components to the data definition system in Zimagi:

- **Base Data Models**: These are abstract models that define certain properties that ally to all inheriting data models. Typically these are used for parent model relationships. So, for example, if Tires belong to Cars, there would be a Car base model that Tire models would extend that would have parent relationship fields. These base models can define properties like key and id field names, field definitions, and meta information related to the Django model itself.

- **Data Model Mixins**: These are mixins that contains collections of field definitions that can be applied to multiple models without having to redefine them in multiple places. They can also extend other model mixins.

- **Data Models**: These are actual data types in the Zimagi platform. They extend a base model and can include various model mixins. They define view and edit role permissions, and can also define their own field definitions, and Django model meta information.

To import data records into the Zimagi data models, we implement a specification base data import system, that consists of source, validator, and formatter plugins and providers _(introduced in subsequent section)_. This allows us to define and import our data with as little code possible, while still retaining complete freedom to extend the platform for many different data types and import sources.

All data models are automatically available through the data API with no code necessary.

### Commands

The command system is composed of a local and API based execution environment that accept a name and parameters, and returns a series of messages, which can be printed to the terminal as execution progresses.

At the core of the command processing engine is a "**command tree**", which is searched when given a command name to run. The resulting command then has an exec method that is called to start the process until completion.

There is an internal framework for parsing given parameters, executing processes, and returning results while running that abstracts away the execution environment, so the same command works both locally through the CLI and through a remote command API for remove processing across the cluster nodes.

Commands are defined both within architectural specifications _(command parameters and other meta information)_ and related Python class definitions. Like data models, commands have three levels of specification, as outlined below:

- **Base Commands**: These specify certain command meta information, such as whether or not to allow API execution and the roles allowed to execute the command

- **Command Mixins**: These provide collections of parameters that can be used by commands to tailor the execution to a particular purpose. These mixins can also define meta information for linking to defined data models in the system to provide autogenerated method accessors and setters for related fields for commands to make it easier to work with data models in commands. Command mixins can extend other command mixins.

- **Commands**: These are the actual executable commands in the system, which are classes with a parse and exec method that is searched and called by the manager indexing system in either the CLI or remote API services. Commands extend a base command and can include multiple command mixins.

### Plugins and Providers

Zimagi implements a plugin system that allows for swappable implementations of interfaces. Plugins can be varied and used for any number of purposes. They can be used to provide extended implementations of data models or implementations of different types of executable libraries. Some examples of plugins in the core system are;

- **Data plugins**: Groups, Configurations, Modules, and Users
- **Import plugins**: Sources, Validators, and Formatters
- **Other plugins**: Tasks _(configurable command configurations within modules, such as Shell commands, or Script executions)_

There are two layers to the plugin specifications:

- **Plugin Mixins**: These are references to mixin classes that take a configurable set of required and optional parameters. The required parameters define a type and a help message, while optional parameters add a default value. Plugin mixins can extend other plugin mixins.

- **Plugins**: These are interface implementations that define a method interface specification and a configurable set of required and optional parameters that apply to all providers, as well as other configurations added by the plugin implementation. Within the plugin specification, there is a set of provider specifications that contain sets of required and optional parameters for the specific provider.

### Parsers

The Zimagi platform defines a collection of parsers that take input data, perform a translation or lookup, and return the resulting data. Parsers that are currently implemented include:

- **conditional value**: String that contains a condition, true value, and a false value that are evaluated as Python expressions _(format: **?> conditional expression ? true expression : false expression**)_

- **configuration**: String that contains a configuration name to lookup and return value _(format: **@configuration_name**)_

- **state**: String that contains a state variable name to lookup and return value _(format: **$state_variable_name**)_

- **token**: String that generates a random token value that is subsequently stored as a state value, which is retrieved and return when exists _(format: **%%state_variable_name:length**)_

- **reference**: String that generates a query for returning data model field values _(format: **&data_model([scope_field=value[;..]]):key_field_name[*]:result_field**)_

### Profiles and Components

Commands in the Zimagi platform can be orchestrated into workflows called **profiles** that run sequences and / or parallel executions. Profiles can also orchestrate other profiles, to build complex workflows with modular architecture.

Profiles utilize **component** implementations that define key value pairs in the profile specification that have a priority, that determines the order of the execution within the profile.

## Modules

Nearly every aspect of the Zimagi platform can be extended through modules, which, by default, are Git version controlled projects.

Modules can contain Django settings, application runtime dependency installations, data models and import specifications, commands, plugins and providers, profiles, and profile components.

<p align="center">
  <img width="700" src="docs/_static/images/zimagi-architecture.png">
</p>

<br/>

# Getting Started
