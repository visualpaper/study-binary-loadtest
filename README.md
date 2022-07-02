# study-binary-loadtest

## Development

- python -m venv venv
- source venv/Scripts/activate  
  ※ Windows の場合 venv\Scripts\Activate.ps1

- (venv) python -m pip install --upgrade pip
- (venv) pip install -r dev-requirements.txt

<br>

※ vccode 上で path が通らず `Import "***" could not be resolved Pylance(reportMissingImports)` が出る時は↓

<br><br>

## ローカル環境での試験

```
locust --host=http://localhost:8080
※ デフォルトでは locustfile.py が利用されます。

locust -f locust_files/my_locust_file.py --host=http://localhost:8080
※ ファイル名を指定する場合は↑のように指定してください。
```

<br><br>

```
1. 該当ライブラリの場所を確認
   $ (venv) find -name "airflow"
   ./venv/Lib/site-packages/locust

2. vscode/settings.json に追記
    "python.analysis.extraPaths" : [
        "./venv/Lib/site-packages/"
    ],
```

<br><br>

## locust メモ

```
class SubTaskSet(TaskSequence):

    # sequece 番号順に実施される。
    # ※ task にも order というものがある。
    @seq_task(1)
    def my_task(self):
        self.client.get("/app/rest/get")

    # SubTask の場合、親 Task に終了したことを通知しなければならない。
    # ※ しなかった場合、この SubTask のみずっと実施することになってしまう。
    @seq_task(2)
    def on_stop(self):
        self.interrupt()

## Binary 転送 SubTask
## ※ ランダムで複数ファイルを転送している。
class BinarySubTaskSet(TaskSequence):
    UPLOAD_FILES_PATH = Path(__file__).parent / "uploadFiles"
    UPLOAD_FILENAMES = ["001.jpg", "002.jpg"]

    APPLICATION_OCTET_STREAM_CONTENT_TYPE_HEADER = {"content-type": "application/octet-stream"}

    @seq_task(1)
    def my_task(self):
        path = self.UPLOAD_FILES_PATH / self.UPLOAD_FILENAMES[random.randrange(2)]

        with open(path.resolve(), 'rb') as upload_file:
            self.client.post(
                "/app/rest/postBinary",
                data=upload_file,
                headers=self.APPLICATION_OCTET_STREAM_CONTENT_TYPE_HEADER
            )

    @seq_task(2)
    def on_stop(self):
        self.interrupt()

class SampleScenario(TaskSet):

    APPLICATION_JSON_CONTENT_TYPE_HEADER = {"content-type": "application/json"}

    # 別の TaskSet を含むこともできる。
    # ※ nest task も使ってみたものの、イマイチうまくいかなかったのでこちらの方法をとっている。
    # ※ {class: weight} の指定をしている。order などの指定も可能。
    tasks = {
        SubTaskSet: 5,
        BinarySubTaskSet: 5
    }

    def on_start(self):
        self._post_id = 1
        self._post_value = "sample222"

    def on_stop(self):
        pass

    @task(1)
    def get(self):
        with self.client.get("/app/rest/get", catch_response=True) as response:
            # デフォルトで 400/500 系は failure として報告されるが
            # ↓のように、特定の場合は success として看做すようにすることもできる。
            if response.status_code == 404:
                response.success()

    # 重みづけ。 get task の 10 倍の実行率となる。
    # ※ 実行率な点に注意。必ず 10 回数される度に 1 回 get が走るわけではなかった。
    # ※ task 内に指定しなければ 1 と看做されるかも？明記されてはなかった。
    @task(10)
    def post(self):
        payload = {
            "id": self._post_id,
            "value": self._post_value
        }

        self.client.post(
            "/app/rest/post",
            data=json.dumps(payload),
            headers=self.APPLICATION_JSON_CONTENT_TYPE_HEADER
        )

class HttpLocustUser(HttpLocust):
    task_set = SampleScenario

    # Tast 実行待ち時間 (min, max)
    min_wait = 500
    max_wait = 1000
```

<br>

# メトリクス
## CPU コマンド
* top
> top -d1
※ ロードアベレージが低くて RPS が出ない場合は I/O、高くて RPS が出ない場合は CPU / メモリを疑う
※ 1 キーで CPU コア別の利用率がわかる
※ スワップの発生頻度も、メモリ使用率もわかる。
※ sleeping が多い場合は wchan (y キー押下) で内容がわかる

