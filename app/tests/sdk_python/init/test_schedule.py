from tests.sdk_python.base import BaseTest

import zimagi


class ScheduleTest(BaseTest):

    @classmethod
    def _message_callback(cls, message):
        pass


    def test_interval_schedule(self):
        start_time = zimagi.time.now_string

        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello world!'
            },
            schedule = '1M'
        )
        self._test_schedule_exec(5, 4,
            command = 'task',
            scheduled = True,
            created__gt = start_time
        )

    def test_crontab_schedule(self):
        start_time = zimagi.time.now_string

        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello world!'
            },
            schedule = '*/1 * * * *'
        )
        self._test_schedule_exec(5, 4,
            command = 'task',
            scheduled = True,
            created__gt = start_time
        )

    def test_datetime_schedule(self):
        start_time = zimagi.time.now
        event_time = zimagi.time.shift(start_time,
            units = 2,
            unit_type = 'minutes',
            to_string = True
        )

        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello world!'
            },
            schedule = event_time
        )
        self._test_schedule_exec(5, 1,
            command = 'task',
            scheduled = True,
            created__gt = zimagi.time.to_string(start_time)
        )


    def _test_schedule_exec(self, wait_minutes, executions, **filters):
        self.command.sleep(wait_minutes * 60)

        num_results = self.data_api.count('log', **filters)
        results = self.data_api.json('log', **{
            'fields': [
                'command',
                'scheduled',
                'created'
            ],
            **filters
        })
        self.assertGreaterEqual(num_results, executions)
        self.assertEqual(num_results, len(results))
