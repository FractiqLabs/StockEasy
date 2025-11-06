# StockEasy - ローカルサーバー起動ガイド

Vercel/Netlifyを使わずに、別のパソコンからStockEasyにアクセスする方法を説明します。

## 🚀 クイックスタート

### 1. Supabase環境変数の設定

まず、`frontend/index.html`を開いて、Supabaseの認証情報を設定します。

**ファイル:** `frontend/index.html` (20行目あたり)

```javascript
window.ENV = {
  SUPABASE_URL: 'https://your-project-id.supabase.co',  // ← ここを変更
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'  // ← ここを変更
};
```

### 2. サーバーを起動

#### 方法A: Pythonスクリプトを使用（推奨）

```bash
# StockEasyディレクトリに移動
cd /path/to/StockEasy

# サーバー起動
python3 start_server.py
```

実行すると、以下のような情報が表示されます：

```
============================================================
🚀 StockEasy サーバー起動
============================================================
📁 ディレクトリ: frontend
🌐 ポート: 8080

📱 アクセス方法:
  - このPC: http://localhost:8080
  - 同じネットワーク内の他のPC: http://192.168.1.100:8080

⚠️  注意:
  1. Supabaseの環境変数を設定してください
     (frontend/index.html の20行目あたり)
  2. ファイアウォールでポート8080を開放してください

🛑 停止: Ctrl+C
============================================================
```

#### 方法B: Pythonの標準モジュールを使用

```bash
cd /path/to/StockEasy/frontend
python3 -m http.server 8080 --bind 0.0.0.0
```

#### 方法C: Node.jsを使用

```bash
# http-serverをインストール（初回のみ）
npm install -g http-server

# サーバー起動
cd /path/to/StockEasy/frontend
http-server -p 8080 -a 0.0.0.0
```

### 3. 別のPCからアクセス

#### 同じWi-Fiネットワーク内の場合

別のPCやスマホのブラウザで以下のURLを開きます：

```
http://192.168.1.100:8080
```

（`192.168.1.100`の部分は、サーバーを起動したPCのIPアドレス）

#### IPアドレスの確認方法

**Windows:**
```cmd
ipconfig
```
→ `IPv4 アドレス` を確認

**Mac/Linux:**
```bash
ifconfig
```
または
```bash
ip addr show
```
→ `inet` のアドレスを確認

---

## 🔥 ファイアウォールの設定

別のPCからアクセスする場合、ファイアウォールでポート8080を開放する必要があります。

### Windowsの場合

1. **Windowsセキュリティ** を開く
2. **ファイアウォールとネットワーク保護** をクリック
3. **詳細設定** をクリック
4. **受信の規則** を右クリック > **新しい規則**
5. 以下を設定：
   - 規則の種類: **ポート**
   - プロトコル: **TCP**
   - ポート番号: **8080**
   - 操作: **接続を許可する**
   - 名前: **StockEasy Server**

### Macの場合

```bash
# ファイアウォールが有効な場合
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/bin/python3
```

### Linuxの場合

```bash
# ufwを使用している場合
sudo ufw allow 8080/tcp

# firewalldを使用している場合
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

---

## 🌍 インターネット経由でアクセスする方法

同じネットワーク内だけでなく、インターネット経由でアクセスしたい場合：

### オプション1: ngrok（最も簡単）

```bash
# ngrokをインストール
# https://ngrok.com/ からダウンロード

# サーバーを起動（別ターミナル）
python3 start_server.py

# ngrokで公開（新しいターミナル）
ngrok http 8080
```

ngrokが生成したURLをコピーして、どこからでもアクセス可能になります：

```
https://abc123.ngrok.io
```

### オプション2: Cloudflare Tunnel

```bash
# cloudflaredをインストール
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# サーバーを起動（別ターミナル）
python3 start_server.py

