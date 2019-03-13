from utility import ssh

import os
import subprocess
import threading


class Shell(object):

    @classmethod
    def exec(cls, command_args, input = None, display = True, env = {}, cwd = None, callback = None):
        stdout = None
        stderr = None
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
            if callback and callable(callback):
                stdout, stderr = callback(process, display = display)
            process.wait()
        finally:
            process.terminate()

        return (process.returncode == 0, stdout, stderr)
