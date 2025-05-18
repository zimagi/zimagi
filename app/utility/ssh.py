import os
import random
import string
from io import StringIO
from os import path

import paramiko
from cryptography.hazmat.primitives import serialization


class SSH:
    @classmethod
    def create_keypair(cls):
        return cls.create_ecdsa_keypair()

    @classmethod
    def create_rsa_keypair(cls):
        key = paramiko.RSAKey.generate(4096)
        private_str = StringIO()
        key.write_private_key(private_str)
        return (private_str.getvalue(), f"ssh-rsa {key.get_base64()}")

    @classmethod
    def create_ecdsa_keypair(cls):
        key = paramiko.ECDSAKey.generate(bits=521)
        private_str = StringIO()
        key.write_private_key(private_str)

        public_key = key.verifying_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH, format=serialization.PublicFormat.OpenSSH
        ).decode("utf-8")
        return (private_str.getvalue(), public_key)

    @classmethod
    def create_password(cls, length=32):
        chars = string.ascii_lowercase + string.digits
        return "".join(random.SystemRandom().choice(chars) for _ in range(length))

    def __init__(self, hostname, username, password, key=None, callback=None, timeout=30, port=22, env=None):
        if not env:
            env = {}

        self.client = None
        self.sftp = None
        self.exec_wrapper = None
        self.exec_wrapper = None
        self.callback = None

        self.env = env
        self.hostname = hostname
        self.port = port
        self.timeout = timeout

        if hostname.find(":") >= 0:
            hostname, portstr = hostname.split(":")
            self.hostname = hostname
            self.port = int(portstr)

        self.username = username
        self.password = password
        self.key = None

        if key:
            self.key = paramiko.RSAKey.from_private_key(StringIO(key))

        self.connect()
        self.exec("id")
        self.callback = callback

    def __del__(self):
        self.close()

    def wrap_file(self, callback):
        self.file_wrapper = callback

    def wrap_exec(self, callback):
        self.exec_wrapper = callback

    def connect(self):
        if self.client:
            self.close()

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.key:
            try:
                self.client.connect(
                    self.hostname,
                    self.port,
                    self.username,
                    pkey=self.key,
                    look_for_keys=False,
                    allow_agent=False,
                    timeout=self.timeout,
                )
            except Exception as e:
                if self.password:
                    self.client.connect(self.hostname, self.port, self.username, self.password, timeout=self.timeout)
                else:
                    raise e
        else:
            self.client.connect(self.hostname, self.port, self.username, self.password, timeout=self.timeout)

        self.sftp = self.client.open_sftp()

    def close(self):
        try:
            self.client.close()
            self.sftp.close()
        except Exception:
            pass

    def download(self, remote_file, local_file, mode=None):
        def callback(remote_file, local_file, mode):
            tmp_file = f"/tmp/dl.{random.randint(1, 1000001)}.zimagi"

            if path.isdir(local_file):
                remote_file_name = path.basename(remote_file)
                local_file = f"{local_file}/{remote_file_name}"

            # Since we can't use sudo and sftp together we need to
            # jump through some hoops
            self.sudo(f"cp -f {remote_file} {tmp_file}")
            self.sudo(f"chmod 644 {tmp_file}")

            self.sftp.get(tmp_file, local_file)
            self.sudo(f"rm -f {tmp_file}")

            if mode:
                os.chmod(local_file, oct(int(str(mode), 8)))

        if self.file_wrapper and callable(self.file_wrapper):
            return self.file_wrapper(self, self._handle_file, callback, remote_file, local_file, mode)
        return self._handle_file(callback, remote_file, local_file, mode)

    def upload(self, local_file, remote_file, mode=None, owner=None, group=None):
        def callback(local_file, remote_file, mode, owner, group):
            tmp_file = f"/tmp/ul.{random.randint(1, 1000001)}.zimagi"

            if path.isdir(remote_file):
                local_file_name = path.basename(local_file)
                remote_file = f"{remote_file}/{local_file_name}"

            # Since we can't use sudo and sftp together we need to
            # jump through some hoops
            self.sftp.put(local_file, tmp_file)
            self.sudo(f"cp -f {tmp_file} {remote_file}")
            self.sudo(f"rm -f {tmp_file}")

            if owner or group:
                if owner and group:
                    owner = f"{owner}:{group}"
                elif group:
                    owner = f":{group}"

                self.sudo(f"chown {owner} {remote_file}")

            if mode:
                self.sudo(f"chmod {oct(int(str(mode), 8))[2:]} {remote_file}")

        if self.file_wrapper and callable(self.file_wrapper):
            return self.file_wrapper(self, self._handle_file, callback, local_file, remote_file, mode, owner, group)
        return self._handle_file(callback, local_file, remote_file, mode, owner, group)

    def _handle_file(self, callback, *args):
        callback(*args)

    def exec(self, command, *args, **options):
        if self.exec_wrapper and callable(self.exec_wrapper):
            return self.exec_wrapper(self, self._exec, command, args, options)
        return self._exec(command, args, options)

    def sudo(self, command, *args, **options):
        command = f"sudo -E -S -p '' {command}"
        return self.exec(command, *args, **options)

    def _exec(self, command, args, options):
        status = -1

        separator = options.pop("_separator", " ")
        command = self._format_command(command, args, options, separator)
        is_sudo = command.startswith("sudo")

        env = []
        for variable, value in self.env.items():
            env.append(f"{variable}='{value}'")
        env = " ".join(env) + " "

        stdin, stdout, stderr = self.client.exec_command(f"{env}{command}".strip())

        if is_sudo:
            if self.password:
                stdin.write(self.password + "\n")
                stdin.flush()

        if self.callback and callable(self.callback):
            self.callback(self, stdin, stdout, stderr)

        return stdout.channel.recv_exit_status()

    def _format_command(self, command, args, options, separator=" "):
        components = [command]

        for arg in args:
            if arg[0] == "-":
                components.append(arg)
            else:
                components.append(f"{arg}")

        for key, value in options.items():
            components.append(f"{key}{separator}{value}")

        return " ".join(components)
