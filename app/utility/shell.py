from utility import ssh

import os
import subprocess
import threading


class Shell(object):

    @classmethod
    def exec(cls, command_args, input = None, display = True, env = {}, cwd = None, callback = None):
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
                callback(process, display = display)

            process.wait()
        finally:
            process.terminate()

        return process.returncode == 0

    @classmethod
    def capture(cls, command_args, input = None, env = {}, cwd = None):
        output = []

        def process(process, display):
            for line in process.stdout:
                line = line.decode('utf-8').strip('\n')
                output.append(line)

        cls.exec(command_args,
            input = input,
            display = False,
            env = env,
            cwd = cwd,
            callback = process
        )
        return "\n".join(output).strip()
