# -*- mode: ruby -*-
# vi: set ft=ruby :
require 'yaml'

# Load Vagrant configurations (versioned or unversioned)
if File.exist?("vagrant/config.yml")
  vm_config = YAML.load_file("vagrant/config.yml")
else
  vm_config = YAML.load_file("vagrant/config.default.yml")
end

set_environment = <<SCRIPT
tee "/etc/profile.d/cenv.sh" > "/dev/null" <<EOF
export PATH="${HOME}/bin:${PATH}"
export DEBUG=true
EOF
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.define :cenv do |machine|
    machine.vm.box = vm_config["box_name"]
    machine.vm.hostname = vm_config["hostname"]
    machine.vm.network "private_network", type: "dhcp"
    
    machine.vm.provider :virtualbox do |v|
      v.name = vm_config["hostname"]
      v.memory = vm_config["memory_size"]
      v.cpus = vm_config["cpus"]
    end

    machine.ssh.username = vm_config["user"]
    
    machine.vm.synced_folder ".", "/vagrant", disabled: true
    machine.vm.synced_folder "./app", "/usr/local/share/cenv", owner: "vagrant", group: "vagrant"
    machine.vm.synced_folder "./data", "/var/local/cenv", owner: "vagrant", group: "vagrant"
    machine.vm.synced_folder "./lib", "/usr/local/lib/cenv", type: "rsync", owner: "vagrant", group: "vagrant"

    machine.vm.provision :shell, inline: set_environment, run: "always"
    machine.vm.provision :file, source: "./app/docker-compose.dev.yml", destination: "docker-compose.yml"

    Dir.foreach("./scripts") do |script|
      next if script == '.' or script == '..'
      script_name = File.basename(script, File.extname(script))
      machine.vm.provision :file, 
        source: "./scripts/#{script}", 
        destination: "bin/#{script_name}"
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
      s.name = "Bootstrapping development server"
      s.path = "scripts/bootstrap.sh"
      s.args = [ 'vagrant', '/dev/stdout', 'true', vm_config['time_zone'] ]
    end

    machine.vm.network :forwarded_port, guest: 5123, host: vm_config["api_port"]
    machine.vm.network :forwarded_port, guest: 5432, host: vm_config["db_port"]
  end
end
