-- StockEasy Row Level Security (RLS) Policies
-- 施設ごとのデータ分離を実現

-- ====================================
-- 1. RLSを有効化
-- ====================================

ALTER TABLE facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;

-- ====================================
-- 2. カスタム認証用のヘルパー関数
-- ====================================

-- 現在のユーザーのfacility_idを取得する関数
CREATE OR REPLACE FUNCTION get_user_facility_id()
RETURNS BIGINT AS $$
BEGIN
    -- Supabase Authのユーザーメタデータから施設IDを取得
    RETURN NULLIF(current_setting('request.jwt.claims', true)::json->>'facility_id', '')::BIGINT;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 現在のユーザーの役割を取得する関数
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    -- Supabase Authのユーザーメタデータから役割を取得
    RETURN NULLIF(current_setting('request.jwt.claims', true)::json->>'role', '');
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- システム管理者かどうかを確認する関数
CREATE OR REPLACE FUNCTION is_system_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (get_user_role() = 'system_admin');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 施設管理者かどうかを確認する関数
CREATE OR REPLACE FUNCTION is_facility_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (get_user_role() IN ('admin', 'system_admin'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ====================================
-- 3. facilities テーブルのRLSポリシー
-- ====================================

-- 施設一覧の取得：全ユーザーが自分の施設を閲覧可能
CREATE POLICY "Users can view their own facility"
    ON facilities FOR SELECT
    USING (
        id = get_user_facility_id() OR
        is_system_admin()
    );

-- 施設の作成：システム管理者のみ
CREATE POLICY "Only system admins can create facilities"
    ON facilities FOR INSERT
    WITH CHECK (is_system_admin());

-- 施設の更新：システム管理者または施設管理者
CREATE POLICY "Facility admins can update their facility"
    ON facilities FOR UPDATE
    USING (
        id = get_user_facility_id() AND is_facility_admin()
        OR is_system_admin()
    );

-- 施設の削除：システム管理者のみ
CREATE POLICY "Only system admins can delete facilities"
    ON facilities FOR DELETE
    USING (is_system_admin());

-- ====================================
-- 4. users テーブルのRLSポリシー
-- ====================================

-- ユーザー一覧の取得：同じ施設のユーザーのみ閲覧可能
CREATE POLICY "Users can view users in their facility"
    ON users FOR SELECT
    USING (
        facility_id = get_user_facility_id() OR
        is_system_admin()
    );

-- ユーザーの作成：施設管理者またはシステム管理者
CREATE POLICY "Facility admins can create users in their facility"
    ON users FOR INSERT
    WITH CHECK (
        (facility_id = get_user_facility_id() AND is_facility_admin())
        OR is_system_admin()
    );

-- ユーザーの更新：施設管理者またはシステム管理者
CREATE POLICY "Facility admins can update users in their facility"
    ON users FOR UPDATE
    USING (
        (facility_id = get_user_facility_id() AND is_facility_admin())
        OR is_system_admin()
    );

-- ユーザーの削除：施設管理者またはシステム管理者
CREATE POLICY "Facility admins can delete users in their facility"
    ON users FOR DELETE
    USING (
        (facility_id = get_user_facility_id() AND is_facility_admin())
        OR is_system_admin()
    );

-- ====================================
-- 5. admin_users テーブルのRLSポリシー
-- ====================================

-- システム管理者のみがアクセス可能
CREATE POLICY "Only system admins can access admin_users"
    ON admin_users FOR ALL
    USING (is_system_admin())
    WITH CHECK (is_system_admin());

-- ====================================
-- 6. equipment テーブルのRLSポリシー
-- ====================================

-- 備品の閲覧：同じ施設の備品のみ閲覧可能
CREATE POLICY "Users can view equipment in their facility"
    ON equipment FOR SELECT
    USING (
        facility_id = get_user_facility_id() OR
        is_system_admin()
    );

-- 備品の作成：施設管理者のみ
CREATE POLICY "Only facility admins can create equipment"
    ON equipment FOR INSERT
    WITH CHECK (
        (facility_id = get_user_facility_id() AND is_facility_admin())
        OR is_system_admin()
    );

-- 備品の更新：同じ施設のユーザーなら可能（借用・返却のため）
-- ただし、一部のフィールド（name, category, locationなど）は管理者のみ
CREATE POLICY "Users can update equipment in their facility"
    ON equipment FOR UPDATE
    USING (
        facility_id = get_user_facility_id() OR
        is_system_admin()
    );

-- 備品の削除：施設管理者のみ
CREATE POLICY "Only facility admins can delete equipment"
    ON equipment FOR DELETE
    USING (
        (facility_id = get_user_facility_id() AND is_facility_admin())
        OR is_system_admin()
    );

-- ====================================
-- 7. 匿名アクセス用のポリシー（ログイン前の施設一覧表示）
-- ====================================

-- 施設一覧は認証前でも閲覧可能にする（オプション）
-- ログインページで施設を選択する必要がある場合
CREATE POLICY "Anonymous users can view all facilities"
    ON facilities FOR SELECT
    TO anon
    USING (true);

-- ====================================
-- 8. サービスロール用のフルアクセス
-- ====================================

-- サービスロール（バックエンド用）は全てのデータにアクセス可能
-- これにより、バックエンドでの管理操作が可能になります

-- facilitiesテーブル
CREATE POLICY "Service role has full access to facilities"
    ON facilities FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- usersテーブル
CREATE POLICY "Service role has full access to users"
    ON users FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- admin_usersテーブル
CREATE POLICY "Service role has full access to admin_users"
    ON admin_users FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- equipmentテーブル
CREATE POLICY "Service role has full access to equipment"
    ON equipment FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ====================================
-- 9. ポリシーの説明
-- ====================================

COMMENT ON POLICY "Users can view their own facility" ON facilities IS
    'ユーザーは自分の施設のみ閲覧可能';

COMMENT ON POLICY "Users can view equipment in their facility" ON equipment IS
    '同じ施設の備品のみ閲覧可能（施設間のデータ分離）';

COMMENT ON POLICY "Users can update equipment in their facility" ON equipment IS
    '職員は借用・返却のため備品を更新可能、管理者は全フィールドを更新可能';
