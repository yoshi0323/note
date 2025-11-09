# Railway デプロイ手順

## 前提条件

- Railwayアカウント（GitHubアカウントでログイン可能）
- GitHubアカウント（方法1の場合）

## 方法1: GitHubリポジトリからデプロイ（推奨）

### ステップ1: Gitリポジトリを初期化

プロジェクトルートで以下を実行：

```bash
# Gitリポジトリを初期化
git init

# すべてのファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit"
```

### ステップ2: GitHubリポジトリを作成

1. GitHubにアクセス: https://github.com/
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例: `note-draft-system`）
4. 「Public」または「Private」を選択
5. 「Create repository」をクリック

### ステップ3: ローカルリポジトリをGitHubにプッシュ

GitHubで表示されるコマンドを実行（例）：

```bash
# リモートリポジトリを追加（YOUR_USERNAMEとYOUR_REPO_NAMEを置き換え）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# メインブランチを設定
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

### ステップ4: Railwayでプロジェクトを作成

1. Railwayにアクセス: https://railway.app/
2. 「Start a New Project」をクリック
3. 「Deploy from GitHub repo」を選択
4. GitHubアカウントでログイン（初回のみ）
5. リポジトリを選択
6. 「Deploy Now」をクリック

### ステップ5: サービス設定

1. デプロイが開始されますが、**ルートディレクトリを変更する必要があります**
2. サービスをクリック → 「Settings」タブ
3. 「Root Directory」を`backend`に設定
4. 変更が自動的に保存されます

### ステップ6: 環境変数の設定（オプション）

1. サービスを選択 → 「Variables」タブ
2. 「+ New Variable」をクリック
3. 必要に応じて追加:
   - **Name**: `CORS_ORIGINS`
   - **Value**: `https://note-c801b.web.app,https://note-c801b.firebaseapp.com`
4. 「Add」をクリック

**注意:** デフォルトで本番フロントエンドURLは既に許可されているため、この設定は通常不要です。

### ステップ7: ドメインの取得

1. サービスを選択 → 「Settings」タブ
2. 「Generate Domain」をクリック
3. 生成されたURLをコピー（例: `https://your-app.railway.app`）
4. このURLをメモしておきます

### ステップ8: デプロイの確認

1. 「Deployments」タブでデプロイの進行状況を確認
2. ログを確認してエラーがないか確認
3. 生成されたURLにアクセスして、`/docs`にアクセス（例: `https://your-app.railway.app/docs`）
4. FastAPIのドキュメントページが表示されれば成功です

---

## 方法2: Railway CLIを使用してデプロイ

### ステップ1: Railway CLIをインストール

```bash
npm install -g @railway/cli
```

### ステップ2: Railwayにログイン

```bash
railway login
```

ブラウザが開くので、Railwayアカウントでログインします。

### ステップ3: プロジェクトを初期化

```bash
# プロジェクトルートで実行
railway init
```

プロジェクト名を入力します。

### ステップ4: サービスを追加

```bash
# backendディレクトリに移動
cd backend

# サービスをリンク
railway link

# ルートディレクトリを設定（必要に応じて）
railway variables set RAILWAY_SERVICE_ROOT_DIRECTORY=backend
```

### ステップ5: デプロイ

```bash
# backendディレクトリから実行
railway up
```

### ステップ6: ドメインの取得

```bash
railway domain
```

または、Railwayのダッシュボードから「Settings」→「Generate Domain」で取得できます。

---

## トラブルシューティング

### デプロイが失敗する場合

1. **ログを確認**
   - Railwayダッシュボード → サービス → 「Deployments」タブ
   - エラーメッセージを確認

2. **Playwrightのインストールエラー**
   - `railway.json`の`buildCommand`に`python -m playwright install chromium`が含まれているか確認
   - 必要に応じて、環境変数で調整

3. **ポートエラーの場合**
   - `Procfile`または`railway.json`で`$PORT`環境変数を使用しているか確認
   - Railwayは自動的に`$PORT`を設定します

4. **依存関係のインストールエラー**
   - `requirements.txt`が正しいか確認
   - Pythonバージョンが適切か確認（`runtime.txt`で指定）

### デプロイ後の確認

1. **APIが動作しているか確認**
   - `https://your-app.railway.app/docs`にアクセス
   - FastAPIのドキュメントページが表示されればOK

2. **CORSエラーの場合**
   - ブラウザのコンソールでエラーを確認
   - 環境変数`CORS_ORIGINS`が正しく設定されているか確認
   - バックエンドのログでCORS設定を確認

---

## 次のステップ

バックエンドのデプロイが完了したら：

1. **フロントエンドの環境変数を設定**
   ```bash
   cd frontend
   echo REACT_APP_API_URL=https://your-app.railway.app > .env.production
   ```

2. **フロントエンドをビルド＆デプロイ**
   ```bash
   npm run build
   cd ..
   firebase deploy --only hosting
   ```

詳細は`DEPLOY.md`を参照してください。

