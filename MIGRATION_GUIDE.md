# StockEasy - フロントエンド移行ガイド

このドキュメントでは、既存のFlask APIコードをSupabase SDKに移行する方法を説明します。

## 📋 移行の概要

### 完了した作業

✅ **インフラ層**
- Supabaseマイグレーション（データベース、RLS、Storage）
- Vercel/Netlifyデプロイ設定
- 環境変数設定

✅ **モジュール層**
- `supabase-client.js` - Supabase接続
- `auth.js` - 認証管理
- `equipment.js` - 備品CRUD操作
- `api-bridge.js` - Flask API互換レイヤー

✅ **HTML層**
- Supabase JavaScript Clientのロード
- 環境変数の設定
- Supabaseモジュールのロード
- APIブリッジのロード

### 残りの作業

⚠️ **既存のJavaScriptコードの移行**

`frontend/index.html`内の既存のJavaScriptコード（約2000行）を、Supabase SDKを使用するように変更する必要があります。

---

## 🔄 移行パターン

### パターン1: ログイン処理

#### 旧コード（Flask API）

```javascript
async function login() {
  const role = document.getElementById('roleSelect').value;
  const password = document.getElementById('loginPassword').value;

  if (role === 'admin') {
    const response = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username: 'admin', password })
    });
    const result = await response.json();
    // ...
  }
}
```

#### 新コード（Supabase SDK）

```javascript
async function login() {
  const role = document.getElementById('roleSelect').value;
  const password = document.getElementById('loginPassword').value;

  // APIブリッジを使用
  const result = await window.StockEasyBridge.loginWithSupabase(role, password);

  if (result.success) {
    console.log('✅ ログイン成功');
    // UI更新処理
  } else {
    console.error('❌ ログイン失敗:', result.message);
    alert(result.message);
  }
}
```

---

### パターン2: 備品一覧取得

#### 旧コード（Flask API）

```javascript
async function loadItems() {
  try {
    const response = await fetch(`${API_BASE}/equipment`);
    const data = await response.json();

    // グローバル変数に保存
    items = data;
    renderItems();
  } catch (error) {
    console.error('データ取得エラー:', error);
  }
}
```

#### 新コード（Supabase SDK）

```javascript
async function loadItems() {
  try {
    // APIブリッジを使用
    const data = await window.StockEasyBridge.loadItemsFromSupabase();

    // グローバル変数に保存
    items = data;
    renderItems();
  } catch (error) {
    console.error('データ取得エラー:', error);
  }
}
```

---

### パターン3: 備品登録

#### 旧コード（Flask API）

