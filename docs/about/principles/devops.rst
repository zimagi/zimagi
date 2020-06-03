###############
DevOps Practice
###############

Although there are many definitions of **DevOps** we believe the practice can be nicely summarized through two overarching perspectives;  *Gene Kim's* **Three Ways**, and the **CALMS principles** defined by *Damon Edwards*, *John Willis*, and *Jez Humble*.

The **Zimagi** system is designed to fit nicely into an organization's **DevOps** practice *(note I include DevSecOps, etc... into one label)*.  Below I will cover some of the ways this system helps integrate teams, technology, and services into a unified whole.

The goal is to maximize economies of scale and create a frictionless environment for the development of software systems.

================
Systems thinking
================

The first of Gene Kim's Three Ways has to do with thinking about the performance of the system as a whole instead of focusing on the independent parts *(silos)*.  When we think about the whole system we can more easily see ways to work seamlessly together to address bottlenecks and inefficiencies in the system.

While systems thinking is well beyond the scope of any software, the **Zimagi** system can help design systems and integrate services to create efficient organizational workflows.  **Zimagi** allows us to think about our systems as a tree of interrelated capabilities with agents *(users)* able to perform functions over time.  The system allows us to link and create standards between services or technology we depend on.  Because the core is so flexible we can integrate pretty much whatever we need, be it an API interface or a CLI execution.

We refer to **Zimagi** as an **Infrastructure Content Management System** because at the core it manages data objects which describe our infrastructure and processes.  This means we can import data through administrative actions or orchestration language and generate output in different forms, *such as for realtime inventories or compliance documentation*.

==============
Feedback loops
==============

The second of Gene Kim's Three Ways has to do with creating feedback loops that drive process improvements in the system over time.  This allows us to evolve quicker with customer needs, and improve the overall quality of service, keeping happy stakeholders.

While **Zimagi** does not create feedback loops itself, it is driven by iterative development based on feedback loops.  The modularity of the system allows shorter feedback loops between release of needed features that can then be later merged with other modules, or the core system if generally applicable.  If something doesn't work or is not needed it can be easily removed.

By allowing the system to grow according to a community driven by sometimes overlapping feedback loops, we can evolve a diverse ecosystem of capabilities organizations can apply to their own operations.

==========================
Continuous experimentation
==========================

The third of Gene Kim's Three Ways is about creating a culture that fosters continual experimentation, taking risks, and learning from failure.  Repetition and practice are the prerequisites for mastery.  Experimentation and continuous learning allow us to constantly innovate in our areas of focus, driving constant improvements in our products and processes.

The **Zimagi** system promotes experimentation by creating a modular architecture and local development mode that makes extending and testing the system easy.  It is also possible to extend the system through simple YAML files, requiring no coding.  If you know how to execute commands on the command line and edit files, you can extend the system to your needs.

There is no need to wait for features to make it into core before you can have a stable upgrade path.  Modules can have their own branching strategies and extend virtually every part of the core system.  They can even extend other modules.  This gives us a lego like ability to construct exactly what we need with the least work possible to efficiently experiment with infrastructure combinations.

=======
Culture
=======

An integrated culture that works well together ultimately helps the organization succeed.  Culture is the biggest driver of effective management.  A team that works well together and focuses on contributing what they know best to make the entire system more sustainable are more likely to produce a software system that works, on a budget.

While the **Zimagi** system can't make teams get along, it can help team members and federated teams work more effectively together.

A role based command execution model is employed that allows for users of different privileges to co-manage different aspects of the infrastructure.  As we mentioned in the micro-services section it is also easy to split the **Zimagi** system into multiple hosted API's focused on different systems or infrastructure groups to promote decentralized management and tighter security.

Modules can define sets of commands, which can be orchestrated through a powerful, yet easy key/value YAML based language.  Modules can easily be created by IT administrators without any coding necessary, and can be as simple as a single YAML file.  The system is based on a deep merge of configurations from different modules which allows for one team to easily build upon the work of an upstream team, to capture more knowledge and updatable work over time from the upstream maintainers.

