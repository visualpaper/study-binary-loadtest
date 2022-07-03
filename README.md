# study-binary-loadtest

## Versions

* python 3.8.1
* poerty 1.1.13

<br><br>

## Setup

- curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -  
  ※ Poetry の bin ディレクトリを手作業で path に追加するかしてください。  
  ※ Unixでは $HOME/.poetry/bin で、Windowsでは %USERPROFILE%\.poetry\bin です。

- poetry new xxxx  
  ※ ひな形が必要ない場合、poetry init で pyproject.toml のみ作成する。  
  ※ poetry はデフォルトでパッケージごとに仮想環境が作成される。  
     後続コマンドでは仮想環境上で実施されるので、venv と競合する場合 `python -m pip uninstall virtualenv` で venv を uninstall すること。

- poetry config virtualenvs.in-project true  
  ※ vscode との連携都合、仮想環境作成場所をフォルダ直下にします。

- poetry add locust==2.10.1
- poetry add -D black
- poetry add -D flake8
- poetry add -D taskipy
- poetry install

<br><br>

## VS Code Setup

### formatter

* black  
  ※ PEP8 準拠していない場合など自動修正してくれるようになる。

```
  "python.formatting.provider": "black",
  "editor.formatOnSave": true, // 保存時に自動で成形するフラグ、好みで false にしてください。
```

### linter

* flake8

```
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  // 設定が必要な場合 toml に記載し、flake8 exe ファイルパスを指定してください。
  "python.linting.flake8Path": ".venv/Scripts/flake8"
```

※ PEP8 準拠していない場合など警告が出るようになる。

<br><br>

## Build

- poetry run task format
- poetry run task lint
- poetry run locust --host=http://localhost:8080  
  ※ デフォルトでは locustfile.py が利用されます。  
  ※ ファイル名を指定する場合は `locust -f locust_files/my_locust_file.py --host=http://localhost:8080` のように指定してください。

<br><br>

## CI

* Github Action で ECR に登録するまで  
  ※ 本来であれば https://zenn.dev/hukurouo/articles/github-actions-build-ecr に乗っ取り OIDC でやるべき。  
  ※ 自 AWS でなく、リポジトリ名を晒したくないので、IAM ユーザの Credentials を以下設定している。
     > Settings > Secrets > Actions > AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_ECR_REPO_NAME

<br><br>

## locust メモ

* http client は requests がベース
* 2xx/3xx 系の場合、catch_response=True でなければデフォルトで OK と記録される。

<br><br>

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

```
> watch -d -n 1 "netstat -alpn | grep -E ':(80|443) ' | awk {'print $5'} | sed -e 's/\:[^.]*$//' | sort | uniq -c"
```

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
