from django.test import tag

from tests.sdk_python.base import BaseTest

import time
import zimagi


class ScheduleBaseTest(BaseTest):

    def _test_schedule_exec(self, wait_minutes, **filters):
        reference_name = filters['config__task_fields__text__icontains']
        allowed_time = (wait_minutes * 60)

        self.command.data("Scheduled commands", str(self.data_api.json('scheduled_task', task = 'zimagi.command.exec')))

        start_time = time.time()
        current_time = start_time

        filters['refresh'] = True

        while (current_time - start_time) < allowed_time:
            num_results = self.data_api.count('log', **filters)
            if num_results:
                self.command.success("Found {} results for {} schedule at {}".format(
                    num_results,
                    reference_name,
                    zimagi.time.now_string
                ))
                break

            self.command.sleep(5)
            current_time = time.time()
            self.command.info("Checking results for {} schedule at {}".format(
                reference_name,
                zimagi.time.now_string
            ))

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
        self.command.data("Results for {} schedule".format(reference_name), str(results))
        self.assertGreaterEqual(num_results, 1)
        self.assertGreaterEqual(len(results), num_results)


@tag('init', 'schedule')
class ScheduleIntervalTest(ScheduleBaseTest):

    @tag('schedule_interval')
    def test_interval_schedule(self):
        start_time = zimagi.time.now_string

        self.command.notice("Starting interval schedule at {}".format(start_time))
        self.command_api.run_task('core', 'echo',
            config = {
                'text': 'Hello interval!'
            },
            schedule = '1M'
        )
        self._test_schedule_exec(5,
            command = 'task',
            config__task_fields__text__icontains = 'interval',
            schedule__isnull = False,
            created__gt = start_time
        )


# @tag('init', 'schedule')
# class ScheduleCrontabTest(ScheduleBaseTest):

#     @tag('schedule_crontab')
#     def test_crontab_schedule(self):
#         self.command.sleep(4)

#         start_time = zimagi.time.now_string

#         self.command.notice("Starting crontab schedule at {}".format(start_time))
#         self.command_api.run_task('core', 'echo',
#             config = {
#                 'text': 'Hello crontab!'
#             },
#             schedule = '*/1 * * * *'
#         )
#         self._test_schedule_exec(5,
#             command = 'task',
#             config__task_fields__text__icontains = 'crontab',
#             schedule__isnull = False,
#             created__gt = start_time
#         )


# @tag('init', 'schedule')
# class ScheduleDatetimeTest(ScheduleBaseTest):

#     @tag('schedule_datetime')
#     def test_datetime_schedule(self):
#         self.command.sleep(2)

#         start_time = zimagi.time.now
#         event_time = zimagi.time.shift(start_time,
#             units = 2,
#             unit_type = 'minutes',
#             to_string = True
#         )

#         self.command.notice("Starting datetime schedule at {}".format(start_time))
#         self.command_api.run_task('core', 'echo',
#             config = {
#                 'text': 'Hello datetime!'
#             },
#             schedule = event_time
#         )
#         self._test_schedule_exec(5,
#             command = 'task',
#             config__task_fields__text__icontains = 'datetime',
#             schedule__isnull = False,
#             created__gt = zimagi.time.to_string(start_time)
#         )
