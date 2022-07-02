from locust import SequentialTaskSet, task

from actions.request_support import RequestSupport
from actions.get_rest_action import GetRestAction

class Scenario1SubTaskSet(SequentialTaskSet):

    def on_start(self):
        self._action = GetRestAction(self.client)

    @task
    def call(self):
        with self._action.call() as response:
            RequestSupport.default_handle(response)
    #@task
    #def end(self):
    #    self.interrupt()