* netstat
> watch -d -n 1 "netstat -s"
※ segments retransmited (セグメント再送出) と segments send out (セグメントの送出) の値を比較し、セグメント再送出が高ければネットワークの信頼性が低い
※ connections established (ESTABLE コネクション数) で、リクエストで受け付けているコネクション数が見える

> watch -d -n 1 "netstat -i"
※ DRP と OVR (ドロップとオーバーラン) が多い場合は飽和の兆候があるが、ここも問題ない。

* 対象サーバへ届いているコネクション数確認
> watch -d -n 1 "netstat -alpn | grep -E ':(80|443) ' | awk {'print $5'} | sed -e 's/\:[^.]*$//' | sort | uniq -c"

* ネットワーク送信量
> watch -d -n 1 "cat /proc/net/dev"
awk '$1=="eth0:\" {printf \"rx: %fMB tx: %fMB\n\", $2/1024/1024, $10/1024/1024}\' < /proc/net/dev"

※ Reviece が受信、Transmit が送信。転送バイト数がわかる。
※ 以下 shell で秒間で確認可能

```
while :
do
  A=`date ; awk '$1=="eth0:" {printf "rx: %fMB tx: %fMB\n", $2/1024/1024, $10/1024/1024}' < /proc/net/dev`
  echo $A
  sleep 1
done
```

## Apache

```
[スレッド数]
watch -n 1 'curl -sS http://localhost/server-status | head -n 30'
※ スレッド数以外は参考にしないほうが良い。サーバ稼働中の間の集計結果が表示されているので微妙に使えない

[各種リミット]
ps aux |grep httpd
cat /proc/xxx/limit

```

## Tomcat

```
[スレッド数]
ps aux | grep java
cd /proc/xxx/task
watch -n 1 'ls -l|wc -l'

[各種リミット]
ps aux | grep java
cat /proc/xxx/limit

※ 変更するには、LimitNOFILE=8192 を [Service] 配下に記載してあげる必要がある。
   (https://www.malasuk.com/linux/increase-open-file-limit-tomcat-centos-7/)
```

## DataDog

```
system.cpu.user: CPUがユーザー空間プロセスの実行に費やした時間の割合(パーセント)
system.cpu.system: CPUがカーネルの実行に費やした時間の割合(パーセント)
system.mem.used: 使用中のRAMの量(バイト)
system.mem.free: 空きRAMの量(バイト)
※ https://docs.datadoghq.com/ja/integrations/system/

system.disk.used: 使用中のディスク容量(バイト)
system.disk.free: 空きディスク容量(バイト)
※ https://docs.datadoghq.com/ja/integrations/disk/

system.net.bytes_rcvd: 1秒間にデバイスで受信されたバイト数
system.net.bytes_sent: 1秒あたりにデバイスから送信されたバイト数
※ https://docs.datadoghq.com/ja/integrations/disk/

jvm.heap_memory: 使用されたJavaヒープメモリの合計(バイト)
jvm.non_heap_memory: 使用されているJava非ヒープメモリの合計(バイト)
jvm.gc.major_collection_count: 発生した主要なガベージコレクションの数
jvm.gc.minor_collection_count: 発生したマイナーガベージコレクションの数
※ https://docs.datadoghq.com/ja/tracing/runtime_metrics/java/

tomcat.thread.busy: 使用中のスレッドの数
tomcat.thread.count: スレッドプールによって管理されるスレッドの数
※ https://docs.datadoghq.com/ja/integrations/tomcat/

apache.performance.busy_workers: リクエストを処理するスレッド数
apache.performance.idle_workers: アイドル状態のスレッド数
※ https://docs.datadoghq.com/ja/integrations/apache/
```

## ThreadDump/HeapDump

```
ps aux | grep java
-> 1
※ コンテナに入った上で実施。

$JAVA_HOME/bin/jps
-> 17 Jps
※ jre のみ環境では jstack や jps がないので、sdk を含むものを利用する必要がある 9.0.44-jdk8-openjdk-buster に変えて実施してみた。

$JAVA_HOME/bin/jstack 1 > threaddump.txt
※ -F を付けると ArrayIndexOutOfBounds が発生した。

$JAVA_HOME/bin/jmap -dump:format=b,file=heapdump.map 1
※ 長いと 10 分ぐらいかかる。
※ かなり重いファイルなので disc 要確保 + 移動時には圧縮必須

※ 共に実施時間中 RPS が落ちたので、本番環境での実施は要注意
```