```javascript
async function registerItem() {
  const itemData = {
    id: document.getElementById('itemId').value,
    name: document.getElementById('itemName').value,
    category: document.getElementById('categorySelect').value,
    location: document.getElementById('locationSelect').value,
    image: imageDataUrl,
    history: []
  };

  const response = await fetch(`${API_BASE}/equipment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(itemData)
  });

  const result = await response.json();
  // ...
}
```

#### 新コード（Supabase SDK）

```javascript
async function registerItem() {
  const itemData = {
    item_id: document.getElementById('itemId').value,
    name: document.getElementById('itemName').value,
    category: document.getElementById('categorySelect').value,
    location: document.getElementById('locationSelect').value,
    imageFile: imageFile, // Base64ではなくFileオブジェクト
    history: []
  };

  // APIブリッジを使用
  const result = await window.StockEasyBridge.registerItemToSupabase(itemData);

  if (result.success) {
    console.log('✅ 登録成功');
    await loadItems(); // 再読み込み
  } else {
    console.error('❌ 登録失敗:', result.message);
    alert(result.message);
  }
}
```

---

### パターン4: 備品更新

#### 旧コード（Flask API）

```javascript
async function updateNote(index, note) {
  const item = items[index];

  await fetch(`${API_BASE}/equipment/${item.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note: note })
  });
}
```

#### 新コード（Supabase SDK）

```javascript
async function updateNote(index, note) {
  const item = items[index];

  // APIブリッジを使用
  const result = await window.StockEasyBridge.updateItemInSupabase(item.id, {
    note: note
  });

  if (result.success) {
    console.log('✅ 更新成功');
    items[index].note = note; // ローカル更新
  } else {
    console.error('❌ 更新失敗:', result.message);
  }
}
```

---

### パターン5: 備品借用

#### 旧コード（Flask API）

```javascript
async function confirmBorrow() {
  const item = items[currentIndex];
  const userName = document.getElementById('borrowUser').value;
  const userLocation = document.getElementById('borrowLocation').value;

  await fetch(`${API_BASE}/equipment/${item.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status: '使用中',
      user: userName,
      current: userLocation,
      history: [...item.history, {
        action: '借用',
        place: userLocation,
        timestamp: new Date().toLocaleString('ja-JP')
      }]
    })
  });
}
```

#### 新コード（Supabase SDK）

```javascript
async function confirmBorrow() {
  const item = items[currentIndex];
  const userName = document.getElementById('borrowUser').value;
  const userLocation = document.getElementById('borrowLocation').value;

  // APIブリッジを使用
  const result = await window.StockEasyBridge.borrowItemFromSupabase(
    item.id,
    userName,
    userLocation
  );

  if (result.success) {
    console.log('✅ 借用成功');
    await loadItems(); // 再読み込み
    closeBorrowModal();
  } else {
    console.error('❌ 借用失敗:', result.message);
    alert(result.message);
  }
}
```

---

### パターン6: 備品返却

#### 旧コード（Flask API）

```javascript
async function confirmReturn() {
  const item = items[currentIndex];
  const note = document.getElementById('returnNote').value;

  await fetch(`${API_BASE}/equipment/${item.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      status: '待機',
      user: '',
      current: item.location,
      note: note,
      history: [...item.history, {
        action: '返却',
        place: item.location,
        timestamp: new Date().toLocaleString('ja-JP')
      }]
    })
  });
}
```

#### 新コード（Supabase SDK）

```javascript
async function confirmReturn() {
  const item = items[currentIndex];
  const note = document.getElementById('returnNote').value;

  // APIブリッジを使用
  const result = await window.StockEasyBridge.returnItemToSupabase(
    item.id,
    note
  );

  if (result.success) {
    console.log('✅ 返却成功');
    await loadItems(); // 再読み込み
    closeReturnModal();
  } else {
    console.error('❌ 返却失敗:', result.message);
    alert(result.message);
  }
}
```

---

## 🔍 主な変更点まとめ

### 1. API_BASEの削除

```javascript
// ❌ 旧コード
const API_BASE = window.location.origin + '/api';

// ✅ 新コード
// API_BASEは不要（api-bridge.jsが提供）
```

### 2. fetch()の置き換え

```javascript
// ❌ 旧コード
const response = await fetch(`${API_BASE}/equipment`, options);
const data = await response.json();

// ✅ 新コード
const data = await window.StockEasyBridge.loadItemsFromSupabase();
```

### 3. エラーハンドリング

```javascript
// ❌ 旧コード
if (response.ok) {
  const data = await response.json();
  // ...
}

// ✅ 新コード
const result = await window.StockEasyBridge.registerItemToSupabase(data);
if (result.success) {
  // ...
}
```

### 4. 画像アップロード

```javascript
// ❌ 旧コード（Base64エンコード）
const imageDataUrl = canvas.toDataURL('image/jpeg');
body: JSON.stringify({ image: imageDataUrl })

// ✅ 新コード（Fileオブジェクト）
const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
const file = new File([blob], 'image.jpg', { type: 'image/jpeg' });
{ imageFile: file }
```

---

## 📝 移行チェックリスト

### 必須の変更

- [ ] `login()` 関数をSupabase認証に置き換え
- [ ] `loadItems()` 関数をSupabase SDKに置き換え
- [ ] `registerItem()` 関数をSupabase SDKに置き換え
- [ ] `updateNote()` などの更新処理をSupabase SDKに置き換え
- [ ] `confirmBorrow()` をSupabase SDKに置き換え
- [ ] `confirmReturn()` をSupabase SDKに置き換え
- [ ] `confirmDelete()` をSupabase SDKに置き換え
- [ ] `exportData()` をSupabase SDKに置き換え
- [ ] `importData()` をSupabase SDKに置き換え

### オプションの変更

- [ ] 画像アップロードをFileオブジェクトに変更（Base64から移行）
- [ ] セッション管理をSupabase Authに移行
- [ ] リアルタイム更新機能の追加（Supabase Realtime）

---

## 🚀 段階的移行の推奨手順

### フェーズ1: 環境構築（完了✅）

1. Supabaseプロジェクト作成
2. マイグレーション実行
3. モジュール作成
4. HTMLへのロード追加

### フェーズ2: 認証移行（次のステップ）

1. `login()` 関数の置き換え
2. `logout()` 関数の置き換え
3. セッション復元の確認

### フェーズ3: 読み取り操作移行

1. `loadItems()` 関数の置き換え
2. 施設一覧取得の置き換え
3. データ表示の動作確認

### フェーズ4: 書き込み操作移行

1. `registerItem()` の置き換え
2. `updateNote()` などの更新処理の置き換え
3. `confirmDelete()` の置き換え

### フェーズ5: 高度な機能移行

1. 借用・返却処理の置き換え
2. 画像アップロードの移行
3. データインポート/エクスポートの移行

### フェーズ6: 最終調整

1. エラーハンドリングの改善
2. パフォーマンス最適化
3. 本番環境デプロイ

---

## 🛠️ 開発時のヒント

### 1. コンソールログの活用

```javascript
console.log('🔍 デバッグ:', data);
console.warn('⚠️ 警告:', message);
console.error('❌ エラー:', error);
```

### 2. Supabaseダッシュボードの確認

- **Table Editor**: データが正しく保存されているか確認
- **Storage**: 画像が正しくアップロードされているか確認
- **Logs**: エラーログを確認

### 3. ブラウザの開発者ツール

- **Console**: エラーメッセージを確認
- **Network**: APIリクエストを確認
- **Application > Local Storage**: セッション情報を確認

---

## 📞 サポート

問題が発生した場合：

1. [DEPLOYMENT.md](DEPLOYMENT.md)のトラブルシューティングを確認
2. Supabaseダッシュボードのログを確認
3. ブラウザのコンソールログを確認
4. GitHubでIssueを作成

---

**次のステップ**: [フェーズ2: 認証移行](#フェーズ2-認証移行次のステップ)から開始してください。
