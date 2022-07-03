from locust import HttpUser, TaskSet, constant_pacing

from apis.scenario1.scenario import Scenario1SubTaskSet
from apis.scenario2.scenario import Scenario2SubTaskSet
from apis.scenario3.scenario import Scenario3SubTaskSet


class MainScenario(TaskSet):
    tasks = {Scenario1SubTaskSet: 1, Scenario2SubTaskSet: 1, Scenario3SubTaskSet: 1}

    def on_start(self):
        self.client.verify = False

class HttpLocustUser(HttpUser):
    tasks = [MainScenario]

    # Tast 実行待ち時間 (x 秒ごとに実行)
    wait_time = constant_pacing(1)
