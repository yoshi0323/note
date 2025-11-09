# Firebase セットアップ手順

## 現在の状況

`note-5d850`プロジェクトがFirebaseコンソールに存在しないか、アクセス権限がない可能性があります。

## 解決方法

### 方法1: Firebaseコンソールでプロジェクトを作成（推奨）

1. Firebaseコンソールにアクセス
   - https://console.firebase.google.com/

2. プロジェクトを作成
   - 「プロジェクトを追加」をクリック
   - プロジェクト名: `note-5d850`（または任意の名前）
   - プロジェクトID: `note-5d850`（自動生成される場合は変更可能）

3. Hostingを有効化
   - プロジェクト作成後、左メニューから「Hosting」を選択
   - 「始める」をクリック

4. プロジェクトを選択
   ```bash
   firebase use note-5d850
   ```

### 方法2: 既存のプロジェクトを使用

既存のプロジェクトを使用する場合：

1. プロジェクト一覧から選択
   ```bash
   firebase projects:list
   ```

2. プロジェクトを選択
   ```bash
   firebase use <project-id>
   ```

3. `.firebaserc`を更新
   ```json
   {
     "projects": {
       "default": "<選択したプロジェクトID>"
     }
   }
   ```

### 方法3: 手動で設定（既に設定ファイルがある場合）

既に`firebase.json`と`.firebaserc`が作成されているため、`firebase init`をスキップできます：

1. プロジェクトが作成されたら、以下を実行：
   ```bash
   firebase use note-5d850
   ```

2. ビルドとデプロイ
   ```bash
   cd frontend
   npm run build
   cd ..
   firebase deploy --only hosting
   ```

## 注意事項

- Firebase設定（`frontend/src/firebase.js`）は既に作成済みです
- プロジェクトIDが異なる場合は、`firebase.js`の`projectId`を更新してください
- `.firebaserc`のプロジェクトIDも更新してください

