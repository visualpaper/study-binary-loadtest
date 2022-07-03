import random

from actions.request_support import RequestSupport
from pathlib import Path
from locust import SequentialTaskSet, task

from actions.post_binary_action import PostBinaryAction


class Scenario2SubTaskSet(SequentialTaskSet):

    UPLOAD_FILES_PATH = Path(__file__).parent.parent.parent / "datas" / "uploadFiles"
    UPLOAD_FILENAMES = ["003"]

    def on_start(self):
        self._action = PostBinaryAction(self.client)

    @task
    def call(self):
        path = self.UPLOAD_FILES_PATH / self.UPLOAD_FILENAMES[random.randrange(1)]

        with open(path.resolve(), "rb") as upload_file:
            with self._action.call(upload_file) as response:
                RequestSupport.default_handle(response)

    @task
    def end(self):
        self.interrupt()
