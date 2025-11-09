# Render デプロイ手順（完全無料）

## 概要

Renderは完全無料でFastAPIアプリケーションをデプロイできます。無料プランでは15分間アクセスがないとスリープしますが、次回アクセス時に自動的に再起動します。

## 前提条件

- GitHubアカウント
- GitHubリポジトリ（既に作成済み: https://github.com/yoshi0323/note）

## デプロイ手順

### ステップ1: Renderアカウント作成

1. https://render.com/ にアクセス
2. 「Get Started for Free」をクリック
3. 「Sign up with GitHub」を選択
4. GitHubアカウントでログイン・認証

### ステップ2: 新しいWebサービスを作成

1. ダッシュボードで「New +」をクリック
2. 「Web Service」を選択

### ステップ3: GitHubリポジトリを接続

1. 「Connect account」をクリック（初回のみ）
2. GitHubアカウントを認証
3. リポジトリ `yoshi0323/note` を検索して選択
4. 「Connect」をクリック

### ステップ4: サービス設定

以下の設定を入力します：

| 項目 | 値 |
|------|-----|
| **Name** | `note-backend`（任意の名前） |
| **Region** | `Singapore`（最寄りのリージョン） |
| **Branch** | `main` |
| **Root Directory** | `backend` ⚠️ **重要** |
| **Runtime** | `Python 3` |
| **Python Version** | `3.11.9`（`runtime.txt`で指定済み、Renderが自動検出） |
| **Build Command** | `pip install -r requirements.txt && python -m playwright install chromium` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

### ステップ5: 環境変数の設定（オプション）

通常は不要ですが、追加のCORS設定が必要な場合：

1. 「Advanced」セクションを展開
2. 「Add Environment Variable」をクリック
3. 以下を追加:
   - **Key**: `CORS_ORIGINS`
   - **Value**: `https://note-c801b.web.app,https://note-c801b.firebaseapp.com`

**注意**: デフォルトで本番フロントエンドURLは既に許可されているため、通常は不要です。

### ステップ6: デプロイ開始

1. 「Create Web Service」をクリック
2. デプロイが開始されます（5〜10分程度）
3. 「Logs」タブで進行状況を確認

### ステップ7: URLの取得と確認

1. デプロイが完了すると、自動的にURLが生成されます
   - 例: `https://note-backend.onrender.com`
2. URLにアクセスして、`/docs`にアクセス
   - 例: `https://note-backend.onrender.com/docs`
3. FastAPIのドキュメントページが表示されれば成功です

## 無料プランの制限

- **スリープ**: 15分間アクセスがないと自動的にスリープします
- **再起動**: 次回アクセス時に自動的に再起動します（30秒〜1分程度）
- **これは無料プランの制限です**

## スリープを防ぐ方法

1. **定期的なアクセス**: 外部サービス（UptimeRobotなど）で定期的にアクセス
2. **有料プラン**: Renderの有料プランにアップグレード（月額$7〜）

## 次のステップ

バックエンドのデプロイが完了したら：

1. **フロントエンドの環境変数を設定**
   ```bash
   cd frontend
   echo REACT_APP_API_URL=https://note-backend.onrender.com > .env.production
   ```
   （`https://note-backend.onrender.com`を実際のRenderのURLに置き換えてください）

2. **フロントエンドをビルド＆デプロイ**
   ```bash
   npm run build
   cd ..
   firebase deploy --only hosting
   ```

## トラブルシューティング

### デプロイが失敗する場合

1. **ログを確認**
   - Renderダッシュボード → サービス → 「Logs」タブ
   - エラーメッセージを確認

2. **Playwrightのインストールエラー**
   - `Build Command`に`python -m playwright install chromium`が含まれているか確認

3. **ポートエラー**
   - `Start Command`で`$PORT`環境変数を使用しているか確認

### スリープ後の初回アクセスが遅い

- 無料プランの制限です
- 30秒〜1分程度で再起動します
- 定期的にアクセスするか、有料プランにアップグレードしてください

## 参考リンク

- Render公式ドキュメント: https://render.com/docs
- Render無料プラン: https://render.com/pricing

