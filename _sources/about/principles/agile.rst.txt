#################
Agile Development
#################

Agile is a software development process that emphasizes: [1]_

  * **Individuals and interactions** over processes and tools

  * **Working software** over comprehensive documentation

  * **Customer collaboration** over contract negotiation

  * **Responding to change** over following a plan

In developing the **Zimagi** system we try to follow the Agile principles to ensure we are creating valuable software that actually fixes problems.

==================================================
Early and continuous delivery of valuable software
==================================================

The **Zimagi** system has evolved through iterations of working software.  It started out a bunch of shell scripts to deploy a high availability Kubernetes, became a Django powered CLI app focused on AWS or physical cluster management, added an HTTPS streaming RPC API, had many revisions of core components, broke apart into a modular architecture, and integrated various technologies like Terraform and Ansible.  The focus has been on getting something to work for a Minimum Viable Product.

Due to experimentation with architecture and our limitation of resources, almost no effort was originally put into documentation or testing.  These were deemed most efficiently executed after a working system and architecture was created to prevent reworking of test frameworks, fixtures, and documentation.  Time is of the essence, and this has been a pretty complicated system to develop.

=======================================================
Welcome changing requirements, even late in development
=======================================================

The requirements for the **Zimagi** system have changed quite a bit over time, and still continue to shift as we talk to more technology folks, and adapt the system to their needs by integrating their ideas.

This has been a major catalyst for the focus on modularity with a common core, so that we can evolve in many different directions simultaniously without compromising the core system.  We want to develop a diverse module ecosystem that tightly integrates around standardized building blocks.

===================================
Deliver working software frequently
===================================

We are frequently releasing updates to the **Zimagi** system through CI/CD processes triggered by code updates.  Supported modules are updated regularly and synced via the **Zimagi** module commands and initialization process.

Given the newness of this application system we are still fixing issues to ensure the software is working according to design requirements.  In the near future we will be adding full coverage unit and acceptance tests so we can ensure we are actually frequently releasing working software.

In the meantime, we can say we are frequently releasing software that mostly works *(we think)*

================================================================
All stakeholders must work together daily throughout the project
================================================================

So far in development this has been an internal tool to design and manage Kubernetes clusters, focused on technology engineers and managers *(us)*.  We have indeed been in touch with ourselves daily.

The **Zimagi** system is designed for technologists needing to create integrated and unified enterprise architecture, *who are our ultimate users*.  As we have more users of the software we will work collaboratively and transparently to co-evolve the software to meet everyone's needs.

===========================================
Build projects around motivated individuals
===========================================

One of the things that has helped advance this project is that the maintainers have a deep passion for and a lot of experience with cloud based infrastructure management and modular platforms *(enough to blow our savings creating the first version of this software)*

The passion has helped advance the project and keeps us motivated to continue, even in the face of set backs and obstacles.

=====================================================
Focus on communication via face-to-face conversations
=====================================================

Our current team meets regularly in person or in virtual meetings to plan development, communications, and related organizational development efforts around the project.

===================================================
Working software is the primary measure of progress
===================================================

From the beginning of this project working software has been the primary goal.  This allowed us to test various architecture patterns without having to worry about changes to tests or documentation with the limited time and resources we had.  Because software was the primary measure of progress, non development related delays have largely been avoided *(with the exception of organizational development tasks)*

We have been able to standardize a modular core architecture through an iterative succession of releases that built upon and redefined previous working releases.  Our architecture has evolved over the months to solve problems found in previous iterations.

=========================================================================
Sustainable development requires maintaining a constant pace indefinitely
=========================================================================

Our team works in weekly sprints, with a common backlog managed in `Trello <https://trello.com/b/uJ7912em/zimagi>`_ *(this board is pretty new)*.  We have weekly check-in meetings where we plan activities and ensure things are on track.

=============================================================================
Continuous attention to technical excellence and good design enhances agility
=============================================================================

Even though the **Zimagi** system has been an iterative series of architectural releases so far, there has always been a focus on creating an extensible architecture that was solid at the core.  We believe that a system is only as good as it's foundation, so we intended to get the core architecture right from the beginning.

Over time we are having to make fewer broad changes to the system to accomodate our feature ideas.  This allows us to move continually faster in release of new features to serve infrastructure management needs.

======================================================================
Focus on simplicity; the art of maximizing the amount of work not done
======================================================================

In the **Zimagi** software architecture there has been a focus on reusability through meta programming and factories to create generic operations, and sensible abstraction to encapsulate reusable logic.  We have also focused on creating a system that requires no programming knowledge to extend in meaningful ways.  The system is designed to make developing enterprise ready management systems as easy as possible.

As for development processes, we have avoided overcomplicating the process and introduced new technologies and processes into the software development lifecycle only as needed.  As the system gets more complete, the processes get more complex *(not before)*

===================================================================================
The best architectures, requirements, and designs emerge from self-organizing teams
===================================================================================

This project started as a personal project designed to set up and manage Kubernetes clusters on bare-metal servers.  It evolved to standardize cloud building blocks, and eventually turned into a very powerful database powered multi user orchestration system.  This evolution was driven by discussions between the developers, co-founders, external cloud architects and engineers, technology managers, and assorted literature and news.

There was no one telling anyone what to do to get where we are.  Development has flowed to what was most needed to serve collective goals, based on continuous feedback.  This process will help it grow in the future in diverse directions.

=========================================================================
Team regularly reflects on effectiveness and adjusts behavior accordingly
=========================================================================

There have been quite a few phases of development so far even with the short lifespan of this project, and as we grow we adopt new processes and technologies for helping us manage ourselves as we develop our team and the **Zimagi** system with related projects.

We are constantly looking at what we have done, measuring our progress, and changing strategies based on the situation at the time.  We meet regularly to discuss what we are doing, what we could be doing, and what we ultimately need to be doing, and recalibrate accordingly.


.. [1] `Agile Manifesto <https://agilemanifesto.org/>`_