==========
Automation
==========

Automation helps organizations scale our operations efficiently.  When we have an effective innovative culture and automation is applied then organizations can start to see exponential returns on our technology investment, as improvements in the technology and process build on each other.

The **Zimagi** system helps us glue all of our automation together into a unified architecture of flexible components utilizing common standards.

Automation often takes many forms.  We program and execute scripts.  We connect to APIs.  We run various tools, and integrate coding frameworks.  **Zimagi** is meant to be a system that can tie everything together into a common orchestration system.  This means orchestration tools like Terraform can work seamlessly with configuration management tools like Ansible, shell scripts, and assorted CLI commands to fully provision and manage high availability infrastructure systems.  Any technology or connection could be added through an adaptable module and plugin model.

Commands serve as the basic execution building block which can manage data.  Commands are arranged into component workflows within the orchestration system, giving us the ability to execute extremely complex operations over time remotely through a secure fault tolerant environment.

====
Lean
====

In organizations it is important that we use resources as effectively as possible, so that we can compete or provide for our constituents more effectively.  This means focusing on a lean process, where we constantly clean up what is not needed.  This philosophy also leads to creating scalable technology architecture, that can scale up and down as needed based on demand.

The **Zimagi** system makes it easy to create and destroy temporary infrastructure, and can operate with minimal resources.

Scaling infrastructure up and down can save us a lot of money, but it takes careful automation to ensure that systems are connected, data is preserved, and we don't have orphan infrastructure *(usually due to errors during destroy)*.  The **Zimagi** system allows us to easily create new resources, scale numbers up and down in the case of components like servers, and cleanly delete resources when not needed.  The orchestration language was made to bootstrap, manage, and clean up very complex deployments.

As mentioned earlier, **Zimagi** can be used in local development mode when experimenting, saving money on cloud resources, and eliminating the need for a server eating memory.  It is also possible to deploy a single server API that works on small cloud images.  If needed **Zimagi** provides orchestration language for setting up a high availability **Zimagi API** in the cloud.

===========
Measurement
===========

In order to know where we are going, we must know where we are and where we have been.  In order to know where we are or where we have been we must take measurements and collect data over time.  This data feeds an evaluation process that creates a feedback loop that allows us to improve over time.  We set goals and accurately measure progress.  It's hard to argue with empirical evidence.

The **Zimagi** system was made to collect data on the state our infrastructure, and it logs all activity so we always know where we are and where we've been.

At the heart of **Zimagi** is a data management system built on Django's Object Relational Mapping *(ORM)* interface, which is quite sophisticated and easy to use.  The **Zimagi** system adds another layer of management on top to eliminate the need for **CRUD** operation definition for application data models.  We implement automatic data management, so no queries are ever needed for tracked data.  New data models and related interface commands are easy to define.

The **Zimagi** system has a powerful command logging interface that gives us a realtime view into what is being executed, and by whom.  We can search the commands that have been executed over time with very granular filters, and we can view detailed information pertaining to every command that has run or is running, including messages that would be displayed through the client gateway interface.

=======
Sharing
=======

In order to create a culture that innovates people must know what is going on.  The more transparent the process and situation, the more people can adjust to compensate.  Trying to operate in an opaque system is like trying to play a baseball game without knowing the inning or score.  It just doesn't work.  Efficient software development requires buy-in from teammates, and the best way to get buy-in is by sharing and openly collaborating.

The **Zimagi** system helps share data on the state of our infrastructure, so we have a realtime picture of resources available, and how everything fits together.

It can be very hard keeping track of everything in our infrastructure at a given time, *especially when we are working in a hybrid or multi-cloud environment*.  The **Zimagi** system is meant to piece everything together and give those with access a view into the current situation.  One really nice thing about the system is that it gives us a very easy way to see the linkages between resources, so we can get a big picture view.

This system also opens up new possibilities for exporting relevant data pertaining to our infrastructure, *such as for inventory, compliance reports, or general IT audits*.  By collecting data into a unified system we can combine, export, and share it more effectively and efficiently with those who need to know what is going on to do their jobs.
