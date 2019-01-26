# JITAI


## ユーザ追加の方法
※研究室のサーバーのパスで記載しています. 
※サーバーのアカウント`jitai`はファイル送信権限がありません.

該当ファイル: `/home/jitai/research/jitai/data/user_list_mamalog.csv`
- ローカルPCで作業する場合

    1. 該当ファイルをローカルPCにダウンロードします.
    ```
    scp root@10.131.63.6:/home/jitai/research/jitai/data/user_list_mamalog.csv [ローカルパス]
    ```
    2. 追記後、サーバーにアップロードします.
    ```
    scp [ローカルパス]/user_list_mamalog.csv root@10.131.63.6:/home/jitai/research/jitai/data/
    ```
    
- サーバー上で編集する場合 
    `vim /home/jitai/research/jitai/data/user_list_mamalog.csv`と押して追記します.
    
プログラムは都度csvファイルを見に行くので、プログラムをストップする必要はありません.

## cronについて
- cronファイルの場所
- ストップ
- リスタート

#### cronファイルの場所
`/etc/cron.d/test_cron`

#### ストップ
`systemctl stop crond`と打つことで止まります.
`systemctl status crond`と打って3行目に`Active: inactive`と書かれているのを確認します.

#### リスタート
`systemctl stop crond`と打つことで再開します.
cronファイルを編集したときは必ずリスタートをしてください.
`systemctl status crond`と打って3行目に`Active: active (running)`と書かれているのを確認します.


### 介入時パラメータ設定ファイルの書き方
ファイル群は`jitai/yaml`というファイルに入っています.
基本的には他のyaml設定ファイルを参考にしてください. 
python実行コマンドは
```
python tasks/setting.py [yaml設定ファイル名]
```

エラーが出る場合は小池に設定ファイルと共にメールください.

## 環境構築

#### python仮想環境
python仮想環境を作ってください.
おすすめはanacondaです.

#### ライブラリインストール
仮想環境に入った状態で、以下のコマンドを実行してください.

```pip install -r requirements.txt```
