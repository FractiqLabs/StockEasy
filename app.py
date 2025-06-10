from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # CORSを有効にする

# 本番環境でHTTPS強制
@app.before_request
def force_https():
    if os.environ.get('ENVIRONMENT') == 'production':
        if request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

# ルート（/）でstatic/index.htmlを返す
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 他の静的ファイル用
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)
def init_db():
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

# データベース接続のヘルパー関数
def get_db_connection():
    conn = sqlite3.connect('equipment.db')
    conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
    return conn

# 静的ファイル配信（HTML）
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 全備品データ取得

# 全備品データ取得
@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM equipment ORDER BY created_at DESC')
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

# 新規備品登録
@app.route('/api/equipment', methods=['POST'])
def create_equipment():
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO equipment (
                item_id, name, location, category, image, history
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['id'],
            data['name'],
            data['location'],
            data['category'],
            data.get('image', ''),
            json.dumps(data.get('history', []))
        ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '備品が登録されました'})
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'このIDは既に使用されています'}), 400

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
