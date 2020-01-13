require 'yaml'
require 'json'
require 'fileutils'

unless File.directory?("./certs")
  FileUtils.mkdir_p("./certs")
end
unless File.directory?("./data")
  FileUtils.mkdir_p("./data")
end
unless File.directory?("./lib")
  FileUtils.mkdir_p("./lib")
end

if File.exist?("./vagrant/config.yml")
  vm_config = YAML.load_file("./vagrant/config.yml")
else
  vm_config = YAML.load_file("./vagrant/config.default.yml")
end

set_environment = <<SCRIPT
tee "/etc/profile.d/mcmi.sh" > "/dev/null" <<EOF
export PATH="${HOME}/bin:${PATH}"
export MCMI_DEBUG=true
export MCMI_DEFAULT_MODULES='#{vm_config["default_modules"].to_json}'
EOF
SCRIPT

if vm_config["share_lib"]
  unless Vagrant.has_plugin?("vagrant-sshfs")
    system "vagrant plugin install vagrant-sshfs"
  end
end

Vagrant.configure("2") do |config|
  config.vm.define :mcmi do |machine|
    machine.vm.box = vm_config["box_name"]
    machine.vm.hostname = vm_config["hostname"]
    machine.vm.network "private_network", type: "dhcp"

    machine.vm.provider :virtualbox do |v|
      v.name = vm_config["hostname"]
      v.memory = vm_config["memory_size"]
      v.cpus = vm_config["cpus"]
      v.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
    end

    machine.ssh.username = vm_config["user"]

    machine.vm.synced_folder ".", "/vagrant", disabled: true
    machine.vm.synced_folder "./certs", "/home/vagrant/certs", owner: "vagrant", group: "vagrant"
    machine.vm.synced_folder "./app", "/home/vagrant/app", owner: "vagrant", group: "vagrant"
    machine.vm.synced_folder "./data", "/var/local/mcmi", owner: "vagrant", group: "vagrant"
    machine.vm.synced_folder "./docs", "/home/vagrant/docs", owner: "vagrant", group: "vagrant"

    if vm_config["share_lib"]
      machine.vm.synced_folder "./lib", "/usr/local/lib/mcmi", type: "sshfs", owner: "vagrant", group: "vagrant"
    end

    machine.vm.provision :shell, inline: set_environment, run: "always"
    machine.vm.provision :shell,
      inline: "[ -L /usr/local/share/mcmi  ] || ln -s /home/vagrant/app /usr/local/share/mcmi",
      run: "always"

    machine.vm.provision :file, source: "./app/docker-compose.dev.yml", destination: "docker-compose.yml"
    machine.vm.provision :file, source: "./docs/requirements.txt", destination: "requirements-docs.txt"

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
      s.args = [ 'vagrant', '/var/log/bootstrap.log', vm_config['time_zone'] ]
    end

    machine.vm.network :forwarded_port, guest: 5123, host: vm_config["api_port"]
    machine.vm.network :forwarded_port, guest: 5432, host: vm_config["db_port"]
    machine.vm.network :forwarded_port, guest: 6379, host: vm_config["queue_port"]
  end
end
