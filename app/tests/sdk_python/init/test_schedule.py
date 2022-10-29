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
                'text': 'Hello interval!'
            },
            schedule = '1M'
        )
        self._test_schedule_exec(3, 1,
            command = 'task',
            config__task_fields__text__icontains = 'interval',
            schedule__isnull = False,
            created__gt = start_time
        )

    def test_crontab_schedule(self):
        start_time = zimagi.time.now_string

        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello crontab!'
            },
            schedule = '*/1 * * * *'
        )
        self._test_schedule_exec(3, 1,
            command = 'task',
            config__task_fields__text__icontains = 'crontab',
            schedule__isnull = False,
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
                'text': 'Hello datetime!'
            },
            schedule = event_time
        )
        self._test_schedule_exec(3, 1,
            command = 'task',
            config__task_fields__text__icontains = 'datetime',
            schedule__isnull = False,
            created__gt = zimagi.time.to_string(start_time)
        )


    def _test_schedule_exec(self, wait_minutes, executions, **filters):
        self.command.sleep(wait_minutes * 60)

        num_results = self.data_api.count('log', **filters)
        results = self.data_api.json('log', **{
            'fields': [
                'command',
                'user=user__name',
                'worker',
                'schedule=schedule__name',
                'interval=schedule__interval__name',
                'crontab=schedule__crontab__name',
                'datetime=schedule__clocked__name',
                'created',
                'text=config__task_fields__text'
            ],
            **filters
        })
        self.assertGreaterEqual(num_results, executions)
        self.assertGreaterEqual(len(results), num_results)
