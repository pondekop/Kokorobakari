# ベースイメージとしてUbuntuを使用
FROM ubuntu:latest
# 必要なツールやライブラリをインストール
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean && \
    ln -s /usr/bin/python3 /usr/bin/python
# 作業ディレクトリの設定
WORKDIR /workspace