# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Load Vagrant configurations (versioned and unversioned)
vm_config = YAML.load_file("vagrant/config.default.yml")
vm_config.merge!(YAML.load_file("vagrant/config.yml")) if File.exist?("vagrant/config.yml")

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  vagrant_home = "/home/vagrant"
  project_directory = "/vagrant"

  config.vm.box = vm_config["box_name"]
  config.vm.hostname = vm_config["server_name"]

  # If you want to listen at a specific local IP address
  # > add "ip_address: '###.###.###.###'" to your vagrant-config.yml
  if vm_config.has_key?("ip_address")
    config.vm.network :private_network, ip: vm_config["ip_address"]
  end

  config.vm.provider :virtualbox do |v|
    v.name = vm_config["server_name"]
    v.memory = vm_config["memory_size"]
    v.cpus = vm_config["cpus"]
  end

  if vm_config["copy_gitconfig"]
    config.vm.provision :file, source: "~/.gitconfig", destination: ".gitconfig"
  end
  if vm_config["copy_vimrc"]
    config.vm.provision :file, source: "~/.vimrc", destination: ".vimrc"
  end

  if vm_config["copy_profile"]
    config.vm.provision :file, source: "~/.profile", destination: ".profile"
  end
  if vm_config["copy_bash_aliases"]
    config.vm.provision :file, source: "~/.bash_aliases", destination: ".bash_aliases"
  end
  if vm_config["copy_bashrc"]
    config.vm.provision :file, source: "~/.bashrc", destination: ".bashrc"
  end
  config.vm.provision :shell do |s|
    s.name = "Bash startup additions (scripts/vagrant-bash)"
    s.inline = <<-SHELL
      if ! grep -q -F '#<<kubernetes>>' "${HOME}/.bashrc" 2>/dev/null
      then
        cat "${PROJECT_DIR}/scripts/vagrant-bash.sh" >> "${HOME}/.bashrc"
      fi
    SHELL
    s.env = { "HOME" => vagrant_home, "PROJECT_DIR" => project_directory }
  end

  config.vm.provision :shell do |s|
    s.name = "Bootstrapping development server"
    s.path = "scripts/bootstrap.sh"
    s.args = [ project_directory ]
  end
end