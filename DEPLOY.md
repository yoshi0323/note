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

**推奨デプロイ先:**
- **Railway** (https://railway.app/) - 無料プランあり、簡単にデプロイ可能
- **Render** (https://render.com/) - 無料プランあり
- **Heroku** (https://www.heroku.com/) - 有料プランのみ（2022年11月以降）

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

**Renderでのデプロイ手順:**

1. Renderにアカウント作成・ログイン（GitHubアカウントでログイン可能）
   - https://render.com/

2. 新しいWebサービスを作成
   - 「New +」→「Web Service」を選択
   - GitHubリポジトリを接続

3. サービス設定
   - **Name**: 任意の名前（例: `note-backend`）
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -m playwright install chromium`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. 環境変数を設定（オプション）
   - 「Environment」セクションで追加:
     - `CORS_ORIGINS`: `https://note-c801b.web.app,https://note-c801b.firebaseapp.com`

5. デプロイ
   - 「Create Web Service」をクリック
   - デプロイ完了後、URLを取得（例: `https://your-app.onrender.com`）

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

