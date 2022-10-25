from tests.sdk_python.base import BaseTest

import zimagi


class ScheduleTest(BaseTest):

    @classmethod
    def _message_callback(cls, message):
        pass


    def test_interval_schedule(self):
        self._test_schedule_exec('1M', 5, 4)

    def test_crontab_schedule(self):
        self._test_schedule_exec('*/1 * * * *', 5, 4)

    def test_datetime_schedule(self):
        event_time = zimagi.time.shift(zimagi.time.now,
            units = 2,
            unit_type = 'minutes',
            to_string = True
        )
        self._test_schedule_exec(event_time, 5, 1)


    def _test_schedule_exec(self, schedule_ref, wait_minutes, executions):
        start_time = zimagi.time.now_string

        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello world!'
            },
            schedule = schedule_ref
        )
        self.command.sleep(wait_minutes * 60)

        filters = {
            'command': 'task',
            'scheduled': True,
            'created__gt': start_time
        }
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
