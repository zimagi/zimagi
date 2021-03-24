###########################
Getting Started with Zimagi
###########################

This guide will help you understand the motivations behind Zimagi, how to set
up a development-ready machine, and primers on working with Vagrant and Docker
(particularly as related to this project). We also discuss what you need to
know about environment setup in order to run this application with other
services.

.. toctree::
    :maxdepth: 3
    :caption: Getting Started

    about
    components
    use_module
    create_module
    vagrant
    contributing

Zimagi is a distributed data processing platform that can orchestrate and
manage acquisition, scheduling, normalization, integration, and process
control.

Zimagi has similar goals to other workflow managers such as Airflow and Luigi,
but with an emphasis on low-code development that relies primarily on
configuration files defined in friendly YAML syntax.

-  **Data Models as Code** - Data Models are the data objects that can
   be defined as code. This makes it easier to collaborate, maintain and
   distribute across functional teams members.

-  **Build Data Processing Workflows** - Complex Data Workflows known as
   *Profiles* can be created to orchestrate the data imports and
   transformations across clusters.

-  **Ship Zimagi Projects** - The data models along with settings,
   specifications and other configurations can be shipped as git version
   controlled *Modules*.

-  **Portability** - Zimagi can be installed anywhere and doesn’t
   require a dedicated server.

-  **Data Security** - The platform data, configurations and fields are
   encrypted. This secures the meta data related to the Zimagi modules.

The Zimagi Platform can be utilized from two user perspectives:

-  *Zimagi Module Developers* - The Data models and specifications are
   defined by these developers. The modules developed by these users
   will be utilized by the Module users.

-  *Zimagi Module Users* - The portable modules developed by the Zimagi
   Module Developers can be cloned onto any machines and zimagi platform
   can be made up and running by the users.



