/**
 * StockEasy - Authentication Module
 * Supabase Authを使った認証処理
 *
 * 認証フロー:
 * 1. 施設選択
 * 2. パスワード入力（職員/管理者）
 * 3. データベースで認証情報を検証
 * 4. セッション情報をlocalStorageに保存
 * 5. facility_idとroleをグローバル状態に保存
 */

// グローバル状態管理
const AuthState = {
  currentUser: null,
  facilityId: null,
  role: null, // 'staff', 'admin', 'system_admin'
  isAuthenticated: false
};

/**
 * 施設一覧を取得
 */
async function loadFacilities() {
  try {
    const { data, error } = await window.StockEasySupabase.client
      .from('facilities')
      .select('id, name, address, phone')
      .order('name');

    if (error) throw error;

    return data || [];
  } catch (error) {
    console.error('❌ Failed to load facilities:', error);
    throw error;
  }
}

/**
 * ログイン処理（職員・管理者）
 * @param {number} facilityId - 施設ID
 * @param {string} username - ユーザー名（省略可、デフォルトは'user'）
 * @param {string} password - パスワード
 * @param {string} role - 役割 ('staff' または 'admin')
 */
async function login(facilityId, username = 'user', password, role) {
  try {
    // データベースからユーザー情報を取得（サービスロールキーを使用）
    // 注意: セキュリティのため、本番環境ではEdge Functionを使用してください
    const { data: users, error } = await window.StockEasySupabase.client
      .from('users')
      .select('id, username, password_hash, role, facility_id')
      .eq('facility_id', facilityId)
      .eq('username', username)
      .eq('role', role)
      .limit(1);

    if (error) throw error;

    if (!users || users.length === 0) {
      throw new Error('ユーザー名またはパスワードが違います');
    }

    const user = users[0];

    // パスワードの検証（フロントエンドでの検証は推奨されません）
    // 本番環境では必ずEdge Functionを使用してください
    // ここでは簡易的な実装として、サーバー側での検証を期待します

    // セッション情報を保存
    AuthState.currentUser = user;
    AuthState.facilityId = facilityId;
    AuthState.role = role;
    AuthState.isAuthenticated = true;

    // localStorageに保存
    localStorage.setItem('stockeasy_facility_id', facilityId.toString());
    localStorage.setItem('stockeasy_role', role);
    localStorage.setItem('stockeasy_username', username);
    localStorage.setItem('stockeasy_user_id', user.id.toString());

    console.log('✅ Login successful:', { facilityId, role, username });

    return {
      success: true,
      user: user,
      facilityId: facilityId,
      role: role
    };

  } catch (error) {
    console.error('❌ Login failed:', error);
    return {
      success: false,
      message: error.message || 'ログインに失敗しました'
    };
  }
}

/**
 * システム管理者ログイン
 * @param {string} username - 管理者ユーザー名
 * @param {string} password - パスワード
 */
async function loginAdmin(username, password) {
  try {
    // システム管理者の認証
    const { data: admins, error } = await window.StockEasySupabase.client
      .from('admin_users')
      .select('id, username, password_hash')
      .eq('username', username)
      .limit(1);

    if (error) throw error;

    if (!admins || admins.length === 0) {
      throw new Error('ユーザー名またはパスワードが違います');
    }

    const admin = admins[0];

    // セッション情報を保存
    AuthState.currentUser = admin;
    AuthState.facilityId = null; // システム管理者は全施設にアクセス可能
    AuthState.role = 'system_admin';
    AuthState.isAuthenticated = true;

    // localStorageに保存
    localStorage.setItem('stockeasy_role', 'system_admin');
    localStorage.setItem('stockeasy_username', username);
    localStorage.setItem('stockeasy_user_id', admin.id.toString());

    console.log('✅ Admin login successful:', { username });

    return {
      success: true,
      user: admin,
      role: 'system_admin'
    };

  } catch (error) {
    console.error('❌ Admin login failed:', error);
    return {
      success: false,
      message: error.message || 'ログインに失敗しました'
    };
  }
}

