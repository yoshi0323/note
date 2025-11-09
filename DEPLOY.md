# Firebase Hosting デプロイガイド

## 前提条件

1. Firebase CLIのインストール
```bash
npm install -g firebase-tools
```

2. Firebaseにログイン
```bash
firebase login
```

3. Firebaseプロジェクトの作成（重要）

**`note-c801b`プロジェクトが存在しない場合は、Firebaseコンソールで作成してください：**

1. Firebaseコンソールにアクセス: https://console.firebase.google.com/
2. 「プロジェクトを追加」をクリック
3. プロジェクト名を入力（例: `note-draft-system`）
4. プロジェクトIDを`note-c801b`に設定（または任意のID）
5. Hostingを有効化（プロジェクト作成後、左メニューから「Hosting」→「始める」）

4. プロジェクトを選択
```bash
# プロジェクト一覧を確認
firebase projects:list

# プロジェクトを選択
firebase use note-c801b
```

**注意:** `firebase init`は実行しないでください。既に設定ファイル（`firebase.json`、`.firebaserc`）が作成済みです。

## デプロイ手順

### 1. バックエンドの設定

バックエンドを本番環境にデプロイし、URLを取得してください。

**推奨デプロイ先（完全無料）:**

1. **Render** (https://render.com/) - **推奨**
   - 完全無料プランあり
   - 15分間アクセスがないとスリープしますが、次回アクセス時に自動的に再起動します
   - 再起動に30秒〜1分程度かかります
   - GitHub連携で簡単にデプロイ可能

2. **Fly.io** (https://fly.io/)
   - 完全無料プランあり（月間160時間まで）
   - スリープしない
   - より高度な設定が必要

3. **Replit** (https://replit.com/)
   - 完全無料プランあり
   - ブラウザベースの開発環境

**有料または期間限定無料:**
- **Railway** - 30日間のみ無料、その後有料
- **Heroku** - 有料プランのみ（2022年11月以降）

**Railwayでのデプロイ手順:**

1. Railwayにアカウント作成・ログイン（GitHubアカウントでログイン可能）
   - https://railway.app/

2. 新しいプロジェクトを作成
   - 「New Project」をクリック
   - 「Deploy from GitHub repo」を選択
   - リポジトリを選択（または「Empty Project」を選択して手動でアップロード）

3. サービスを追加
   - 「+ New」→「GitHub Repo」を選択
   - リポジトリを選択
   - ルートディレクトリを`backend`に設定

4. 環境変数を設定（オプション）
   - サービスを選択 → 「Variables」タブ
   - 必要に応じて追加:
     - `CORS_ORIGINS`: `https://note-c801b.web.app,https://note-c801b.firebaseapp.com`（カンマ区切り）

5. デプロイ設定
   - Railwayは自動的に`requirements.txt`を検出して依存関係をインストール
   - `Procfile`がある場合は自動的に使用されます
   - ポートは自動的に`$PORT`環境変数から取得されます

6. デプロイ完了後
   - 「Settings」→「Generate Domain」でURLを取得
   - または、カスタムドメインを設定可能
   - 取得したURLをメモ（例: `https://your-app.railway.app`）

**Renderでのデプロイ手順（完全無料・推奨）:**

1. **Renderにアカウント作成・ログイン**
   - https://render.com/ にアクセス
   - 「Get Started for Free」をクリック
   - GitHubアカウントでログイン（推奨）

2. **新しいWebサービスを作成**
   - ダッシュボードで「New +」をクリック
   - 「Web Service」を選択

3. **GitHubリポジトリを接続**
   - 「Connect account」をクリック（初回のみ）
   - GitHubアカウントを認証
   - リポジトリ `yoshi0323/note` を選択
   - 「Connect」をクリック

4. **サービス設定を入力**
   - **Name**: 任意の名前（例: `note-backend`）
   - **Region**: 最寄りのリージョンを選択（例: `Singapore`）
   - **Branch**: `main`（デフォルト）
   - **Root Directory**: `backend` ⚠️ **重要**
   - **Runtime**: `Python 3`
   - **Python Version**: `3.11.9`（`runtime.txt`で指定済み、Renderが自動検出します）
   - **Build Command**: 
     ```
     pip install -r requirements.txt && python -m playwright install chromium
     ```
   - **Start Command**: 
     ```
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: `Free` を選択

5. **環境変数を設定（オプション）**
   - 「Advanced」セクションを展開
   - 「Add Environment Variable」をクリック
   - 必要に応じて追加:
     - **Key**: `CORS_ORIGINS`
     - **Value**: `https://note-c801b.web.app,https://note-c801b.firebaseapp.com`
   - **注意**: デフォルトで本番フロントエンドURLは既に許可されているため、通常は不要です

6. **デプロイ開始**
   - 「Create Web Service」をクリック
   - デプロイが開始されます（5〜10分程度かかります）
   - 「Logs」タブでデプロイの進行状況を確認できます

7. **URLの取得**
   - デプロイが完了すると、自動的にURLが生成されます
   - 例: `https://note-backend.onrender.com`
   - このURLをメモしておきます

8. **動作確認**
   - 生成されたURLにアクセスして、`/docs`にアクセス
   - 例: `https://note-backend.onrender.com/docs`
   - FastAPIのドキュメントページが表示されれば成功です

**Renderの無料プランの注意事項:**
- 15分間アクセスがないと自動的にスリープします
- 次回アクセス時に自動的に再起動します（30秒〜1分程度かかります）
- これは無料プランの制限です
- スリープを防ぐには、定期的にアクセスするか、有料プランにアップグレードする必要があります

**注意事項:**
- バックエンドのCORS設定は既に本番フロントエンドURL（`https://note-c801b.web.app`、`https://note-c801b.firebaseapp.com`）を含んでいます
- Playwrightのブラウザインストールが必要なため、Renderの場合は`Build Command`に含める必要があります
- Railwayの場合は、デプロイ後に自動的にインストールされる場合がありますが、必要に応じて環境変数や設定で調整してください

### 2. フロントエンドの環境変数設定

本番環境のバックエンドURLを設定します。

**方法1: 環境変数ファイル（推奨）**

`frontend/.env.production`ファイルを作成（`.gitignore`に含まれているため、手動で作成してください）:
```
REACT_APP_API_URL=https://your-backend-url.com
```

**注意:** `.env.production`ファイルはGitにコミットされません。本番環境では手動で作成する必要があります。

**方法2: 直接コードを変更**

`frontend/src/services/api.js`の`API_BASE_URL`を変更:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-backend-url.com';
```

### 3. フロントエンドのビルド

```bash
cd frontend
npm install
npm run build
```

**注意:** `build`コマンドは本番環境用に設定されています（バックエンドURL: `https://note-121s.onrender.com`）。環境変数は`cross-env`を使用してビルド時に設定されます。

### 4. Firebase Hostingにデプロイ

プロジェクトルートから実行:
```bash
firebase deploy --only hosting
```

### 5. デプロイの確認

デプロイが完了すると、以下のようなURLが表示されます:
```
✔ Deploy complete!

Project Console: https://console.firebase.google.com/project/note-c801b/overview
Hosting URL: https://note-c801b.web.app
```

## 継続的なデプロイ

### 自動デプロイの設定

GitHub Actionsなどで自動デプロイを設定することもできます。

### 手動デプロイ

コードを変更した後、以下のコマンドで再デプロイ:
```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

## トラブルシューティング

### ビルドエラー

- `npm run build`でエラーが発生する場合、依存関係を再インストール:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### デプロイエラー

- Firebase CLIが最新版か確認:
```bash
npm install -g firebase-tools@latest
```

- Firebaseプロジェクトが正しく設定されているか確認:
```bash
firebase projects:list
```

### バックエンド接続エラー

- ブラウザのコンソールでエラーを確認
- CORS設定が正しいか確認
- バックエンドURLが正しく設定されているか確認

## 環境変数の設定

本番環境では、以下の環境変数を設定してください:

- `REACT_APP_API_URL`: バックエンドAPIのURL

これらの環境変数は、ビルド時に`process.env.REACT_APP_API_URL`として参照されます。

