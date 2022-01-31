
ENV["VAGRANT_EXPERIMENTAL"] = "typed_triggers"

vagrant_user = "vagrant"
vagrant_box = "bento/ubuntu-20.04"

config_dir = "#{__dir__}/config"
project_dir = "/project"


if File.exist?("#{config_dir}/vagrant.yml")
  vm_config = YAML.load_file("#{config_dir}/vagrant.yml")
else
  vm_config = YAML.load_file("#{config_dir}/_vagrant.yml")
end

Vagrant.configure("2") do |config|

  config.trigger.before :"VagrantPlugins::ProviderVirtualBox::Action::CheckGuestAdditions", type: :action do |t|
    t.info = "Ensuring project directory exists and is writable"
    t.run_remote = {
      inline: "mkdir -p #{project_dir}; chown #{vagrant_user}:#{vagrant_user} #{project_dir}"
    }
  end

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
    machine.vm.synced_folder "#{__dir__}/.circleci", "#{project_dir}/.circleci", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/.git", "#{project_dir}/.git", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/scripts", "#{project_dir}/scripts", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/config", "#{project_dir}/config", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/docker", "#{project_dir}/docker", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/docs", "#{project_dir}/docs", owner: vagrant_user, group: vagrant_user

    if File.directory?("#{__dir__}/certs")
      machine.vm.synced_folder "#{__dir__}/certs", "#{project_dir}/certs", owner: vagrant_user, group: vagrant_user
    end
    if File.directory?("#{__dir__}/build")
      machine.vm.synced_folder "#{__dir__}/build", "#{project_dir}/build", owner: vagrant_user, group: vagrant_user
    end

    machine.vm.synced_folder "#{__dir__}/app", "#{project_dir}/app", type: "rsync", owner: vagrant_user, group: vagrant_user
    machine.vm.synced_folder "#{__dir__}/package", "#{project_dir}/package", type: "rsync", owner: vagrant_user, group: vagrant_user

    if File.directory?("#{__dir__}/charts")
      machine.vm.synced_folder "#{__dir__}/charts", "#{project_dir}/charts", type: "rsync", owner: vagrant_user, group: vagrant_user
    end
    if File.directory?("#{__dir__}/lib")
      machine.vm.synced_folder "#{__dir__}/lib", "#{project_dir}/lib", type: "rsync", owner: vagrant_user, group: vagrant_user
    end

    machine.vm.provision :file, source: "#{__dir__}/.gitignore", destination: "#{project_dir}/.gitignore"
    machine.vm.provision :file, source: "#{__dir__}/Vagrantfile", destination: "#{project_dir}/Vagrantfile"
    machine.vm.provision :file, source: "#{__dir__}/README.md", destination: "#{project_dir}/README.md"
    machine.vm.provision :file, source: "#{__dir__}/LICENSE", destination: "#{project_dir}/LICENSE"

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

    vm_config["port_map"].each do |guest_port, host_port|
        machine.vm.network :forwarded_port, guest: guest_port, host: host_port
    end
  end
end
