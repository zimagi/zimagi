##########################
Twelve Factor Applications
##########################

The twelve-factor application is a methodology for building software-as-a-service apps that: [1]_

  * Use **declarative** formats for setup automation, to minimize time and cost for new developers joining the project

  * Have a **clean contract** with the underlying operating system, offering maximum portability between execution environments

  * Are suitable for **deployment** on modern **cloud platforms**, obviating the need for servers and systems administration

  * **Minimize divergence** between development and production, enabling **continuous deployment** for maximum agility

  * Can **scale up** without significant changes to tooling, architecture, or development practices

Many application hosting platforms are built with the Twelve Factor Application methodology in mind, and following the principles makes it easier to develop integrated micro-services systems.  The twelve factors ultimately encourage portability and agility.  For these reasons, **MCMI is designed and built keeping the twelve factors in mind**.

======================================================
One codebase tracked in revision control, many deploys
======================================================

The **MCMI** core is hosted in a single `Git repository <https://github.com/dccs-tech/mcmi>`_ that serves as the deployment source for all builds, including this documentation site.  Currently CI/CD pipelines are handled through `CircleCI <https://circleci.com/>`_, which allows easy containerized workflows.  Deploys are made continuously to the central Docker Hub and PyPI ecosystems on merges to master branch *(latest tag)* and the creation of new tags.

**MCMI modules** are installed and synced through local or remote API command executions.  They may lock in revisions and tags or follow branches.  For now all modules must be `Git <https://git-scm.com/>`_ repositories, but in the future more sources will be supported.

===========================================
Explicitly declare and isolate dependencies
===========================================

In the **MCMI** system all core dependencies are encapsulated in the application Dockerfile, which creates a standardized base runtime.  Modules may also install dependencies, *currently through PIP requirements files or install scripts*, for flexible system level modifications.  The **MCMI** system builds and uses derivative images that contain a mixture of the core dependencies and all installed module dependencies.

Since the core system is built on a `Debian operating system <https://www.debian.org/>`_, all module operations can be tailored to one runtime, avoiding the nightmare of missing system tools or non standard OS information in installation scripts.  It is possible that new **MCMI** base images could be created built on different operating systems with supported modules.

The **MCMI** system also provides a `Vagrant <https://www.vagrantup.com/>`_ development environment that bootstraps both the CLI client and a running local server to make developing with the system easier across desktop operating systems.

===============================
Store config in the environment
===============================

All configurations in the **MCMI** system can be passed through the operating system environment.  The system is built on the `Django framework <https://www.djangoproject.com/>`_ that has a core and various module settings files that use a configuration lookup interface that ensures environment variables can override **ALL** default configurations.

Environment variables are instrumental in the deployment of the standalone and high availability API server systems.  Enironment variables are collected and combined with values written into profiles *(manifests)* and passed to remote containers on API initialization, allowing for a standardized and highly configurable system.  This also allows for easy integration with CI/CD systems.

============================================
Treat backing services as attached resources
============================================

As already mentioned in the `containerization section <./containers.html>`_ the **MCMI** system can manage external services that handle background jobs through Docker containers on the host system.  On startup these generate services definition files and are automatically restarted when needed if they have been stopped.

Since the **MCMI** architecture is based on containers we can run in many different application management systems, such as Docker Compose or Kubernetes.  In our case, since **MCMI** is meant to manage platforms like Kubernetes, we build our internal application manifests through Docker Compose, and attach any needed resources in the definition, *such as a PostgreSQL database service for the standalone server*.  Our goal is to keep our runtime dependencies as close to the container engine as possible.

It is also easy to tie external services together through environment variables as needed.

======================================
Strictly separate build and run stages
======================================

The **MCMI** system cleanly separates the build and run stages through automatic CI/CD processing on development updates.  Currently there are three build and deployment processes in action that facilitate the production deploy of the system.  All build and deploy workflows rely on environment variables passed through the CI/CD system.

Docker runtime
--------------

On deploys to master, or when tags are created, the CI/CD system builds a new image based on the core specifications in the bundled Dockerfile, and then deploys that image to `Docker Hub <https://hub.docker.com/r/mcmi/mcmi>`_ with either the tag **latest** *(for master branch)* or the **version** tag.  You can pull this runtime with **docker pull mcmi/mcmi:latest**.

The system provides two gateway interfaces; **CLI utility**, and **API bootstrap script**, *that initializes the application and runs a secure web server for the API*.  These can both serve as container entrypoints to handle both local and remote execution.

Developers pull prebuilt images based on their intended version from the central Docker Hub or their own private registry to use in their own infrastructure.

CLI application
---------------

The **MCMI** system bundles a **MCMI** utility that serves as a core CLI interface for working with the system.  It is not required to use this interface but it can be handier than rolling our own, *especially to those not familiar with Docker run command syntax*.

To install on as many target platforms as possible we create this asset as a `PyPI project <https://pypi.org/project/mcmi/>`_ **pip install mcmi**.  The setup process first builds the project on version updates, collecting the executable asset, then deploys to the central PIP registry.

Documentation site
------------------

This documentation site is also built and deployed through CI/CD to both `GitHub pages <https://dccs-tech.github.io/mcmi/>`_ and the `ReadTheDocs site <https://mcmi.readthedocs.io/en/latest/>`_.

The documentation is built with `Sphinx <http://www.sphinx-doc.org/en/master/>`_ and uses the make utility to build a HTML version of the `reStructuredText <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_ documentation markup.  You can see a version of this site in the `gh-pages branch <https://github.com/dccs-tech/mcmi/tree/gh-pages>`_ of the core **MCMI** repository.

