-- StockEasy Initial Schema Migration
-- このファイルをSupabaseダッシュボードのSQL Editorで実行してください

-- ====================================
-- 1. テーブル作成
-- ====================================

-- 施設テーブル
CREATE TABLE IF NOT EXISTS facilities (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) DEFAULT '',
    phone VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- ユーザーテーブル（職員・管理者）
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT REFERENCES facilities(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'staff' CHECK (role IN ('staff', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(facility_id, username)
);

-- システム管理者テーブル
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 備品テーブル
CREATE TABLE IF NOT EXISTS equipment (
    id BIGSERIAL PRIMARY KEY,
    item_id VARCHAR(50) NOT NULL,
    facility_id BIGINT REFERENCES facilities(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    location VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    current_location VARCHAR(100) DEFAULT '',
    user_location VARCHAR(100) DEFAULT '',
    status VARCHAR(50) DEFAULT '待機',
    note TEXT DEFAULT '',
    image_url TEXT DEFAULT '',  -- Supabase Storageへのパス
    history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(facility_id, item_id)
);

-- ====================================
-- 2. インデックス作成（パフォーマンス向上）
-- ====================================

CREATE INDEX IF NOT EXISTS idx_equipment_facility_id ON equipment(facility_id);
CREATE INDEX IF NOT EXISTS idx_equipment_item_id ON equipment(item_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category);
CREATE INDEX IF NOT EXISTS idx_users_facility_id ON users(facility_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ====================================
-- 3. updated_at自動更新トリガー
-- ====================================

-- トリガー関数を作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- equipmentテーブルにトリガーを設定
DROP TRIGGER IF EXISTS update_equipment_updated_at ON equipment;
CREATE TRIGGER update_equipment_updated_at
    BEFORE UPDATE ON equipment
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- 4. デフォルトデータの挿入
-- ====================================

-- デフォルト管理者アカウントを作成（パスワード: admin123）
-- 注意: 本番環境では必ずパスワードを変更してください
INSERT INTO admin_users (username, password_hash)
VALUES ('admin', '$pbkdf2-sha256$29000$N.ZcS.mdI4RwTgkhpJQSwg$VY8KfKc0FkD8bBvKpYnqRu6Kg9xU9nP5xWKxYkPqNR0')
ON CONFLICT (username) DO NOTHING;

-- サンプル施設（テスト用 - 必要に応じて削除）
INSERT INTO facilities (name, address, phone)
VALUES
    ('サンプル施設A', '東京都渋谷区1-2-3', '03-1234-5678'),
    ('サンプル施設B', '大阪府大阪市2-3-4', '06-2345-6789')
ON CONFLICT DO NOTHING;

-- ====================================
-- 5. コメント追加（ドキュメント化）
-- ====================================

COMMENT ON TABLE facilities IS '施設情報テーブル';
COMMENT ON TABLE users IS '施設ユーザー（職員・管理者）テーブル';
COMMENT ON TABLE admin_users IS 'システム管理者テーブル';
COMMENT ON TABLE equipment IS '備品管理テーブル';

COMMENT ON COLUMN equipment.item_id IS '備品ID（施設内でユニーク）';
COMMENT ON COLUMN equipment.image_url IS 'Supabase Storageの画像パス（例: equipment-images/facility_1/item_001.jpg）';
COMMENT ON COLUMN equipment.history IS '備品の履歴をJSON形式で保存';
