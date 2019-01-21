from utility import ssh

import os
import subprocess
import threading


class ExecMixin(object):

    def sh(self, command_args, input = None, display = True, env = {}, cwd = None):
        shell_env = os.environ.copy()
        for variable, value in env.items():
            shell_env[variable] = value
  
        process = subprocess.Popen(command_args,
                                   bufsize = 0,
                                   env = shell_env,
                                   cwd = cwd,
                                   stdin = subprocess.PIPE,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        if input:
            if isinstance(input, (list, tuple)):
                input = "\n".join(input) + "\n"
            else:
                input = input + "\n"
            
            process.stdin.write(input)
        try:
            stdout, stderr = self._sh_callback(process, display = display)
            process.wait()
        finally:
            process.terminate()
        
        return (process.returncode == 0, stdout, stderr)

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
                    
                    if display:
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
