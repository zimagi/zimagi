from django.conf import settings
from queue import Full, Empty

from systems.commands import exec
from utility.data import dump_json, load_json
from utility.parallel import Parallel
from utility.display import format_exception_info

import multiprocessing
import time
import re
import logging


logger = logging.getLogger(__name__)


class AgentCommand(exec.ExecCommand):

    process_queues = [ 'default' ]
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
        process_manager = multiprocessing.Manager()
        process_queues = process_manager.dict()
        for queue in self.process_queues:
            process_queues[queue] = process_manager.Queue()

        def exec_process(name):
            def run_loop(queues):
                self._process_queues = queues

                self.exec()
                self.exec_loop(name, getattr(self, name))

            process = multiprocessing.Process(
                name = name,
                daemon = True,
                target = run_loop,
                args = [ process_queues ]
            )
            self.process_map[name] = process

            process.start()
            process.join()

            if process.exitcode != 0:
                self.error("Process {} failed".format(name))

        if self.processes:
            Parallel.list(
                self.processes,
                exec_process,
                thread_count = len(self.processes),
                disable_parallel = False
            )
        else:
            self.exec_loop('main', self.exec)


    def exec_init(self, name):
        # Implement in subclass if needed
        pass

    def exec_exit(self, name, success, error):
        # Implement in subclass if needed
        pass

    def exec_loop(self, name, exec_callback):
        try:
            self.exec_init(name)
            self.run_exec_loop(name, exec_callback,
                terminate_callback = self.terminate_agent,
                pause = self.pause
            )
            self.exec_exit(name, True, None)

        except Exception as e:
            self.error(str(e),
                prefix = name,
                traceback = format_exception_info(),
                terminate = False
            )
            self.exec_exit(name, False, e)

    def terminate_agent(self):
        return False


    def push(self, data, name = 'default', block = True, timeout = None):
        queue = self._process_queues.get(name, None)
        if not queue:
            self.error("Process queue {} not defined".format(name))

        try:
            queue.put(dump_json(data),
                block = block,
                timeout = timeout
            )
            return True
        except Full:
            return False

    def pull(self, name = 'default', timeout = 0, block_sec = 10, terminate_callback = None):
        queue = self._process_queues.get(name, None)
        if not queue:
            self.error("Process queue {} not defined".format(name))

        start_time = time.time()
        current_time = start_time

        def _default_terminate_callback(channel):
            return False

        if terminate_callback is None or not callable(terminate_callback):
            terminate_callback = _default_terminate_callback

        while not terminate_callback(name):
            try:
                data = load_json(queue.get(
                    block = True,
                    timeout = block_sec
                ))
                start_time = time.time()

            except Empty:
                data = None

            if data is not None:
                yield data

            current_time = time.time()

            if timeout and ((current_time - start_time) > timeout):
                break


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