==================================================
Execute the app as one or more stateless processes
==================================================

The **MCMI** system is a stateless CLI or running server that relies on connected database and shared file systems to store persistent data.  **ALL** runtimes are completely isolated from the host environment, and see only what is shared, or **MCMI_** prefixed environment variables that help configure operations.

Basically all execution, be it local or remote, runs through the **docker run** command to execute the two potential entrypoint scripts depending on needs.

It is possible to share local directories and resource connections, or in the case of high availability mode, connect to an external high availability database with NFS mounted file system mounts shared with the running containers.  Containerization gives us an easy way to share into isolated runtimes.

================================
Export services via port binding
================================

The **MCMI** system is fully self contained.  It comes bundled with it's own `Gunicorn <https://gunicorn.org/>`_ based multi-threaded web server that is capable of streaming over secure connections.  It is important that the application be able to encapsulate the web server for itegrated configurability through the environment and easy setup on deployment.

Since the **MCMI** runtime is built on containers it is easy to bind to ports in systems like Docker Compose or Kubernetes.  It is however internally designed to listen on **port 5123**.  When the **mcmi-api.sh** script is run it initializes the hosted application and starts the web server listening for requests on the application port.  This port can be easily mapped as needed.

===============================
Scale out via the process model
===============================

There are quite a few types of concurrency in use in the **MCMI** system due to the fact that it is designed to run other sets of infrastructure management tasks.

Application servers
-------------------

Since all application servers are stateless and built on easy to deploy standardized runtimes, it is easy to scale web servers up and down as needed to handle variable traffic conditions.  All servers execute initalization scripts that start application servers that run for as long as the underlying container is alive.

Command processes
-----------------

Many commands when executed run combinations of other commands, which often wrap system processes, *such as an Ansible or Terraform run*.  Each of these is treated as an independent process usually wrapped in an application thread.

This creates a highly concurrent toolbox that can run behind a web server in a shared environment.

Utility thread pools
--------------------

Many internal list operations are processed as thread pools, which are managed via queues with concurrency limits.  There is an easy interface for running parallel operations in isolated threads.

===========================================================
Maximize robustness with fast startup and graceful shutdown
===========================================================

Since **MCMI** is designed around gateway script execution it is easy to manage, and handles failure gracefully.  Since all application executions are containerized it is easy to remove and clear the runtimes for storage or security reasons.

Client gateway
--------------

When we execute the CLI interface we are really just running a container that acts on local data.  The startup time depends on the availability of the container images.  Admittedly this process is slower than running a host binary, but has several advantages that provide for more security and portability.

One consideration that must be mentioned is that if modules are installed then a derivative image must be constructed before execution can begin.  The system automatically knows when it needs to build this image and does so before executing commands.  This can add time to the command execution based on what modules are being installed and their dependencies.  After the image is constructed, it is used, and no other is built until the modules change again.  There are commands available to manage this process.

The client is designed to catch all exceptions, and in certain cases rollback operations if neccessary.  If the client is operating in local mode, and the user aborts, the system terminates immediately and logs the execution.  Local mode is primary designed for experimental development, not production management.

Server gateway
--------------

When the **MCMI API** is running on a host we are also running a container that bootstraps all installed module dependencies into the running image.  This adds some time to the bootstrap process depending on what modules are installed on the system and their dependencies.  Immediately after installing module dependencies it starts the application server to begin listening for incoming commands to execute.

New modules can be added to the remote API by executing module commands on the system, which will have new dependencies.  After changing any modules on a hosted **MCMI** server, the system will need to be restarted so it can rebuild the application runtime with the updated dependencies.

The hosted **MCMI API** is designed to be failure resistent in the case of interrupted connections.  When a command execution is requested, the system launches a new worker process to handle that continues even if the user loses connection until completion or failure.  All results and messages that would be visible to the user normally are logged in the system and can be used to audit the running command execution in real time.  Backtraces are also recorded with each logged exception even if not displayed through the interface making debugging easier after the fact.

================================================================
Keep development, staging, and production as similar as possible
================================================================

The **MCMI** system bootstraps and manages itself through a standardized container architecture so ensuring environments are similar is a piece of cake.  All hosted application runtimes are compartmentalized into client environments, which allows for easy contextual management across infrastructure projects and environments.

Since **MCMI** needs access to resources, *like server SSH connections*, it needs to be deployed close to the resources being managed so the entire perimeter can be locked down, exposing a central command interface for an infrastructure environment.  The **MCMI** CLI interface makes deploying new remote API systems configured with different sets of modules exceptionally easy *(only four configurations necessary)*.

===========================
Treat logs as event streams
===========================

In the **MCMI** system all logs are directed to the **STDOUT** event stream making it easy to follow for log aggregation tools, and works well with general containerized log capture.  The system does not write to specialized log files.

The current logging level can be controlled through an environment variable that can be passed to the CLI shell environment or server container environment.  Currently we pass variables through Docker Compose configurations.

Command execution logs are treated separately and handled with integrated data models that allow for easy search and viewing from the application itself.

===============================================
Run admin/management tasks as one-off processes
===============================================

This twelfth factor just happens to be the **MCMI** sweet spot.  It was designed and built to create a portable toolbox of administrative and management commands as one-off processes.  The system generates a command tree formed by the core and all installed modules.  There is a command registry and routing system that finds, initializes, and ultimately runs the requested command in the foreground for client execution and in the background for server execution.

All commands execute in a process and can run subprocesses and threads, forming an internal concurrent process tree.  All commands are executed by users with role based permissions and logged to be easily audited by administrators.


.. [1] `Twelve Factor Applications <https://12factor.net/>`_