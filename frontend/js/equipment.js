/**
 * StockEasy - Equipment Management Module
 * 備品管理のCRUD操作
 */

/**
 * 備品一覧を取得
 * @param {object} filters - フィルタ条件 {category, status, searchTerm}
 */
async function getEquipment(filters = {}) {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId && !window.StockEasyAuth.isSystemAdmin()) {
      throw new Error('施設IDが設定されていません');
    }

    let query = window.StockEasySupabase.client
      .from('equipment')
      .select('*')
      .order('created_at', { ascending: false });

    // 施設フィルタ（システム管理者以外）
    if (facilityId) {
      query = query.eq('facility_id', facilityId);
    }

    // カテゴリフィルタ
    if (filters.category && filters.category !== 'all') {
      query = query.eq('category', filters.category);
    }

    // ステータスフィルタ
    if (filters.status && filters.status !== 'all') {
      query = query.eq('status', filters.status);
    }

    // 検索フィルタ
    if (filters.searchTerm) {
      query = query.or(`name.ilike.%${filters.searchTerm}%,item_id.ilike.%${filters.searchTerm}%`);
    }

    const { data, error } = await query;

    if (error) throw error;

    // 画像URLを変換
    const equipmentWithImages = data.map(item => ({
      ...item,
      image: item.image_url ? window.StockEasySupabase.getImageUrl(item.image_url) : ''
    }));

    return equipmentWithImages;

  } catch (error) {
    console.error('❌ Failed to get equipment:', error);
    throw error;
  }
}

/**
 * 備品を新規登録
 * @param {object} equipmentData - 備品データ
 */
async function createEquipment(equipmentData) {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    // 管理者権限チェック
    if (!window.StockEasyAuth.isAdmin()) {
      throw new Error('管理者権限が必要です');
    }

    // 画像のアップロード（ある場合）
    let imageUrl = '';
    if (equipmentData.imageFile) {
      imageUrl = await window.StockEasySupabase.uploadImage(
        equipmentData.imageFile,
        facilityId,
        equipmentData.item_id
      );
    }

    // 備品データを挿入
    const { data, error } = await window.StockEasySupabase.client
      .from('equipment')
      .insert([{
        facility_id: facilityId,
        item_id: equipmentData.item_id,
        name: equipmentData.name,
        location: equipmentData.location,
        category: equipmentData.category,
        current_location: equipmentData.current_location || '',
        user_location: equipmentData.user_location || '',
        status: equipmentData.status || '待機',
        note: equipmentData.note || '',
        image_url: imageUrl,
        history: equipmentData.history || []
      }])
      .select();

    if (error) throw error;

    console.log('✅ Equipment created successfully:', data[0].id);

    return { success: true, data: data[0] };

  } catch (error) {
    console.error('❌ Failed to create equipment:', error);
    return {
      success: false,
      message: error.message || '備品の登録に失敗しました'
    };
  }
}

/**
 * 備品情報を更新
 * @param {string} itemId - 備品ID
 * @param {object} updates - 更新データ
 */
async function updateEquipment(itemId, updates) {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    // 管理者のみが編集可能なフィールド
    const adminOnlyFields = ['name', 'category', 'location', 'item_id'];
    const hasAdminOnlyFields = Object.keys(updates).some(key =>
      adminOnlyFields.includes(key)
    );

    // 管理者権限チェック（管理者専用フィールドの更新時）
    if (hasAdminOnlyFields && !window.StockEasyAuth.isAdmin()) {
      throw new Error('管理者権限が必要です');
    }

    // 画像の更新（ある場合）
    if (updates.imageFile) {
      const imageUrl = await window.StockEasySupabase.uploadImage(
        updates.imageFile,
        facilityId,
        itemId
      );
      updates.image_url = imageUrl;
      delete updates.imageFile;
    }

    // 備品データを更新
    const { data, error } = await window.StockEasySupabase.client
      .from('equipment')
      .update(updates)
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .select();

    if (error) throw error;

    if (!data || data.length === 0) {
      throw new Error('備品が見つかりません');
    }

    console.log('✅ Equipment updated successfully:', itemId);

    return { success: true, data: data[0] };

  } catch (error) {
    console.error('❌ Failed to update equipment:', error);
    return {
      success: false,
      message: error.message || '備品の更新に失敗しました'
    };
  }
}

/**
 * 備品を削除
 * @param {string} itemId - 備品ID
 */
async function deleteEquipment(itemId) {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    // 管理者権限チェック
    if (!window.StockEasyAuth.isAdmin()) {
      throw new Error('管理者権限が必要です');
    }

    // 備品情報を取得（画像削除のため）
    const { data: equipment, error: fetchError } = await window.StockEasySupabase.client
      .from('equipment')
      .select('image_url')
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .single();

    if (fetchError) throw fetchError;

    // 画像を削除
    if (equipment.image_url) {
      await window.StockEasySupabase.deleteImage(equipment.image_url);
    }

    // 備品を削除
    const { error } = await window.StockEasySupabase.client
      .from('equipment')
      .delete()
      .eq('facility_id', facilityId)
      .eq('item_id', itemId);

    if (error) throw error;

    console.log('✅ Equipment deleted successfully:', itemId);

    return { success: true };

  } catch (error) {
    console.error('❌ Failed to delete equipment:', error);
    return {
      success: false,
      message: error.message || '備品の削除に失敗しました'
    };
  }
}