# Cloudflare Tunnelで公開
cloudflared tunnel --url http://localhost:8080
```

### オプション3: 自分のVPS/サーバー

AWS、GCP、Azure、さくらのVPSなどを使用してホスティングすることもできます。

---

## 📱 モバイルデバイスからアクセス

### 1. 同じWi-Fiに接続

スマホやタブレットを、サーバーを起動したPCと同じWi-Fiネットワークに接続します。

### 2. ブラウザでアクセス

```
http://192.168.1.100:8080
```

### 3. ホーム画面に追加（PWA風）

iOS Safariの場合：
1. 共有アイコンをタップ
2. 「ホーム画面に追加」を選択

Androidの場合：
1. メニューを開く
2. 「ホーム画面に追加」を選択

---

## 🔒 セキュリティに関する注意

### 注意事項

1. **パスワードの変更**
   - デフォルト管理者パスワード（`admin123`）は必ず変更してください

2. **HTTPSの使用**
   - 本番環境では必ずHTTPS（SSL/TLS）を使用してください
   - ngrokやCloudflare Tunnelは自動的にHTTPSになります

3. **ファイアウォール**
   - 必要なポートのみ開放してください
   - 使用後は閉じることを推奨します

4. **ローカルネットワーク限定**
   - 社内ネットワークなど、信頼できるネットワーク内での使用を推奨
   - インターネット公開は ngrok/Cloudflare Tunnel を使用

---

## 🛠️ トラブルシューティング

### 問題1: 別のPCから接続できない

**原因:** ファイアウォールでブロックされている

**解決策:**
1. ファイアウォールでポート8080を開放
2. サーバーが `0.0.0.0` でリッスンしているか確認（`127.0.0.1`ではダメ）

### 問題2: 「環境変数が見つかりません」エラー

**原因:** Supabase認証情報が設定されていない

**解決策:**
1. `frontend/index.html` を開く
2. 20行目あたりの `window.ENV` を編集
3. SupabaseのURLとANON KEYを設定

### 問題3: IPアドレスがわからない

**解決策:**
- Windowsの場合: コマンドプロンプトで `ipconfig`
- Mac/Linuxの場合: ターミナルで `ifconfig` または `ip addr`
- サーバー起動時に表示されるIPアドレスを確認

### 問題4: ポート8080が既に使用されている

**解決策:**
```bash
# 別のポート番号を使用
python3 -m http.server 8081 --bind 0.0.0.0
```

または `start_server.py` の `PORT = 8080` を変更

---

## 📊 推奨構成

### 小規模利用（5〜10人）

```
サーバーPC（Windows/Mac/Linux）
  ↓ 同じWi-Fi
スマホ/タブレット/PC（複数台）
```

- Pythonの簡易サーバーで十分
- ローカルネットワーク内のみでアクセス

### 中規模利用（10〜50人）

```
サーバーPC + ngrok/Cloudflare Tunnel
  ↓ インターネット
スマホ/タブレット/PC（複数台、どこからでも）
```

- ngrokまたはCloudflare Tunnelで公開
- HTTPS自動対応
- 無料プランでも十分

### 大規模利用（50人以上）

```
VPS/クラウドサーバー + Nginx
  ↓ インターネット
スマホ/タブレット/PC（多数）
```

- AWS、GCP、Azure、さくらのVPSなどを使用
- Nginxでリバースプロキシ設定
- SSL証明書（Let's Encrypt）でHTTPS化

---

## 🎯 まとめ

### 最も簡単な方法（ローカルネットワーク内のみ）

```bash
# 1. Supabase認証情報を設定
# frontend/index.html を編集

# 2. サーバー起動
python3 start_server.py

# 3. 別のPCからアクセス
# http://192.168.1.100:8080
```

### インターネット公開したい場合

```bash
# 1. サーバー起動
python3 start_server.py

# 2. ngrokで公開
ngrok http 8080

# 3. 生成されたURLをシェア
# https://abc123.ngrok.io
```

---

質問があれば、いつでも聞いてください！ 🚀
