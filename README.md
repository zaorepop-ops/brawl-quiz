# ブロスタ キャラクター当てクイズ（Django）

Brawl Stars のキャラクター画像を見て、日本語名の4択から当てるクイズです。
サーバー側でロースター取得・出題・採点を管理します。

> **注意:** GitHub Pages では Django をホストできません。
> 現状はローカル（または任意の WSGI/ASGI サーバー）で動かしてください。
> 旧静的版は [`legacy_static/`](./legacy_static/) に残してあります。

## 必要環境

- Python 3.10+（3.12 / 3.13 推奨）
- インターネット接続（起動時・キャッシュ更新時に [BrawlAPI](https://api.brawlapi.com/v1/brawlers) へアクセス）

## セットアップ（ローカル）

```bash
cd /path/to/.github.io   # このリポジトリ
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

ブラウザで http://127.0.0.1:8000/ を開いてください。

## アーキテクチャ概要

- `config/` … Django プロジェクト設定
- `quiz/` … クイズアプリ
  - `characters_config.py` … 日本語名オーバーライド / 除外 / 追加キャラ（旧 `characters.js`）
  - `services.py` … BrawlAPI 取得・メモリキャッシュ・出題ロジック
  - セッションに正解・スコア・出題デッキを保持
  - JSON API: `/api/start/`, `/api/answer/`, `/api/next/`, `/api/status/`
  - フロントは `quiz/static/quiz/quiz.js` が API を呼び、UI は従来どおり日本語

## 旧静的サイト

`legacy_static/` に以前の `index.html` / `script.js` / `characters.js` / `styles.css` を退避しています。
GitHub Pages 向けの静的デプロイが必要な場合はそちらを参照してください。
