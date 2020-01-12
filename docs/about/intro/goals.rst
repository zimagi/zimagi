#####
Goals
#####

As we discussed in the `problem section <./problem.html>`_, there is a profound need to integrate cloud services and physical hardware into a **federated cloud strategy** in order to economically leverage the cloud given rapidly expanding computing needs and constrained organizational resources.

Being professionally involved in this field for many years, we needed a system that could allow us to unify the management of platforms and applications across vendors and hardware using standardized building blocks that can be easily developed by non-engineers.  We needed a system that doesn't rely on the security promises of people but enforces it as architecture.  We needed an internet capable toolbox where we can collaborate with other organizations to build truly interoperable systems with distributed teams.

.. image:: /_static/images/goals.png
    :width: 700px
    :height: 400px
    :align: center
    :alt: MCMI goals

*Our challenge:* **Design a modular database driven web platform and toolset that makes it easy to securely design, build, and manage complex federated infrastructure.**

We think of this as an **Infrastructure Content Management System**, *made for auditable multi tenant administration and CI/CD pipelines*.

===================
Open and extensible
===================

One of the central goals of this project is to maximize the pluggability and modularity of the data, command, and orchestration component models, so that more systems and cloud providers can be integrated easily into a unified interface.

It should be easy for non-programmers to evolve the system to suit their needs with evolving common standards that allow federated teams to design, build, and manage dynamic infrastructure over time.

By focusing on building and freely releasing an extensible open core we can merge open source and proprietary extensions as needed for organizational needs.  The core is meant to be an architectural bridge and secure runtime.

We are ultimately planning a marketplace of modules with various forms of core extension, but for now modules containing plugins can be easily created as Git repositories and installed via commands or environment variable definitions.

=====================================
High performance and reliable systems
=====================================

Many computing jobs require high performance computing.  This includes data science processing and data management.  As the cloud has created APIs for all manner of services, it has also added system bloat, such as in the case of hypervisors.  With containerization it gets even slower as layers are added.  Sometimes running on dedicated hardware is the right choice, or we want to run containers on hardware.  When dedicated hardware is not the right choice, it's important that we can switch cloud providers if necessary to ensure regional or service level reliability.

This project attempts to make building hybrid and multi clouds easier by creating a plugin model that works well with automation of the cloud, or manual entry of physical hardware / dedicated systems, so that the cloud and physical infrastructure can coexist harmoniously in a unified architecture, able to be managed together or independently.  By pursuing a multi-cloud plugin model we make it easier to switch vendors to ensure access to the best performing and most reliable systems and services.

===================
Secure environments
===================

Security is of central importance to every organization.  It is important that administrative privileges are limited to current users who are acting in specific capacities.  It is important that important data is not corrupted or leaked, and that communications can not be intercepted.  It is really important to know what is going on, and who is doing what.  After all, management of infrastructure entails knowing almost all of your root credentials.  Breaches in security can be the death of organizations.

We aim to make the **MCMI** project the most secure way to manage federated infrastructure.  To keep all communications secure we enforce certificate identified clients for fully encrypted streaming API requests *(including requirement to encrypt client credentials and command parameters)*. To ensure data is secure we store sensitive information in strongly encrypted form (**AES 256**), so if the database is hacked or backups are stolen there is time to recover.  All commands require users with certain roles, and all executions are logged and easily searchable.  We aim to make it more secure and fill in the gaps with your help.

====================================
Standardized and automated processes
====================================

Different cloud providers have different strengths and weaknesses.  Mission critical systems demand high availability and reliable / performant hardware.  Modern Portfolio Theory states that the best way to ensure safety and growth is to diversify.  By diversifying, organizations enjoy the benefits of emerging technology quicker, integrated into their workflows, maximizing their competitive advantage, and lowering the overall risk and cost of ownership.

A major goal of this project is to bring systems and cloud providers together to create this diversity, allowing easy switching between systems and providers by creating a standardized language, runtime, and interface to developing infrastructure and process automation building blocks through an extensible microservices architecture.

With **MCMI** organizations build and host API based command trees that manage infrastructure and orchestrate diverse workflows, managed by administrators with different roles.

======================================
Integrated and scalable infrastructure
======================================

An organization can only grow as fast as they can scale their infrastructure and processes before they experience negative results from growth.  It is also important to be able to take advantage of the prime benefit of the cloud; that you can scale down infrastructure spending when not in use to preserve operating capital.  Using the cloud as a continuous data center without scalable architecture is **VERY** costly.  Sometimes scaling across regions requires connecting services, which adds a new degree of difficulty.

This project is designed to promote extreme scalability of composible cloud architecture building blocks.  It is easy to define, create, and destroy *(with an architecture that is standard across providers when possible)*.  The intention is that cloud building blocks are developed and maintained by experts and shared with other divisions / organizations to create a federated IT architecture that promotes economies of scale through specialization of labor.

===================
Fast learning curve
===================

Imagine if designing multi / hybrid cloud was as easy as defining and overriding cascading key value pairs.  This system would not require coding to design complex infrastructure, but module integration and human readable data configuration.  Imagine if we could weave our favorite technologies together into a unified toolbelt that could be shared and co-maintained.  Imagine if hardware was almost as easy to manage over time as cloud resources, and we could view it different ways.  Imagine a federated world driven by standards that securely bind our infrastructure and processes.  This is the world we imagine.

Organizations need easy ways to grow quickly to serve evolving needs, while facing resource shortages.  Fewer people are required to do more requiring an easier time training.  The **MCMI** system is designed to standardize interfaces to systems and providers, to allow for broad flexibility of purpose.
