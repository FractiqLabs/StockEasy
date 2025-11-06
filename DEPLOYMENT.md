# StockEasy - Supabase移行デプロイ手順書

このドキュメントでは、StockEasyをRenderからSupabase + Vercel/Netlifyに移行する手順を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [ステップ1: Supabaseプロジェクトのセットアップ](#ステップ1-supabaseプロジェクトのセットアップ)
3. [ステップ2: データベースマイグレーション](#ステップ2-データベースマイグレーション)
4. [ステップ3: Storageセットアップ](#ステップ3-storageセットアップ)
5. [ステップ4: フロントエンドの準備](#ステップ4-フロントエンドの準備)
6. [ステップ5: Vercel/Netlifyデプロイ](#ステップ5-vercelnetlifyデプロイ)
7. [ステップ6: 動作確認](#ステップ6-動作確認)
8. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

以下のアカウントを準備してください：

- ✅ [Supabase](https://supabase.com/)アカウント（無料プランでOK）
- ✅ [Vercel](https://vercel.com/)または[Netlify](https://netlify.com/)アカウント（無料プランでOK）
- ✅ GitHubアカウント（リポジトリ連携用）

---

## ステップ1: Supabaseプロジェクトのセットアップ

### 1.1 新規プロジェクトの作成

1. [Supabaseダッシュボード](https://app.supabase.com/)にログイン
2. **New Project**をクリック
3. 以下の情報を入力：
   - **Name**: `stockeasy-production`
   - **Database Password**: 強力なパスワードを生成（メモしておく）
   - **Region**: `Northeast Asia (Tokyo)`を選択（日本の場合）
   - **Pricing Plan**: `Free`を選択

4. **Create New Project**をクリック

⏱️ プロジェクトの作成には2〜3分かかります。

### 1.2 APIキーの取得

プロジェクトが作成されたら：

1. サイドバーから **Settings** > **API** を開く
2. 以下の情報をコピーして保存：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon / public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` ⚠️ **秘密にすること**

---

## ステップ2: データベースマイグレーション

### 2.1 SQLエディタでマイグレーションを実行

1. Supabaseダッシュボードで **SQL Editor** を開く
2. **New Query**をクリック

### 2.2 テーブルスキーマの作成

`supabase/migrations/20250101000000_initial_schema.sql`の内容をコピーして実行：

```sql
-- ファイルの内容をコピー&ペースト
```

✅ 実行完了後、**Table Editor**で以下のテーブルが作成されていることを確認：
- `facilities`
- `users`
- `admin_users`
- `equipment`

### 2.3 RLSポリシーの設定

`supabase/migrations/20250101000001_rls_policies.sql`の内容をコピーして実行：

```sql
-- ファイルの内容をコピー&ペースト
```

✅ 実行完了後、**Authentication** > **Policies**で各テーブルのポリシーが確認できます。

### 2.4 Storageの設定

`supabase/migrations/20250101000002_storage_setup.sql`の内容をコピーして実行：

```sql
-- ファイルの内容をコピー&ペースト
```

---

## ステップ3: Storageセットアップ

### 3.1 Storageバケットの確認

1. Supabaseダッシュボードで **Storage** を開く
2. `equipment-images`バケットが作成されていることを確認
3. バケットの設定で **Public bucket**が有効になっていることを確認

### 3.2 フォルダ構造の作成（オプション）

手動でフォルダを作成する場合：

```
equipment-images/
  ├── facility_1/
  ├── facility_2/
  └── ...
```

⚠️ **注意**: フォルダは備品登録時に自動的に作成されるため、事前作成は不要です。

---

## ステップ4: フロントエンドの準備

### 4.1 既存HTMLの移行

既存の`static/index.html`をベースに、以下の変更を加えます：

#### A. Supabase JavaScript Clientの追加

`<head>`セクションに以下を追加：

```html
<!-- Supabase JavaScript Client -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

#### B. 環境変数の設定

`<head>`セクションに以下を追加（Supabase認証情報を設定）：

```html
<script>
  // 環境変数をグローバルに設定
  window.ENV = {
    SUPABASE_URL: 'YOUR_SUPABASE_URL_HERE',
    SUPABASE_ANON_KEY: 'YOUR_SUPABASE_ANON_KEY_HERE'
  };
</script>
```

⚠️ **本番環境では、VercelまたはNetlifyの環境変数を使用してください**

#### C. JavaScriptファイルのロード

`</body>`の直前に以下を追加：

```html
<!-- StockEasy Supabase Modules -->
<script src="/js/supabase-client.js"></script>
<script src="/js/auth.js"></script>
<script src="/js/equipment.js"></script>

<script>
  // Supabaseクライアントを初期化
  document.addEventListener('DOMContentLoaded', () => {
    if (window.StockEasySupabase.initSupabase()) {
      console.log('✅ StockEasy initialized successfully');
    } else {
      console.error('❌ Failed to initialize StockEasy');
    }
  });
</script>
```

### 4.2 ファイル配置

以下のファイル構造を確認：

```
frontend/
├── index.html           # メインHTMLファイル
├── js/
│   ├── supabase-client.js
│   ├── auth.js
│   └── equipment.js
├── css/
│   └── styles.css       # （オプション）
└── assets/
    ├── favicon-16x16.png
    ├── favicon-32x32.png
    └── apple-touch-icon.png
```

---

## ステップ5: Vercel/Netlifyデプロイ

### オプションA: Vercelでデプロイ

#### 5.1 GitHubにプッシュ

```bash
git add .
git commit -m "Add Supabase migration files"
git push origin main
```

#### 5.2 Vercelでインポート

1. [Vercel Dashboard](https://vercel.com/dashboard)にログイン
2. **New Project** > **Import Git Repository**
3. GitHubリポジトリを選択
4. 以下の設定を入力：
   - **Framework Preset**: `Other`
   - **Root Directory**: `./`（デフォルト）
   - **Build Command**: （空欄）
   - **Output Directory**: `frontend`

#### 5.3 環境変数の設定

**Environment Variables**セクションで以下を追加：

```
SUPABASE_URL = https://xxxxx.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 5.4 デプロイ

**Deploy**をクリックして、デプロイを開始します。

---

### オプションB: Netlifyでデプロイ

#### 5.1 GitHubにプッシュ

```bash
git add .
git commit -m "Add Supabase migration files"
git push origin main
```

#### 5.2 Netlifyでインポート

1. [Netlify Dashboard](https://app.netlify.com/)にログイン
2. **New site from Git** > **GitHub**
3. リポジトリを選択
4. 以下の設定を入力：
   - **Base directory**: （空欄）
   - **Build command**: （空欄）
   - **Publish directory**: `frontend`

#### 5.3 環境変数の設定

**Site settings** > **Build & deploy** > **Environment** > **Environment variables**で以下を追加：

```
SUPABASE_URL = https://xxxxx.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 5.4 デプロイ

**Deploy site**をクリックして、デプロイを開始します。

---

## ステップ6: 動作確認

### 6.1 基本機能のテスト

デプロイ完了後、以下を確認：

1. ✅ サイトが正常に表示される
2. ✅ ログイン画面が表示される
3. ✅ 施設一覧が取得できる（データベース接続確認）

### 6.2 認証テスト

デフォルト管理者アカウントでログイン：

- **ユーザー名**: `admin`
- **パスワード**: `admin123`

⚠️ **セキュリティ**: 本番環境では必ずパスワードを変更してください！

### 6.3 備品登録テスト

1. 管理者画面から備品を新規登録
2. 画像をアップロード
3. Supabase Storageで画像が保存されていることを確認

### 6.4 RLSテスト

1. 複数の施設を作成
2. 各施設で異なるユーザーを作成
3. 他の施設のデータが閲覧できないことを確認

---

## トラブルシューティング

### 問題1: 「Supabase credentials are missing」エラー

**原因**: 環境変数が設定されていない

**解決策**:
- Vercel/Netlifyで環境変数が正しく設定されているか確認
- 再デプロイを実行

### 問題2: データベース接続エラー

**原因**: RLSポリシーが正しく設定されていない

**解決策**:
- Supabaseダッシュボードで**Authentication** > **Policies**を確認
- マイグレーションSQLを再実行

### 問題3: 画像がアップロードできない

**原因**: Storageバケットが公開設定になっていない、またはRLSポリシーが正しくない

**解決策**:
- Supabaseダッシュボードで**Storage** > `equipment-images`を開く
- **Make public**が有効になっているか確認
- Storage RLSポリシーを確認

### 問題4: ログインできない

**原因**: 認証情報が間違っている、またはユーザーが存在しない

**解決策**:
- Supabase SQL Editorで以下を実行して管理者を確認:

```sql
SELECT * FROM admin_users;
```

- デフォルトパスワードは`admin123`
- 必要に応じて新しい管理者を作成

### 問題5: 他の施設のデータが見える

**原因**: RLSポリシーが無効、またはfacility_idが正しく設定されていない

**解決策**:
- テーブルのRLSが有効になっているか確認:

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

- すべてのテーブルで`rowsecurity = true`であることを確認

---

## セキュリティ推奨事項

### 本番環境での必須対策

1. ✅ **デフォルトパスワードの変更**
   - 管理者パスワードを強力なものに変更

2. ✅ **HTTPSの使用**
   - Vercel/Netlifyは自動的にHTTPSを有効化

3. ✅ **CORS設定の確認**
   - Supabaseダッシュボードで許可するドメインを設定

4. ✅ **環境変数の保護**
   - Service Role Keyは絶対にフロントエンドに含めない
   - `.env`ファイルは`.gitignore`に追加

5. ✅ **定期的なバックアップ**
   - Supabaseダッシュボードから定期的にデータをエクスポート

---

## 次のステップ

### パフォーマンス最適化

- [ ] 画像の最適化（WebP形式への変換）
- [ ] CDNの活用（Vercel/Netlify標準）
- [ ] データベースインデックスの追加

### 機能追加

- [ ] Edge Functionによる認証強化
- [ ] リアルタイム更新（Supabase Realtime）
- [ ] 通知機能（メール/プッシュ通知）

### 監視・ログ

- [ ] Supabase Logsの確認
- [ ] Vercel/Netlify Analytics の有効化
- [ ] エラートラッキング（Sentry等）

---

## サポート

問題が解決しない場合：

1. [Supabaseドキュメント](https://supabase.com/docs)を確認
2. [Vercelドキュメント](https://vercel.com/docs)または[Netlifyドキュメント](https://docs.netlify.com/)を確認
3. GitHubリポジトリでIssueを作成

---

## ライセンス

このプロジェクトは、既存のStockEasyプロジェクトのライセンスに従います。

---

**🎉 デプロイ完了おめでとうございます！**

StockEasyがSupabaseとVercel/Netlifyで稼働するようになりました。
