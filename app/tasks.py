import time

from celery import shared_task

@shared_task(name='task1')
def sleeptime(total_time):
    print(f"Sleeping for {total_time} seconds")
    time.sleep(total_time)
    return "TIME COMPLETED"