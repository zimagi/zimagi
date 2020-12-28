# Launching Vagrant containers

If all goes well, you can simply launch a virtual machine with multiple Docker
containers by switching to the repository directory and typing:

```bash
vagrant up
```

Provisioning the maching and launching the images will take a few minutes, but
otherwise everything should "just work."

## When things go wrong

### Dependencies

A few dependencies need to be installed on the host.  The first of these,
straighforwardly, is Vagrant itself.  Instructions for installing Vagrant are
at https://www.vagrantup.com/downloads.html.

For Vagrant to work, it also needs a virtual machine provider installed.  Our
included Vagrantfile utilizes VirtualBox, but other such as VMWare, Hyper-V, or
indeed Docker containerization, will also work.  Using a different virtual
machine will require small modifications to the Vagrantfile.

Installation instructions for VirtualBox can be found at
https://www.virtualbox.org/wiki/Downloads.

Zimagi uses sshfs (Secure Shell File System) to share the contents of the
`lib/` directory between host and guest.  Allowing this workflow is
advantageous and easier than working only through git commits.  You will need
to install sshd on your host system for this to work, usually in the form of
OpenSSH.  Information about installing OpenSSH can be found at
https://www.openssh.com/.

However, a currently known bug in Vagrant prevents sshfs from working on some
host configurations.  We are working to resolve this restriction.  The file
`vagrant/config.yml` overrides `config.default.yml` to disable sshfs.  You may
wish to reenable it by setting `share_lib: true` (as in the default config).

### Ports

Vagrant allows port translation between those inside its boxes and ports on the
host system.  In particular, the Zimagi system utilizes PostgreSQL, Redis, and
an HTTP server (Django) as part of its design.  These conventionally use ports
5432, 6379, and 8000, respectively.  The default config maps these guest ports
to the same numbered host ports.  

However, since each of these services are relatively likely to be services you
run on your host machine if you are a developer, we have mapped the standard
guest ports to a number one higher in the `vagrant/config.yml` settings.  If
you know these services are not running on your particular machine, you may
find it more intuitive to restore ports to an identity mapping.

You can check whether ports are being used on a Unix-like system using, e.g:

```bash
% sudo lsof -i :5432
COMMAND   PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
postgres 1350 postgres    3u  IPv6  38714      0t0  TCP localhost:postgresql (LISTEN)
postgres 1350 postgres    4u  IPv4  38715      0t0  TCP localhost:postgresql (LISTEN)
```

You *do* need to run `lsof` as a superuser, or information will be silently not
reported.

### Recovery

If you attempt to launch Vargrant unsucessfully, the partially started machine
tends to wind up in an unstable state.  Merely installing a dependency or
fixing a configuration will not necesarily allow you to run `vagrant up`
successfully.

To fully start again, you should try:

```
vagrant destroy -f
rm -rf .vagrant
# If under VirtualBox
VBoxManage unregistervm zimagi
vagrant up
```

You may not need all those steps, but performing all of them should be thorough
in removing corrupted artifacts.


