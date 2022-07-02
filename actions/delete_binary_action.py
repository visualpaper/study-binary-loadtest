
class DeleteBinaryAction():
    API_PATH = "/rest/deleteBinary/{id}"
    def __init__(self, client):
        self._client = client

    def call(self, id):
        return self._client.delete(
            self.API_PATH.format(id=id),
            catch_response=True,
            name=self.API_PATH
        )
