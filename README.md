# StockEasy - らくらく備品管理システム

> ⚠️ **重要なお知らせ**: このプロジェクトはSupabase + Vercel/Netlifyアーキテクチャに移行中です。
> 詳細は [DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

## 📋 概要

StockEasyは、介護施設や医療機関向けに開発された備品管理システムです。車いす、歩行器、エアマットなどの備品の貸出・返却を簡単に管理し、施設運営の効率化を実現します。

### ✨ 主な特徴

- 📸 **写真付き備品管理** - 備品を画像付きで登録し、視覚的に管理
- 🔄 **リアルタイム貸出管理** - 貸出・返却状況を即座に把握
- 📍 **位置追跡機能** - 各備品の現在地と推奨返却場所を表示
- 👥 **権限管理** - 職員用と管理者用の2つのアクセスレベル
- 💾 **データ保護** - 自動保存とバックアップ機能
- 📱 **レスポンシブデザイン** - PC、タブレット、スマートフォンに対応
- 🔒 **施設ごとのデータ分離** - Row Level Security (RLS) による完全な分離
- ☁️ **クラウドストレージ** - Supabase Storageで画像を安全に保存

## 🏗️ アーキテクチャ

### 新アーキテクチャ（Supabase移行版）

```
┌─────────────────┐
│  Vercel/Netlify │  ← フロントエンドホスティング
│   (Frontend)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│    Supabase     │  ← バックエンド・データベース
│  ┌───────────┐  │
│  │ PostgreSQL │  │  ← データベース + RLS
│  ├───────────┤  │
│  │   Auth    │  │  ← 認証管理
│  ├───────────┤  │
│  │  Storage  │  │  ← 画像保存
│  └───────────┘  │
└─────────────────┘
```

### 旧アーキテクチャ（Flask版）

```
┌─────────────────┐
│     Render      │
│ ┌─────────────┐ │
│ │   Flask     │ │  ← Pythonバックエンド
│ ├─────────────┤ │
│ │ PostgreSQL  │ │  ← データベース
│ └─────────────┘ │
└─────────────────┘
```

## 🚀 クイックスタート

### オプションA: Supabase版（推奨）

#### 必要な環境

- Node.js 18以上（開発時のみ）
- Supabaseアカウント（無料プラン可）
- Vercel または Netlifyアカウント（無料プラン可）

#### デプロイ手順

詳細な手順は [DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

**概要:**

1. Supabaseプロジェクトを作成
2. データベースマイグレーションを実行
3. フロントエンドをVercel/Netlifyにデプロイ

```bash
# 1. リポジトリのクローン
git clone https://github.com/yourusername/stockeasy.git
cd stockeasy

# 2. Supabaseでマイグレーションを実行
# （SupabaseダッシュボードのSQL Editorで実行）

# 3. Vercel/Netlifyにデプロイ
# （ダッシュボードからGitHubリポジトリを連携）
```

### オプションB: Flask版（旧バージョン）

⚠️ **非推奨**: この方法はRenderの無料プラン終了に伴い利用できなくなりました。

#### 必要な環境

- Python 3.8以上
- pip（Pythonパッケージマネージャー）

#### インストール手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/yourusername/stockeasy.git
cd stockeasy
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

3. **アプリケーションの起動**
```bash
python app.py
```

4. **ブラウザでアクセス**
```
http://localhost:8080
```

## 📖 使い方

### ログイン

1. **職員としてログイン**
   - 役割選択で「職員」を選択
   - パスワード不要でログイン可能

2. **管理者としてログイン**
   - 役割選択で「管理者」を選択
   - パスワード: `admin123`

### 基本操作

#### 職員向け機能
- **備品の借用**: 「借用」ボタンから使用場所を選択
- **備品の返却**: 「返却」ボタンから返却場所を選択
- **備考の追加**: 備考欄に直接入力して情報を更新
- **フィルタリング**: カテゴリ別に備品を絞り込み

#### 管理者向け機能
- **新規備品登録**: 備品名、ID、保管場所、カテゴリ、画像を設定
- **備品情報編集**: 「編集」ボタンから各種情報を変更
- **備品削除**: 編集画面から不要な備品を削除
- **データ管理**: エクスポート/インポート機能でバックアップ

## 🏗️ システム構成

### Supabase版（新）

```
StockEasy/
├── supabase/
│   └── migrations/
│       ├── 20250101000000_initial_schema.sql   # テーブル作成
│       ├── 20250101000001_rls_policies.sql     # RLS設定
│       └── 20250101000002_storage_setup.sql    # Storage設定
├── frontend/
│   ├── index.html                              # メインHTML
│   ├── js/
│   │   ├── supabase-client.js                  # Supabase接続
│   │   ├── auth.js                             # 認証処理
│   │   └── equipment.js                        # 備品管理
│   ├── css/
│   │   └── styles.css
│   └── assets/
│       └── *.png
├── .env.example                                # 環境変数テンプレート
├── vercel.json                                 # Vercelデプロイ設定
├── netlify.toml                                # Netlifyデプロイ設定
├── DEPLOYMENT.md                               # デプロイ手順書
└── README.md                                   # このファイル
```

### Flask版（旧）

```
StockEasy/
├── app.py              # Flaskアプリケーション本体
├── requirements.txt    # Python依存関係
├── Procfile           # Renderデプロイ設定
├── static/            # 静的ファイル
│   └── index.html     # フロントエンドUI
└── equipment.db       # SQLiteデータベース（廃止予定）
```

## 🛠️ 技術スタック

### Supabase版（新）

#### バックエンド
- **Supabase** - BaaS（Backend as a Service）
  - **PostgreSQL** - リレーショナルデータベース + RLS
  - **Supabase Auth** - 認証管理
  - **Supabase Storage** - オブジェクトストレージ
  - **Row Level Security (RLS)** - 施設ごとのデータ分離

#### フロントエンド
- **HTML5/CSS3** - モダンなUI構築
- **JavaScript (Vanilla)** - インタラクティブな操作
- **Supabase JavaScript Client** - データベース操作
- **Transformer.js** - ローカルAI機能（オプション）
- **レスポンシブデザイン** - 全デバイス対応

#### インフラ
- **Vercel / Netlify** - 静的サイトホスティング
- **GitHub** - ソースコード管理とCI/CD

### Flask版（旧）

#### バックエンド
- **Flask** (2.3.3) - Pythonウェブフレームワーク
- **PostgreSQL / SQLite** - データベース
- **Flask-CORS** - クロスオリジンリクエスト対応

#### フロントエンド
- **HTML5/CSS3** - モダンなUI構築
- **JavaScript (Vanilla)** - インタラクティブな操作
- **レスポンシブデザイン** - 全デバイス対応

## 🌐 デプロイ

### Supabase版のデプロイ（推奨）

詳細な手順は [DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

**簡単な流れ:**

1. **Supabaseプロジェクトの作成**
   - [Supabaseダッシュボード](https://app.supabase.com/)で新規プロジェクト作成
   - APIキーを取得

2. **データベースマイグレーション**
   - SQL Editorでマイグレーションファイルを実行
   - RLSポリシーを設定
   - Storageバケットを作成

3. **Vercel/Netlifyでデプロイ**
   - GitHubリポジトリを連携
   - 環境変数を設定（SUPABASE_URL, SUPABASE_ANON_KEY）
   - デプロイ実行

### Flask版のデプロイ（非推奨）

⚠️ **Renderの無料プラン終了に伴い、この方法は利用できなくなりました。**

<details>
<summary>参考：Render/Herokuへのデプロイ手順（廃止予定）</summary>

1. **環境変数の設定**
```bash
ENVIRONMENT=production
PORT=8080
DATABASE_URL=postgresql://...
```

2. **Procfileの確認**
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

3. **デプロイコマンド**
```bash
# Heroku
heroku create your-app-name
git push heroku main

# Render
# Render.comのダッシュボードから設定
```

</details>

## 🔒 セキュリティ

- HTTPS強制リダイレクト（本番環境）
- パスワード保護された管理者機能
- SQLインジェクション対策
- XSS対策済み

## 📊 データ形式

### エクスポート/インポート形式（JSON）
```json
[
  {
    "id": "WC001",
    "name": "車いす（自走式）",
    "location": "事務所",
    "category": "車いす",
    "current": "2F",
    "user": "2F",
    "status": "使用中",
    "note": "定期メンテナンス済み",
    "image": "data:image/jpeg;base64,...",
    "history": [
      {
        "action": "借用",
        "place": "2F",
        "timestamp": "2025/6/11 10:30:00"
      }
    ],
    "createdAt": "2025-06-11T01:30:00.000Z"
  }
]
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

1. **ログインできない**
   - ブラウザのキャッシュをクリア
   - JavaScriptが有効か確認

2. **データが表示されない**
   - データベースの初期化: `/api/init-db`にアクセス
   - ブラウザのコンソールでエラーを確認

3. **画像アップロードが失敗する**
   - ファイルサイズを確認（推奨: 2MB以下）
   - 対応形式: JPEG, PNG, GIF

## 🤝 貢献方法

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 👏 謝辞

- すべてのコントリビューター
- 介護施設の職員の皆様のフィードバック
- オープンソースコミュニティ

## 📞 サポート

問題や質問がある場合は、以下の方法でサポートを受けられます：

- [Issues](https://github.com/yourusername/stockeasy-system/issues)でバグ報告
- [Discussions](https://github.com/yourusername/stockeasy-system/discussions)で質問
- メール: shinjitanaka.s@gmail.com
