/**
 * StockEasy - API Bridge Module
 * Flask API呼び出しとSupabase SDKをブリッジするラッパー関数
 *
 * このファイルにより、既存のコードを最小限の変更でSupabaseに移行できます。
 */

// ====================================
// グローバル変数（既存コードとの互換性）
// ====================================

// API_BASEは不要になりましたが、既存コードとの互換性のため残す
const API_BASE = '';

// ====================================
// 認証関連のラッパー関数
// ====================================

/**
 * ログイン処理（既存のlogin()関数をラップ）
 */
async function loginWithSupabase(role, password, facilityId = null) {
  try {
    if (role === 'admin') {
      // 管理者ログイン
      const result = await window.StockEasyAuth.loginAdmin('admin', password);
      return result;
    } else {
      // 職員ログイン（施設IDが必要）
      if (!facilityId) {
        return { success: false, message: '施設を選択してください' };
      }
      const result = await window.StockEasyAuth.login(facilityId, 'staff', password, 'staff');
      return result;
    }
  } catch (error) {
    console.error('❌ Login error:', error);
    return { success: false, message: error.message || 'ログインに失敗しました' };
  }
}

/**
 * ログアウト処理
 */
async function logoutFromSupabase() {
  try {
    const result = await window.StockEasyAuth.logout();
    return result;
  } catch (error) {
    console.error('❌ Logout error:', error);
    return { success: false, message: error.message || 'ログアウトに失敗しました' };
  }
}

// ====================================
// 備品管理関連のラッパー関数
// ====================================

/**
 * 備品一覧取得（既存のloadItems()関数をラップ）
 */
async function loadItemsFromSupabase(filters = {}) {
  try {
    const equipment = await window.StockEasyEquipment.getEquipment(filters);
    return equipment;
  } catch (error) {
    console.error('❌ Load items error:', error);
    throw error;
  }
}

/**
 * 備品登録（既存のregisterItem()関数をラップ）
 */
async function registerItemToSupabase(itemData) {
  try {
    const result = await window.StockEasyEquipment.createEquipment(itemData);
    return result;
  } catch (error) {
    console.error('❌ Register item error:', error);
    return { success: false, message: error.message || '備品の登録に失敗しました' };
  }
}

/**
 * 備品更新（既存のupdateNote()などをラップ）
 */
async function updateItemInSupabase(itemId, updates) {
  try {
    const result = await window.StockEasyEquipment.updateEquipment(itemId, updates);
    return result;
  } catch (error) {
    console.error('❌ Update item error:', error);
    return { success: false, message: error.message || '備品の更新に失敗しました' };
  }
}

/**
 * 備品削除
 */
async function deleteItemFromSupabase(itemId) {
  try {
    const result = await window.StockEasyEquipment.deleteEquipment(itemId);
    return result;
  } catch (error) {
    console.error('❌ Delete item error:', error);
    return { success: false, message: error.message || '備品の削除に失敗しました' };
  }
}

/**
 * 備品借用
 */
async function borrowItemFromSupabase(itemId, userName, userLocation) {
  try {
    const result = await window.StockEasyEquipment.borrowEquipment(itemId, userName, userLocation);
    return result;
  } catch (error) {
    console.error('❌ Borrow item error:', error);
    return { success: false, message: error.message || '備品の借用に失敗しました' };
  }
}

/**
 * 備品返却
 */
async function returnItemToSupabase(itemId, note = '') {
  try {
    const result = await window.StockEasyEquipment.returnEquipment(itemId, note);
    return result;
  } catch (error) {
    console.error('❌ Return item error:', error);
    return { success: false, message: error.message || '備品の返却に失敗しました' };
  }
}

/**
 * データエクスポート
 */
async function exportDataFromSupabase() {
  try {
    const result = await window.StockEasyEquipment.exportData();
    return result;
  } catch (error) {
    console.error('❌ Export data error:', error);
    return { success: false, message: error.message || 'データのエクスポートに失敗しました' };
  }
}

/**
 * データインポート
 */
async function importDataToSupabase(file) {
  try {
    const result = await window.StockEasyEquipment.importData(file);
    return result;
  } catch (error) {
    console.error('❌ Import data error:', error);
    return { success: false, message: error.message || 'データのインポートに失敗しました' };
  }
}

// ====================================
// 施設管理関連のラッパー関数
// ====================================

/**
 * 施設一覧取得
 */
async function loadFacilitiesFromSupabase() {
  try {
    const facilities = await window.StockEasyAuth.loadFacilities();
    return facilities;
  } catch (error) {
    console.error('❌ Load facilities error:', error);
    return [];
  }
}

// ====================================
// 後方互換性のためのエイリアス
// ====================================

// 既存のapiCall()関数の代替（廃止予定）
async function apiCall(url, options = {}) {
  console.warn('⚠️ apiCall()は廃止予定です。Supabase SDKを直接使用してください。');

  // 簡易的なルーティング（完全な互換性はありません）
  if (url.includes('/equipment') && options.method === 'GET') {
    return { ok: true, json: async () => await loadItemsFromSupabase() };
  } else if (url.includes('/equipment') && options.method === 'POST') {
    const data = JSON.parse(options.body);
    const result = await registerItemToSupabase(data);
    return { ok: result.success, json: async () => result };
  } else if (url.includes('/equipment/') && options.method === 'PUT') {
    const itemId = url.split('/').pop();
    const data = JSON.parse(options.body);
    const result = await updateItemInSupabase(itemId, data);
    return { ok: result.success, json: async () => result };
  } else if (url.includes('/equipment/') && options.method === 'DELETE') {
    const itemId = url.split('/').pop();
    const result = await deleteItemFromSupabase(itemId);
    return { ok: result.success, json: async () => result };
  }

  console.error('❌ Unsupported API call:', url, options);
  return { ok: false, json: async () => ({ success: false, message: 'Unsupported API call' }) };
}

// グローバルに公開
window.StockEasyBridge = {
  // 認証
  loginWithSupabase,
  logoutFromSupabase,

  // 備品管理
  loadItemsFromSupabase,
  registerItemToSupabase,
  updateItemInSupabase,
  deleteItemFromSupabase,
  borrowItemFromSupabase,
  returnItemToSupabase,
  exportDataFromSupabase,
  importDataToSupabase,

  // 施設管理
  loadFacilitiesFromSupabase,

  // 後方互換性
  apiCall
};

console.log('✅ StockEasy API Bridge loaded');
