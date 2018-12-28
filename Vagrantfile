# -*- mode: ruby -*-
# vi: set ft=ruby :
require 'yaml'

# Load Vagrant configurations (versioned or unversioned)
if File.exist?("vagrant/config.yml")
  vm_config = YAML.load_file("vagrant/config.yml")
else
  vm_config = YAML.load_file("vagrant/config.default.yml")
end

Vagrant.configure("2") do |config|
  config.vm.define :cenv do |machine|
    machine.vm.box = vm_config["box_name"]
    machine.vm.hostname = vm_config["hostname"]
    machine.vm.network "private_network", type: "dhcp"

    machine.vm.provider :virtualbox do |v|
      v.name = vm_config["hostname"]
      v.memory = vm_config["memory_size"]
      v.cpus = vm_config["cpus"]
      v.customize ['setextradata', :id, 'VBoxInternal2/SharedFoldersEnableSymlinksCreate/v-root', '1']
    end

    machine.ssh.username = vm_config["user"]
    
    machine.vm.synced_folder ".", "/vagrant", disabled: true
    machine.vm.synced_folder ".", "/opt/cenv"

    if vm_config["copy_gitconfig"]
      machine.vm.provision :file, source: "~/.gitconfig", destination: ".gitconfig"
    end
    if vm_config["copy_vimrc"]
      machine.vm.provision :file, source: "~/.vimrc", destination: ".vimrc"
    end

    if vm_config["copy_profile"]
      machine.vm.provision :file, source: "~/.profile", destination: ".profile"
    end
    if vm_config["copy_bash_aliases"]
      machine.vm.provision :file, source: "~/.bash_aliases", destination: ".bash_aliases"
    end
    if vm_config["copy_bashrc"]
      machine.vm.provision :file, source: "~/.bashrc", destination: ".bashrc"
    end

    machine.vm.provision :shell do |s|
      s.name = "Bash startup additions (scripts/vagrant-bash)"
      s.inline = <<-SHELL
        if ! grep -q -F '#<<cenv>>' "/home/vagrant/.bashrc" 2>/dev/null
        then
          cat "/opt/cenv/scripts/vagrant-bash.sh" >> "/home/vagrant/.bashrc"
        fi
      SHELL
    end

    machine.vm.provision :shell do |s|
      s.name = "Bootstrapping development server"
      s.path = "scripts/bootstrap.sh"
      s.args = [ 'vagrant', '/var/log/bootstrap.log', 'true', vm_config['time_zone'] ]
    end

    machine.vm.network :forwarded_port, guest: 5123, host: vm_config["api_port"]
    machine.vm.network :forwarded_port, guest: 5432, host: vm_config["db_port"]
  end
end
