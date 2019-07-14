################
Containerization
################

The **CENV** system is built on a fully containerized client / server architecture.  In fact, it is **made** to be difficult to run outside of containers.

Containers give us certain advantages that we use to enhance remote connection security and build a common core runtime for module developers.  Since we have based the architecture on containerized images it is easier for us to layer system architecture and create derivatives.  We also use containers to allow for a local operating mode that can perform any operation of a hosted **CENV API** and store local data yielding a flexible system that can effectively conserve resources, and is great for development.  **CENV** can also manage other containerized host services.

==================
Enhancing security
==================

One of the features of the **CENV** containerized architecture is that the service client runs the same image as the hosted API system, creating a synced mirror.  If the client is running an environment with a remote host defined then the client image and server image must match.  The images must share common certificates used for encrypting communications and data. **CENV requires a trusted and specialized client**.

All sensitive local and remote data is also encrypted/decrpyted with the image certificates.

Containers work well for us because they can be firewalled behind private registries, thus requiring credentialled access to run certain images.  Images can also easily be deleted after use, making them more ephemeral than installing dependencies and projects on the local machine.

Since images are layered, organizations can generate their own image certificates *(with included script)* and easily bundle with derivative Dockerfiles while inheriting all of the runtime dependencies.  These images can be built and deployed to private registries via **CI/CD** processes.

Different client environments can be set that use different images *(possibly with remote hosts)*, and developers can easily switch between them when working across projects or infrastructure environments.

======================
Extending core runtime
======================

One of the reasons containerization is so important for the **CENV** system is that it offers the ability to package extensible application runtimes.  This allows modules to add runtime dependencies that support their capabilities while keeping the core container image small and generic.

The system can generate and use new container images that are a combination of all installed module system dependencies, giving us a dynamic application runtime.  The ability for modules to run installation scripts and require Python packages provide integrated capabilities, such as Ansible and Terraform integration of the **CENV Cluster Management Module**.

==========
Local mode
==========

This system started out as a command line tool built on Django data modelling capabilities.  Shortly after, a streaming RPC command API was added that allows for the mirror execution of most local commands in shared remote environments.  This dual nature of the **CENV** system provides many benefits.

The local CLI based execution model for commands allows for easy development and experimentation without any system setup.  This local environment can then deploy itself to create standalone or high availability remote environments to provide an integrated networked command execution model that is great for individuals and federated team management alike.

Containers give us the ability to bundle all API dependencies into a locally executable runtime that can mirror what we run on a server.  As we have mentioned above in the security section, local and remote images must always match to successfully connect and operate.

This system also means developers of **CENV** core and modules do not have to worry about divergent runtime environment specifications, and can focus on the task at hand instead of handling different hosting configurations.  **CENV** is very opinionated about the runtime environment to standardize and allow easier integration without extra effort.

==================
Service management
==================

The **CENV** system is designed to be able to manage host Docker services.  It has a system management interface that allows for the execution of containers that modules might need running in the background to achieve their objectives.

The core system uses this system management interface to launch a local PostgreSQL database server from the official Docker image.  When this database is in use it replaces the connection to the default SQLite3 database file.  This can be handy for testing on a more robust database or increasing database access concurrency.  The core provides commands for starting and stopping and/or removing this service.

Any module can use this interface to create auxillary services that provide background capabilities as needed for plugins and commands.
