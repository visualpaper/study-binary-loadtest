import json

class RequestSupport:

    @staticmethod
    def default_handle(response):
        """
        catch_response=True オプションを付けている場合に with 構文配下で利用してください。
        > with self._action.call() as response:
        >   RequestSupport.default_handle(response)
        ※ LocustResponse では、with 構文を閉じた際にデフォルトで success 状態として記録されます。
           その後、もう一度 with 構文で開いた場合、二重に記録される点に注意してください。
        """

        if hasattr(response, 'error') and response.error:
            try:
                response.failure(
                    u'error:%s, body: %s '
                    % (response.error, json.loads(response.content.decode('utf8')))
                )
            except:
                response.failure(response.text)
            raise response.error

        return response
