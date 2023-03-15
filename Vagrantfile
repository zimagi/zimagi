
vagrant_user = "vagrant"
vagrant_box = "bento/ubuntu-22.04"

config_dir = "#{__dir__}/config"
project_dir = "/project"


if File.exist?("#{config_dir}/vagrant.yml")
  vm_config = YAML.load_file("#{config_dir}/vagrant.yml")
else
  vm_config = YAML.load_file("#{config_dir}/_vagrant.yml")
end

Vagrant.configure("2") do |config|

  config.vm.define vm_config["hostname"] do |machine|
    machine.ssh.username = vagrant_user
    machine.vm.box = vagrant_box
    machine.vm.hostname = vm_config["hostname"]

    machine.vm.provider :virtualbox do |v|
      v.name = vm_config["hostname"]
      v.memory = vm_config["memory_size"]
      v.cpus = vm_config["cpus"]
      v.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
    end

    machine.vm.synced_folder "#{__dir__}", "/vagrant", disabled: true
    machine.vm.synced_folder "#{__dir__}", "#{project_dir}", owner: vagrant_user, group: vagrant_user

    if vm_config["copy_ssh_keys"]
      Dir.foreach("#{Dir.home}/.ssh") do |file|
        next if file == '.' or file == '..' or file == 'authorized_keys' or File.directory? "#{Dir.home}/.ssh/#{file}"
        machine.vm.provision :file, source: "#{Dir.home}/.ssh/#{file}", destination: "/home/#{vagrant_user}/.ssh/#{file}"
      end
    end
    if vm_config["copy_gitconfig"]
      machine.vm.provision :file, source: "#{Dir.home}/.gitconfig", destination: "/home/#{vagrant_user}/.gitconfig"
    end
    if vm_config["copy_vimrc"]
      machine.vm.provision :file, source: "#{Dir.home}/.vimrc", destination: "/home/#{vagrant_user}/.vimrc"
    end
    if vm_config["copy_profile"]
      machine.vm.provision :file, source: "#{Dir.home}/.profile", destination: "/home/#{vagrant_user}/.profile"
    end
    if vm_config["copy_bash_aliases"]
      machine.vm.provision :file, source: "#{Dir.home}/.bash_aliases", destination: "/home/#{vagrant_user}/.bash_aliases"
    end
    if vm_config["copy_bashrc"]
      machine.vm.provision :file, source: "#{Dir.home}/.bashrc", destination: "/home/#{vagrant_user}/.bashrc"
    end

    machine.vm.provision :shell do |s|
      s.name = "Saving session initialization script"
      s.path = "#{__dir__}/scripts/vm/session.sh"
    end
    machine.vm.provision :shell do |s|
      s.name = "Initializing Virtual Machine"
      s.path = "#{__dir__}/scripts/vm/init.sh"
    end

    vm_config["ports"].each do |host_port, port_reference|
      service_file, port_name = port_reference.split(':')
      service_file = "#{__dir__}/data/run/#{service_file}.data"

      if File.exist?(service_file)
        file_data = File.read(service_file)
        service_info = JSON.parse(file_data)
        guest_port = service_info.fetch('ports', {}).fetch(port_name, nil)

        if guest_port
          machine.vm.network :forwarded_port, guest: guest_port, host: host_port
        end
      end
    end
  end
end
