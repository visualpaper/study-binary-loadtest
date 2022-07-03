class PostBinaryAction:
    API_PATH = "/rest/postBinary"
    APPLICATION_OCTET_STREAM_CONTENT_TYPE_HEADER = {
        "content-type": "application/octet-stream"
    }

    def __init__(self, client):
        self._client = client

    def call(self, payload):
        return self._client.post(
            self.API_PATH,
            data=payload,
            headers=self.APPLICATION_OCTET_STREAM_CONTENT_TYPE_HEADER,
            catch_response=True,
            name=self.API_PATH,
        )
