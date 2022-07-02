

class GetRestAction():
    API_PATH = "/rest/get"

    def __init__(self, client):
        self._client = client

    def call(self):
        return self._client.get(
            self.API_PATH,
            catch_response=True,
            name=self.API_PATH
        )
