from django.conf import settings

from systems.commands import exec
from utility.parallel import Parallel

import billiard as multiprocessing
import re
import logging


logger = logging.getLogger(__name__)


class AgentCommand(exec.ExecCommand):

    processes = ()
    process_map = {}


    def signal_shutdown(self):
        try:
            for name, process in self.process_map.items():
                process.terminate()
                process.join()

        except Exception as error:
            logger.info("Signal shutdown for base executable command errored with: {}".format(error))

        super().signal_shutdown()


    def _exec_local_handler(self, log_key, primary = True):
        profiler_name = 'exec.agent.local.primary' if primary else 'exec.agent.local'
        notify = False

        if (primary and settings.WORKER_EXEC) or not self.set_queue_task(log_key):
            try:
                self.preprocess_handler(self.options, primary)
                try:
                    self.start_profiler(profiler_name)
                    self.run_exclusive(self.lock_id, self.repeat_exec,
                        error_on_locked = self.lock_error,
                        timeout = self.lock_timeout,
                        interval = self.lock_interval,
                        run_once = self.run_once
                    )
                finally:
                    self.stop_profiler(profiler_name)

                notify = True
            finally:
                self.postprocess_handler(self.exec_result, primary)
        return notify


    def _exec_api_handler(self, log_key):
        profiler_name = 'exec.agent.api'
        try:
            self.start_profiler(profiler_name)
            self.set_queue_task(log_key, True)
        finally:
            self.stop_profiler(profiler_name)
        return False


    def repeat_exec(self):

        def exec_process(name):

            def run_loop():
                self.exec()
                self.exec_loop(name, getattr(self, name))

            process = multiprocessing.Process(
                name = name,
                daemon = True,
                target = run_loop
            )
            self.process_map[name] = process

            process.start()
            process.join()

            if process.exitcode != 0:
                self.error("Process {} failed".format(name))

        if self.processes:
            Parallel.list(self.processes, exec_process, thread_count = len(self.processes))
        else:
            self.exec_loop('main', self.exec)


    def exec_init(self, name):
        # Implement in subclass if needed
        pass

    def exec_exit(self, name, success, error):
        # Implement in subclass if needed
        pass

    def exec_loop(self, name, exec_callback):
        success = True
        error = None

        try:
            self.exec_init(name)
            self.run_exec_loop(name, exec_callback, pause = self.pause)

        except Exception as e:
            success = False
            error = e
            raise e
        finally:
            self.exec_exit(name, success, error)


    def _check_agent_schedule(self, spec):
        current_time = self.time.components()

        if 'weeks' in spec and spec['weeks'].strip() != '*' and current_time.week not in self._expand_time_values(spec['weeks']):
            return False
        if 'weekdays' in spec and spec['weekdays'].strip() != '*' and current_time.weekday not in self._expand_time_values(spec['weekdays']):
            return False
        if 'months' in spec and spec['months'].strip() != '*' and current_time.month not in self._expand_time_values(spec['months']):
            return False
        if 'days' in spec and spec['days'].strip() != '*' and current_time.day not in self._expand_time_values(spec['days']):
            return False
        if 'hours' in spec and spec['hours'].strip() != '*' and current_time.hour not in self._expand_time_values(spec['hours']):
            return False
        if 'minutes' in spec and spec['minutes'].strip() != '*' and current_time.minute not in self._expand_time_values(spec['minutes']):
            return False
        return True

    def _expand_time_values(self, pattern):
        values = []
        for value in re.sub(r'\s+', '', pattern).split(','):
            value_range = re.match(r'^(\d+)\-(\d+)$', value)
            if value_range:
                values.extend(list(range(
                    int(value_range.group(1)),
                    (int(value_range.group(2)) + 1)
                )))
            else:
                values.append(int(value))
        return values
