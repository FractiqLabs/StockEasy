-- StockEasy Storage Setup
-- 備品画像用のSupabase Storage設定

-- ====================================
-- 1. Storageバケットの作成
-- ====================================

-- equipment-images バケットを作成
-- 注意: この操作はSupabaseダッシュボードのStorageセクションでも実行可能です
INSERT INTO storage.buckets (id, name, public)
VALUES ('equipment-images', 'equipment-images', true)
ON CONFLICT (id) DO NOTHING;

-- ====================================
-- 2. Storage RLSポリシー
-- ====================================

-- 画像の閲覧：認証済みユーザーは自分の施設の画像を閲覧可能
CREATE POLICY "Users can view images in their facility"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'equipment-images' AND
        (
            -- パスが facility_<ID>/ で始まる場合、そのIDが自分の施設IDと一致する
            (storage.foldername(name))[1] = 'facility_' || get_user_facility_id()::TEXT
            OR is_system_admin()
        )
    );

-- 画像のアップロード：認証済みユーザーは自分の施設フォルダにのみアップロード可能
CREATE POLICY "Users can upload images to their facility folder"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'equipment-images' AND
        (
            (storage.foldername(name))[1] = 'facility_' || get_user_facility_id()::TEXT
            OR is_system_admin()
        )
    );

-- 画像の更新：認証済みユーザーは自分の施設の画像を更新可能
CREATE POLICY "Users can update images in their facility"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'equipment-images' AND
        (
            (storage.foldername(name))[1] = 'facility_' || get_user_facility_id()::TEXT
            OR is_system_admin()
        )
    );

-- 画像の削除：施設管理者またはシステム管理者のみ削除可能
CREATE POLICY "Facility admins can delete images in their facility"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'equipment-images' AND
        (
            ((storage.foldername(name))[1] = 'facility_' || get_user_facility_id()::TEXT AND is_facility_admin())
            OR is_system_admin()
        )
    );

-- ====================================
-- 3. 匿名アクセス（公開画像）
-- ====================================

-- 公開設定のバケットなので、画像URLは誰でもアクセス可能
-- ただし、直接URLを知っている人のみアクセス可能（セキュリティ上問題なし）

-- ====================================
-- 4. フォルダ構造の説明
-- ====================================

-- 推奨フォルダ構造:
-- equipment-images/
--   ├── facility_1/
--   │   ├── item_001.jpg
--   │   ├── item_002.png
--   │   └── ...
--   ├── facility_2/
--   │   ├── item_001.jpg
--   │   └── ...
--   └── ...

-- 画像URLの例:
-- https://<project-id>.supabase.co/storage/v1/object/public/equipment-images/facility_1/item_001.jpg

COMMENT ON TABLE storage.objects IS
    '備品画像は equipment-images バケットに保存される。フォルダ構造: facility_<id>/<item_id>.jpg';
