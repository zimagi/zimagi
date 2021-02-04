###########################
Getting Started with Zimagi
###########################

The Zimagi platform is a collaborative effort to build an API or local CLI
based distributed processing engine that focuses on low code development and
easy remote management across clusters of machines.  The primary components of
Zimagi are a data definition and management system, a modular plugin system, a
local and remote command execution environment, and an workflow orchestration
system.  Together these systems form the core for effectively managing data
processing pipelines in a variety of applications.  Always feel free to
recommend improvements in the GitHub issue queue.

We have tried to make getting started with development, and hopefully
contributing back to the Zimagi project, quick and painless. In this pursuit we
are building off of trusted open source tools and frameworks, such as Vagrant,
Docker, Django, Celery, and many others. Getting started with the platform
requires almost no setup, and management of the system is designed to be easy
through the use of virtualization, automation, and CI/CD practices. All actions
performed “should be” automated through CLI and API commands and various
scripts (located in the “scripts” directories).

This guide will help you understand the motivations behind the Zimagi effort,
how to get set up on your machine and ready for development, and primers on
working with Vagrant and Docker (particularly related to this project). We will
also cover what you need to know about environment setup in order to run this
application with other services.

.. toctree::
    :maxdepth: 3
    :caption: Getting Started

    about
    development/readme
    development/module
    environment
    hosting
    help
    contributing

