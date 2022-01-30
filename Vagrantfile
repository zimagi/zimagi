
if File.exist?("#{__dir__}/config/vagrant.yml")
  vm_config = YAML.load_file("#{__dir__}/config/vagrant.yml")
else
  vm_config = YAML.load_file("#{__dir__}/config/_vagrant.yml")
end

init_session = <<SCRIPT
cat > /etc/profile.d/zimagi.sh <<EOF
source /project/reactor path
cd /project
EOF
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.define vm_config["hostname"] do |machine|
    machine.ssh.username = vm_config["user"]
    machine.vm.box = vm_config["box_name"]
    machine.vm.hostname = vm_config["hostname"]

    machine.vm.provider :virtualbox do |v|
      v.name = vm_config["hostname"]
      v.memory = vm_config["memory_size"]
      v.cpus = vm_config["cpus"]
      v.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
    end

    machine.vm.synced_folder ".", "/vagrant", disabled: true
    machine.vm.synced_folder ".", "/project", owner: "vagrant", group: "vagrant"

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

    machine.vm.provision :shell, inline: init_session, run: "always"

    vm_config["port_map"].each do |guest_port, host_port|
        machine.vm.network :forwarded_port, guest: guest_port, host: host_port
    end
  end
end
