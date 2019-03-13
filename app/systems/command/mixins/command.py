from utility import ssh, shell

import os
import subprocess
import threading


class ExecMixin(object):

    def sh(self, command_args, input = None, display = True, env = {}, cwd = None):
        return shell.Shell.exec(command_args,
            input = input,
            display = display,
            env = env,
            cwd = cwd,
            callback = self._sh_callback
        )

    def _sh_callback(self, process, display = True):
        stdout = []
        stderr = []

        def stream_stdout():
            for line in process.stdout:
                line = line.decode('utf-8').strip('\n')
                stdout.append(line)

                if display:
                    self.info(line)

        def stream_stderr():
            for line in process.stderr:
                line = line.decode('utf-8').strip('\n')

                if not line.startswith('[sudo]'):
                    stderr.append(line)
                    self.warning(line)

        thrd_out = threading.Thread(target = stream_stdout)
        thrd_out.start()

        thrd_err = threading.Thread(target = stream_stderr)
        thrd_err.start()

        thrd_out.join()
        thrd_err.join()

        return (stdout, stderr)


    def ssh(self, hostname, username, password = None, key = None, timeout = 10):
        try:
            conn = ssh.SSH(hostname, username, password,
                key = key,
                callback = self._ssh_callback,
                timeout = timeout
            )
            conn.wrap_exec(self._ssh_exec)
            conn.wrap_file(self._ssh_file)

        except Exception as e:
            self.error("SSH connection to {} failed: {}".format(hostname, e))

        return conn

    def _ssh_exec(self, ssh, executer, command, args, options):
        id_prefix = "[{}]".format(ssh.hostname)

        try:
            return executer(command, args, options)
        except Exception as e:
            self.error("SSH {} execution failed: {}".format(command, e), prefix = id_prefix)

    def _ssh_file(self, ssh, executer, callback, *args):
        id_prefix = "[{}]".format(ssh.hostname)

        try:
            executer(callback, *args)
        except Exception as e:
            self.error("SFTP transfer failed: {}".format(e), prefix = id_prefix)

    def _ssh_callback(self, ssh, stdin, stdout, stderr):
        id_prefix = "[{}]".format(ssh.hostname)

        def stream_stdout():
            for line in stdout:
                self.info(line.strip('\n'), prefix = id_prefix)

        def stream_stderr():
            for line in stderr:
                if not line.startswith('[sudo]'):
                    self.warning(line.strip('\n'), prefix = id_prefix)

        thrd_out = threading.Thread(target = stream_stdout)
        thrd_out.start()

        thrd_err = threading.Thread(target = stream_stderr)
        thrd_err.start()

        thrd_out.join()
        thrd_err.join()
