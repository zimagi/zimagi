##############
Micro-Services
##############

The **CENV** system is designed to generally follow the `micro-services architecture pattern <https://en.wikipedia.org/wiki/Microservices>`_, and even provide a basic building block approach to creating highly specialized, yet interconnected micro-service management APIs.

=======================
Modular building blocks
=======================

**CENV** exists for one core reason; to **securely orchestrate commands as needed in a shared environment**.  These commands can be compartmentalized into specialized runtimes.  Because of the modular architecture, the core can be used as a base to create interfaces to various organizational capabilities and services, that could work together to form integrated functions.

It is completely up to the user to determine in what manner to mix what modules into independently hosted systems.

========================
Decentralized processing
========================

One of the key architectural features of **CENV** is that it is designed to be run in a decentralized manner.  For instance, separate APIs would be deployed to manage different infrastructure environments so that these environments can be securely locked down with a single management interface.  Thus if one system goes down for some reason, the others stay operational.

Our initial use case is to have an individual **CENV API** manage a potentially multi-region or multi-provider federated Kubernetes cluster environment.

It is easy to deploy the **CENV API** in a remote configuration, and easy to manage and track decentralized instances.  The **CE** client can contextually switch between and manage connections to multiple remote hosts.

==============================
Technology and service wrapper
==============================

**CENV** is meant to be a glue that holds technologies and services people love to use to provide a role based access interface that brings everything together.  In this capacity, major functional components can be written in other languages, and service integrations are fairly easy to develop.  The **CENV** system is great at integrating APIs and CLI commands written in languages that are the best fit for the task at hand.

This focus on integration gives us the ability to provide diverse organizational capabilities while keeping a small core system.  The common core makes adding and splitting capabilities between systems easy and reduces the learning curve for creating command driven micro-services that power organizations systems and services.