/**
 * 備品を借用
 * @param {string} itemId - 備品ID
 * @param {string} userName - 借用者名
 * @param {string} userLocation - 借用先（部屋番号など）
 */
async function borrowEquipment(itemId, userName, userLocation) {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    // 現在の備品情報を取得
    const { data: equipment, error: fetchError } = await window.StockEasySupabase.client
      .from('equipment')
      .select('*')
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .single();

    if (fetchError) throw fetchError;

    if (equipment.status !== '待機') {
      throw new Error('この備品は既に借用されています');
    }

    // 履歴に追加
    const history = equipment.history || [];
    history.push({
      action: 'borrow',
      user: userName,
      location: userLocation,
      timestamp: new Date().toISOString()
    });

    // 備品を更新
    const { data, error } = await window.StockEasySupabase.client
      .from('equipment')
      .update({
        status: '使用中',
        user_location: userName,
        current_location: userLocation,
        history: history
      })
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .select();

    if (error) throw error;

    console.log('✅ Equipment borrowed successfully:', itemId);

    return { success: true, data: data[0] };

  } catch (error) {
    console.error('❌ Failed to borrow equipment:', error);
    return {
      success: false,
      message: error.message || '備品の借用に失敗しました'
    };
  }
}

/**
 * 備品を返却
 * @param {string} itemId - 備品ID
 * @param {string} note - 備考（オプション）
 */
async function returnEquipment(itemId, note = '') {
  try {
    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    // 現在の備品情報を取得
    const { data: equipment, error: fetchError } = await window.StockEasySupabase.client
      .from('equipment')
      .select('*')
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .single();

    if (fetchError) throw fetchError;

    if (equipment.status !== '使用中') {
      throw new Error('この備品は借用されていません');
    }

    // 履歴に追加
    const history = equipment.history || [];
    history.push({
      action: 'return',
      user: equipment.user_location,
      location: equipment.current_location,
      note: note,
      timestamp: new Date().toISOString()
    });

    // 備品を更新
    const { data, error } = await window.StockEasySupabase.client
      .from('equipment')
      .update({
        status: '待機',
        user_location: '',
        current_location: equipment.location, // 元の場所に戻す
        note: note,
        history: history
      })
      .eq('facility_id', facilityId)
      .eq('item_id', itemId)
      .select();

    if (error) throw error;

    console.log('✅ Equipment returned successfully:', itemId);

    return { success: true, data: data[0] };

  } catch (error) {
    console.error('❌ Failed to return equipment:', error);
    return {
      success: false,
      message: error.message || '備品の返却に失敗しました'
    };
  }
}

/**
 * データをエクスポート（JSON形式）
 */
async function exportData() {
  try {
    const equipment = await getEquipment();

    const dataStr = JSON.stringify(equipment, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `stockeasy_export_${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    URL.revokeObjectURL(url);

    console.log('✅ Data exported successfully');

    return { success: true };

  } catch (error) {
    console.error('❌ Failed to export data:', error);
    return {
      success: false,
      message: error.message || 'データのエクスポートに失敗しました'
    };
  }
}

/**
 * データをインポート（JSON形式）
 * @param {File} file - インポートするJSONファイル
 */
async function importData(file) {
  try {
    // 管理者権限チェック
    if (!window.StockEasyAuth.isAdmin()) {
      throw new Error('管理者権限が必要です');
    }

    const facilityId = window.StockEasyAuth.getCurrentFacilityId();

    if (!facilityId) {
      throw new Error('施設IDが設定されていません');
    }

    const reader = new FileReader();

    return new Promise((resolve, reject) => {
      reader.onload = async (e) => {
        try {
          const data = JSON.parse(e.target.result);

          if (!Array.isArray(data)) {
            throw new Error('無効なデータ形式です');
          }

          // 各備品をインポート
          const results = [];
          for (const item of data) {
            // facility_idを現在の施設IDで上書き
            item.facility_id = facilityId;

            const result = await createEquipment(item);
            results.push(result);
          }

          const successCount = results.filter(r => r.success).length;
          const failCount = results.length - successCount;

          console.log(`✅ Data imported: ${successCount} success, ${failCount} failed`);

          resolve({
            success: true,
            message: `${successCount}件のデータをインポートしました`,
            successCount,
            failCount
          });

        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => {
        reject(new Error('ファイルの読み込みに失敗しました'));
      };

      reader.readAsText(file);
    });

  } catch (error) {
    console.error('❌ Failed to import data:', error);
    return {
      success: false,
      message: error.message || 'データのインポートに失敗しました'
    };
  }
}

// グローバルに公開
window.StockEasyEquipment = {
  getEquipment,
  createEquipment,
  updateEquipment,
  deleteEquipment,
  borrowEquipment,
  returnEquipment,
  exportData,
  importData
};
