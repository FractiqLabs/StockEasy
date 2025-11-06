/**
 * StockEasy - Supabase Client Setup
 * Supabase接続の初期化と設定
 */

// 環境変数からSupabaseの設定を取得
// Vercel/Netlifyでは環境変数として設定してください
const SUPABASE_URL = window.ENV?.SUPABASE_URL || '';
const SUPABASE_ANON_KEY = window.ENV?.SUPABASE_ANON_KEY || '';

// Supabaseクライアントの初期化
let supabase = null;

/**
 * Supabaseクライアントを初期化
 */
function initSupabase() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.error('❌ Supabase credentials are missing. Please check your environment variables.');
    showError('Supabaseの設定が見つかりません。環境変数を確認してください。');
    return false;
  }

  try {
    // Supabase JavaScript Clientの初期化
    supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storage: window.localStorage
      },
      db: {
        schema: 'public'
      }
    });

    console.log('✅ Supabase client initialized successfully');
    return true;
  } catch (error) {
    console.error('❌ Failed to initialize Supabase client:', error);
    showError('Supabaseの初期化に失敗しました: ' + error.message);
    return false;
  }
}

/**
 * 現在のセッション情報を取得
 */
async function getCurrentSession() {
  try {
    const { data: { session }, error } = await supabase.auth.getSession();

    if (error) {
      console.error('❌ Failed to get session:', error);
      return null;
    }

    return session;
  } catch (error) {
    console.error('❌ Session retrieval error:', error);
    return null;
  }
}

/**
 * 現在のユーザー情報を取得
 */
async function getCurrentUser() {
  try {
    const { data: { user }, error } = await supabase.auth.getUser();

    if (error) {
      console.error('❌ Failed to get user:', error);
      return null;
    }

    return user;
  } catch (error) {
    console.error('❌ User retrieval error:', error);
    return null;
  }
}

/**
 * Supabase Storageから画像URLを取得
 * @param {string} filePath - ファイルパス（例: facility_1/item_001.jpg）
 * @returns {string} - 公開URL
 */
function getImageUrl(filePath) {
  if (!filePath) return '';

  const { data } = supabase.storage
    .from('equipment-images')
    .getPublicUrl(filePath);

  return data?.publicUrl || '';
}

/**
 * Supabase Storageに画像をアップロード
 * @param {File} file - アップロードするファイル
 * @param {number} facilityId - 施設ID
 * @param {string} itemId - 備品ID
 * @returns {Promise<string>} - アップロードされたファイルのパス
 */
async function uploadImage(file, facilityId, itemId) {
  try {
    // ファイル拡張子を取得
    const fileExt = file.name.split('.').pop();
    const fileName = `${itemId}_${Date.now()}.${fileExt}`;
    const filePath = `facility_${facilityId}/${fileName}`;

    // 既存の画像を削除（同じitem_idの画像があれば）
    const { data: existingFiles } = await supabase.storage
      .from('equipment-images')
      .list(`facility_${facilityId}`, {
        search: itemId
      });

    if (existingFiles && existingFiles.length > 0) {
      const filesToRemove = existingFiles.map(x => `facility_${facilityId}/${x.name}`);
      await supabase.storage
        .from('equipment-images')
        .remove(filesToRemove);
    }

    // 新しい画像をアップロード
    const { data, error } = await supabase.storage
      .from('equipment-images')
      .upload(filePath, file, {
        cacheControl: '3600',
        upsert: true
      });

    if (error) {
      console.error('❌ Image upload failed:', error);
      throw error;
    }

    console.log('✅ Image uploaded successfully:', filePath);
    return filePath;

  } catch (error) {
    console.error('❌ Upload error:', error);
    throw error;
  }
}

/**
 * Supabase Storageから画像を削除
 * @param {string} filePath - 削除するファイルのパス
 */
async function deleteImage(filePath) {
  if (!filePath) return;

  try {
    const { error } = await supabase.storage
      .from('equipment-images')
      .remove([filePath]);

    if (error) {
      console.error('❌ Image deletion failed:', error);
      throw error;
    }

    console.log('✅ Image deleted successfully:', filePath);
  } catch (error) {
    console.error('❌ Delete error:', error);
    throw error;
  }
}

/**
 * エラーメッセージを表示
 * @param {string} message - エラーメッセージ
 */
function showError(message) {
  // この関数は後でUIコンポーネントと連携します
  console.error(message);
  alert(message);
}

/**
 * デバッグモード設定
 */
const DEBUG_MODE = window.location.hostname === 'localhost' ||
                   window.location.hostname === '127.0.0.1';

/**
 * デバッグログを出力
 */
function debugLog(...args) {
  if (DEBUG_MODE) {
    console.log('[StockEasy Debug]', ...args);
  }
}

// グローバルに公開
window.StockEasySupabase = {
  initSupabase,
  getCurrentSession,
  getCurrentUser,
  getImageUrl,
  uploadImage,
  deleteImage,
  debugLog,
  get client() {
    return supabase;
  }
};