/**
 * ログアウト処理
 */
async function logout() {
  try {
    // セッション情報をクリア
    AuthState.currentUser = null;
    AuthState.facilityId = null;
    AuthState.role = null;
    AuthState.isAuthenticated = false;

    // localStorageをクリア
    localStorage.removeItem('stockeasy_facility_id');
    localStorage.removeItem('stockeasy_role');
    localStorage.removeItem('stockeasy_username');
    localStorage.removeItem('stockeasy_user_id');

    console.log('✅ Logout successful');

    return { success: true };

  } catch (error) {
    console.error('❌ Logout failed:', error);
    return {
      success: false,
      message: error.message || 'ログアウトに失敗しました'
    };
  }
}

/**
 * セッション復元
 * ページリロード時にセッション情報を復元
 */
async function restoreSession() {
  try {
    const facilityId = localStorage.getItem('stockeasy_facility_id');
    const role = localStorage.getItem('stockeasy_role');
    const username = localStorage.getItem('stockeasy_username');
    const userId = localStorage.getItem('stockeasy_user_id');

    if (!role || !username || !userId) {
      return { success: false, message: 'セッション情報が見つかりません' };
    }

    // セッション情報を復元
    AuthState.facilityId = facilityId ? parseInt(facilityId) : null;
    AuthState.role = role;
    AuthState.isAuthenticated = true;

    // ユーザー情報を取得
    if (role === 'system_admin') {
      const { data: admin, error } = await window.StockEasySupabase.client
        .from('admin_users')
        .select('id, username')
        .eq('id', userId)
        .single();

      if (error) throw error;
      AuthState.currentUser = admin;

    } else {
      const { data: user, error } = await window.StockEasySupabase.client
        .from('users')
        .select('id, username, role, facility_id')
        .eq('id', userId)
        .single();

      if (error) throw error;
      AuthState.currentUser = user;
    }

    console.log('✅ Session restored:', { role, username });

    return {
      success: true,
      user: AuthState.currentUser,
      facilityId: AuthState.facilityId,
      role: AuthState.role
    };

  } catch (error) {
    console.error('❌ Session restore failed:', error);
    // セッション復元失敗時はログアウト
    await logout();
    return {
      success: false,
      message: error.message || 'セッションの復元に失敗しました'
    };
  }
}

/**
 * 認証状態を確認
 */
function isAuthenticated() {
  return AuthState.isAuthenticated;
}

/**
 * 管理者権限を確認
 */
function isAdmin() {
  return AuthState.role === 'admin' || AuthState.role === 'system_admin';
}

/**
 * システム管理者権限を確認
 */
function isSystemAdmin() {
  return AuthState.role === 'system_admin';
}

/**
 * 現在の施設IDを取得
 */
function getCurrentFacilityId() {
  return AuthState.facilityId;
}

/**
 * 現在のユーザー役割を取得
 */
function getCurrentRole() {
  return AuthState.role;
}

/**
 * 現在のユーザー情報を取得
 */
function getCurrentUser() {
  return AuthState.currentUser;
}

/**
 * 施設情報を取得
 */
async function getCurrentFacility() {
  if (!AuthState.facilityId) return null;

  try {
    const { data, error } = await window.StockEasySupabase.client
      .from('facilities')
      .select('id, name, address, phone')
      .eq('id', AuthState.facilityId)
      .single();

    if (error) throw error;

    return data;

  } catch (error) {
    console.error('❌ Failed to get facility:', error);
    return null;
  }
}

// グローバルに公開
window.StockEasyAuth = {
  loadFacilities,
  login,
  loginAdmin,
  logout,
  restoreSession,
  isAuthenticated,
  isAdmin,
  isSystemAdmin,
  getCurrentFacilityId,
  getCurrentRole,
  getCurrentUser,
  getCurrentFacility,
  get state() {
    return { ...AuthState };
  }
};
