
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
    machine.vm.synced_folder ".", "/project", owner: vm_config["user"], group: vm_config["user"]

    if vm_config["copy_ssh_keys"]
      Dir.foreach("#{Dir.home}/.ssh") do |file|
        next if file == '.' or file == '..' or file == 'authorized_keys' or File.directory? "#{Dir.home}/.ssh/#{file}"
        machine.vm.provision :file, source: "#{Dir.home}/.ssh/#{file}", destination: "/home/#{vm_config["user"]}/.ssh/#{file}"
      end
    end
    if vm_config["copy_gitconfig"]
      machine.vm.provision :file, source: "#{Dir.home}/.gitconfig", destination: "/home/#{vm_config["user"]}/.gitconfig"
    end
    if vm_config["copy_vimrc"]
      machine.vm.provision :file, source: "#{Dir.home}/.vimrc", destination: "/home/#{vm_config["user"]}/.vimrc"
    end
    if vm_config["copy_profile"]
      machine.vm.provision :file, source: "#{Dir.home}/.profile", destination: "/home/#{vm_config["user"]}/.profile"
    end
    if vm_config["copy_bash_aliases"]
      machine.vm.provision :file, source: "#{Dir.home}/.bash_aliases", destination: "/home/#{vm_config["user"]}/.bash_aliases"
    end
    if vm_config["copy_bashrc"]
      machine.vm.provision :file, source: "#{Dir.home}/.bashrc", destination: "/home/#{vm_config["user"]}/.bashrc"
    end

    machine.vm.provision :shell, inline: init_session, run: "always"

    vm_config["port_map"].each do |guest_port, host_port|
        machine.vm.network :forwarded_port, guest: guest_port, host: host_port
    end
  end
end
