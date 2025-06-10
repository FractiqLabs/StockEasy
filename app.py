from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 本番環境対応
if os.environ.get('ENVIRONMENT') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = True

# 本番環境でHTTPS強制
@app.before_request
def force_https():
    if os.environ.get('ENVIRONMENT') == 'production':
        if request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

# データベース初期化
def init_db():
    try:
        conn = sqlite3.connect('equipment.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT NOT NULL,
                current_location TEXT DEFAULT '',
                user_location TEXT DEFAULT '',
                status TEXT DEFAULT '待機',
                note TEXT DEFAULT '',
                image TEXT DEFAULT '',
                history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("データベース初期化完了")
    except Exception as e:
        print(f"データベース初期化エラー: {e}")

# データベース接続のヘルパー関数
def get_db_connection():
    try:
        conn = sqlite3.connect('equipment.db')
        conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
        return conn
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

# 静的ファイル配信（HTML）
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

# テスト用エンドポイント
@app.route('/api/test')
def test_api():
    return jsonify({'status': 'OK', 'message': 'APIは正常に動作しています'})

# ヘルスチェック用
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ファビコンやその他の静的ファイル配信
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# 全備品データ取得
@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM equipment ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        equipment_list = []
        for row in rows:
            try:
                history_data = json.loads(row['history']) if row['history'] else []
            except:
                history_data = []
                
            equipment = {
                'name': row['name'],
                'id': row['item_id'],
                'location': row['location'],
                'category': row['category'],
                'current': row['current_location'] or '',
                'user': row['user_location'] or '',
                'status': row['status'],
                'note': row['note'] or '',
                'image': row['image'] or '',
                'history': history_data,
                'createdAt': row['created_at']
            }
            equipment_list.append(equipment)
        
        conn.close()
        return jsonify(equipment_list)
        
    except Exception as e:
        print(f"備品データ取得エラー: {e}")
        return jsonify({'error': 'データ取得に失敗しました', 'details': str(e)}), 500

# 新規備品登録
@app.route('/api/equipment', methods=['POST'])
def create_equipment():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'データが送信されていません'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO equipment (
                item_id, name, location, category, image, history
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('id', ''),
            data.get('name', ''),
            data.get('location', ''),
            data.get('category', ''),
            data.get('image', ''),
            json.dumps(data.get('history', []))
        ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '備品が登録されました'})
        
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': 'このIDは既に使用されています'}), 400
    except Exception as e:
        if conn:
            conn.close()
        print(f"備品登録エラー: {e}")
        return jsonify({'success': False, 'message': f'登録に失敗しました: {str(e)}'}), 500

# 備品情報更新
@app.route('/api/equipment/<item_id>', methods=['PUT'])
def update_equipment(item_id):
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 更新するフィールドを動的に構築
    update_fields = []
    values = []
    
    if 'name' in data:
        update_fields.append('name = ?')
        values.append(data['name'])
    if 'location' in data:
        update_fields.append('location = ?')
        values.append(data['location'])
    if 'category' in data:
        update_fields.append('category = ?')
        values.append(data['category'])
    if 'current' in data:
        update_fields.append('current_location = ?')
        values.append(data['current'])
    if 'user' in data:
        update_fields.append('user_location = ?')
        values.append(data['user'])
    if 'status' in data:
        update_fields.append('status = ?')
        values.append(data['status'])
    if 'note' in data:
        update_fields.append('note = ?')
        values.append(data['note'])
    if 'image' in data:
        update_fields.append('image = ?')
        values.append(data['image'])
    if 'history' in data:
        update_fields.append('history = ?')
        values.append(json.dumps(data['history']))
    
    # updated_atを追加
    update_fields.append('updated_at = CURRENT_TIMESTAMP')
    values.append(item_id)
    
    query = f'UPDATE equipment SET {", ".join(update_fields)} WHERE item_id = ?'
    
    cursor.execute(query, values)
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': '備品が見つかりません'}), 404
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '備品情報が更新されました'})

# 備品削除
@app.route('/api/equipment/<item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM equipment WHERE item_id = ?', (item_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': '備品が見つかりません'}), 404
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '備品が削除されました'})

# データエクスポート
@app.route('/api/export', methods=['GET'])
def export_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM equipment')
    rows = cursor.fetchall()
    
    equipment_list = []
    for row in rows:
        equipment = {
            'name': row['name'],
            'id': row['item_id'],
            'location': row['location'],
            'category': row['category'],
            'current': row['current_location'],
            'user': row['user_location'],
            'status': row['status'],
            'note': row['note'],
            'image': row['image'],
            'history': json.loads(row['history']) if row['history'] else [],
            'createdAt': row['created_at']
        }
        equipment_list.append(equipment)
    
    conn.close()
    return jsonify(equipment_list)

# データインポート
@app.route('/api/import', methods=['POST'])
def import_data():
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 既存データを削除
        cursor.execute('DELETE FROM equipment')
        
        # 新しいデータを挿入
        for item in data:
            cursor.execute('''
                INSERT INTO equipment (
                    item_id, name, location, category, current_location,
                    user_location, status, note, image, history
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['id'],
                item['name'],
                item['location'],
                item['category'],
                item.get('current', ''),
                item.get('user', ''),
                item.get('status', '待機'),
                item.get('note', ''),
                item.get('image', ''),
                json.dumps(item.get('history', []))
            ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'データがインポートされました'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'インポートに失敗しました: {str(e)}'}), 400

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0' if os.environ.get('ENVIRONMENT') == 'production' else '127.0.0.1'
    app.run(debug=app.config['DEBUG'], host=host, port=port)
