# CENV documentation

CENV (Command Environment) is a command orchestration environment.

<br/>

## Outline

#### Introduction

* **[Overview](introduction/readme.md)**

  * [Problem](introduction/problem.md)
  * [Goals](introduction/goals.md)
  * [Progress](introduction/progress.md)

#### Principles

* **[Overview](principles/readme.md)**

  * [Containerization](principles/containers.md)
  * [Twelve Factor Applications](principles/twelve-factor-apps.md)
  * [Agile Development](principles/agile.md)
  * [DevOps Practices](principles/devops.md)

#### Getting Started

* **[Overview](start/readme.md)**

  * [Installation](start/installation.md)
  * [CLI Interface](start/cli.md)
  * [API Background](start/api.md)
  * [CI/CD Integration](start/cicd.md)

#### Architecture

* **[Overview](architecture/readme.md)**

  * [System Management](architecture/system-management.md)
  * [Data Management](architecture/data-management.md)
  * [Command Framework](architecture/command-framework.md)
  * [Command Environment](architecture/command-environment.md)
  * [Orchestration System](architecture/orchestration-system.md)
  * [Orchestration Language](architecture/orchestration-language.md)
  * [Module System](architecture/module-system.md)

#### Modules

* **[Overview](modules/readme.md)**

  * [Core](modules/core.md)
  * [Cluster Management](modules/cluster.md)
  * [Percona MySQL Cluster](modules/percona.md)
  * [API](modules/api.md)

#### Commands

* **[Overview](commands/readme.md)**

  * **[Core Commands](commands/core/readme.md)**

    * [Integrations](commands/core/integrations.md)
    * [Getting Help](commands/core/help.md)
    * [Logging and Audit](commands/core/audit.md)
    * [Users and Environments](commands/core/user-environment.md)
    * [States and Configurations](commands/core/state-config.md)
    * [Groups and Roles](commands/core/groups.md)
    * [Module Management](commands/core/modules.md)
    * [Database Management](commands/core/database.md)
    * [Task Execution](commands/core/tasks.md)
    * [Profile Execution](commands/core/profiles.md)

  * **[Cluster Management Commands](commands/cluster/readme.md)**

    * [Integrations](commands/cluster/integrations.md)
    * [Domains and DNS Management](commands/cluster/dns.md)
    * [Network and Subnet Management](commands/cluster/network.md)
    * [Firewall Management](commands/cluster/firewall.md)
    * [Certificate Management](commands/cluster/certificates.md)
    * [Shared Storage Management](commands/cluster/storage.md)
    * [Server Management](commands/cluster/servers.md)
    * [Load Balancing](commands/cluster/load-balancing.md)
    * [CENV Deployment](commands/cluster/deployment.md)

#### Tasks

* **[Overview](tasks/readme.md)**

  * **[Cluster Management Tasks](tasks/cluster/readme.md)**

    * [Ansible](tasks/cluster/ansible.md)
    * [Management](tasks/cluster/management.md)
    * [Utilities](tasks/cluster/utilities.md)

  * **[Percona Cluster Tasks](tasks/percona/readme.md)**

    * [Ansible](tasks/percona/ansible.md)
    * [Management](tasks/percona/management.md)

  * **[CENV API Tasks](tasks/api/readme.md)**

    * [Ansible](tasks/api/ansible.md)
    * [Management](tasks/api/management.md)

#### Profiles

* **[Overview](profiles/readme.md)**

  * **[Core Profiles](profiles/core/readme.md)**

    * [Display](profiles/core/display.md)

  * **[Cluster Management Profiles](profiles/cluster/readme.md)**

    * [Display](profiles/cluster/display.md)
    * [Configuration](profiles/cluster/config.md)
    * [Domain](profiles/cluster/domain.md)
    * [Network](profiles/cluster/network.md)

  * **[Percona Cluster Profiles](profiles/percona/readme.md)**

    * [Configuration](profiles/percona/config.md)
    * [Cluster](profiles/percona/cluster.md)

  * **[API Profiles](profiles/api/readme.md)**

    * [Configuration](profiles/api/config.md)
    * [Domain](profiles/api/domain.md)
    * [Network](profiles/api/network.md)
    * [Core](profiles/api/core.md)
    * [Cluster Bootstrap](profiles/api/cluster-bootstrap.md)
    * [Cluster Manage](profiles/api/cluster-manage.md)
    * [Administration Manage](profiles/api/admin-manage.md)

#### Getting Help

* **[Overview](help/readme.md)**

#### Contributing

* **[Overview](contribute/readme.md)**

<br/>

## Related projects

* [CENV Cluster Module](https://github.com/venturiscm/cenv-cluster)
* [CENV Percona Module](https://github.com/venturiscm/cenv-percona)
* [CENV API Module](https://github.com/venturiscm/cenv-api)
* [CENV Kubernetes Module](https://github.com/venturiscm/cenv-kubernetes)

<br/>