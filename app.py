from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# JSON文字化け対策
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# 本番環境対応
if os.environ.get('ENVIRONMENT') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = True

# データベース接続設定
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    # Render.comの場合、postgres://をpostgresql://に変更
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# 本番環境でHTTPS強制
@app.before_request
def force_https():
    if os.environ.get('ENVIRONMENT') == 'production':
        if request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'), code=301)

# データベース接続のヘルパー関数
def get_db_connection():
    try:
        if DATABASE_URL:
            # PostgreSQL接続
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            # ローカル開発用（SQLiteフォールバック）
            import sqlite3
            conn = sqlite3.connect('equipment.db')
            conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return None

# データベース初期化（PostgreSQL版）
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            # PostgreSQL用のテーブル作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id SERIAL PRIMARY KEY,
                    item_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    location VARCHAR(100) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    current_location VARCHAR(100) DEFAULT '',
                    user_location VARCHAR(100) DEFAULT '',
                    status VARCHAR(50) DEFAULT '待機',
                    note TEXT DEFAULT '',
                    image TEXT DEFAULT '',
                    history TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # SQLite用（ローカル開発）
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
# 管理者パスワードテーブルを追加
        if DATABASE_URL:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # デフォルト管理者アカウントを作成
        hashed_password = generate_password_hash('admin123')
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash) 
                VALUES (%s, %s) 
                ON CONFLICT (username) DO NOTHING
            ''', ('admin', hashed_password))
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO admin_users (username, password_hash) 
                VALUES (?, ?)
            ''', ('admin', hashed_password))

        
        conn.commit()
        cursor.close()
        conn.close()
        print("データベース初期化完了")
    except Exception as e:
        print(f"データベース初期化エラー: {e}")
        if conn:
            conn.close()

# 静的ファイル配信
@app.route('/')
@app.route('/<path:path>')
def home(path=''):
    try:
        if path.startswith('api/') or path.startswith('static/'):
            return '', 404
        return send_from_directory('static', 'index.html')
    except Exception as e:
        print(f"Static file error: {e}")
        return 'ファイルが見つかりません', 404

@app.route('/static/<path:filename>')
def static_files(filename):
    try:
        return send_from_directory('static', filename)
    except:
        return f'ファイル {filename} が見つかりません', 404

@app.route('/api/test')
def test_api():
    db_status = "PostgreSQL" if DATABASE_URL else "SQLite（ローカル）"
    return jsonify({
        'status': 'OK', 
        'message': 'APIは正常に動作しています',
        'database': db_status
    })

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# 全備品データ取得
@app.route('/api/equipment', methods=['GET'])
def get_equipment():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM equipment ORDER BY created_at DESC')
        
        if DATABASE_URL:
            # PostgreSQL
            rows = cursor.fetchall()
        else:
            # SQLite
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
                'createdAt': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
            }
            equipment_list.append(equipment)
        
        cursor.close()
        conn.close()
        return jsonify(equipment_list)
        
    except Exception as e:
        print(f"備品データ取得エラー: {e}")
        if conn:
            conn.close()
        return jsonify({'error': 'データ取得に失敗しました', 'details': str(e)}), 500

# 新規備品登録
@app.route('/api/equipment', methods=['POST'])
def create_equipment():
    conn = None
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'データが送信されていません'}), 400
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        
        if DATABASE_URL:
            # PostgreSQL
            cursor.execute('''
                INSERT INTO equipment (
                    item_id, name, location, category, image, history
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                data.get('id', ''),
                data.get('name', ''),
                data.get('location', ''),
                data.get('category', ''),
                data.get('image', ''),
                json.dumps(data.get('history', []))
            ))
        else:
            # SQLite
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
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '備品が登録されました'})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'success': False, 'message': 'このIDは既に使用されています'}), 400
        
        print(f"備品登録エラー: {e}")
        return jsonify({'success': False, 'message': f'登録に失敗しました: {str(e)}'}), 500

# 備品情報更新
@app.route('/api/equipment/<item_id>', methods=['PUT'])
def update_equipment(item_id):
    conn = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新するフィールドを動的に構築
        update_fields = []
        values = []
        
        if DATABASE_URL:
            # PostgreSQL
            param_placeholder = '%s'
        else:
            # SQLite
            param_placeholder = '?'
        
        if 'name' in data:
            update_fields.append(f'name = {param_placeholder}')
            values.append(data['name'])
        if 'location' in data:
            update_fields.append(f'location = {param_placeholder}')
            values.append(data['location'])
        if 'category' in data:
            update_fields.append(f'category = {param_placeholder}')
            values.append(data['category'])
        if 'current' in data:
            update_fields.append(f'current_location = {param_placeholder}')
            values.append(data['current'])
        if 'user' in data:
            update_fields.append(f'user_location = {param_placeholder}')
            values.append(data['user'])
        if 'status' in data:
            update_fields.append(f'status = {param_placeholder}')
            values.append(data['status'])
        if 'note' in data:
            update_fields.append(f'note = {param_placeholder}')
            values.append(data['note'])
        if 'image' in data:
            update_fields.append(f'image = {param_placeholder}')
            values.append(data['image'])
        if 'history' in data:
            update_fields.append(f'history = {param_placeholder}')
            values.append(json.dumps(data['history']))
        
        # updated_atを追加
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(item_id)
        
        query = f'UPDATE equipment SET {", ".join(update_fields)} WHERE item_id = {param_placeholder}'
        
        cursor.execute(query, values)
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '備品が見つかりません'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '備品情報が更新されました'})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"更新エラー: {e}")
        return jsonify({'success': False, 'message': f'更新に失敗しました: {str(e)}'}), 500

# 備品削除
@app.route('/api/equipment/<item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute('DELETE FROM equipment WHERE item_id = %s', (item_id,))
        else:
            cursor.execute('DELETE FROM equipment WHERE item_id = ?', (item_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '備品が見つかりません'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': '備品が削除されました'})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"削除エラー: {e}")
        return jsonify({'success': False, 'message': f'削除に失敗しました: {str(e)}'}), 500

# データエクスポート
@app.route('/api/export', methods=['GET'])
def export_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM equipment')
        
        if DATABASE_URL:
            rows = cursor.fetchall()
        else:
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
                'createdAt': row['created_at'].isoformat() if hasattr(row['created_at'], 'isoformat') else str(row['created_at'])
            }
            equipment_list.append(equipment)
        
        cursor.close()
        conn.close()
        return jsonify(equipment_list)
        
    except Exception as e:
        if conn:
            conn.close()
        print(f"エクスポートエラー: {e}")
        return jsonify({'error': 'エクスポートに失敗しました', 'details': str(e)}), 500

# データインポート
@app.route('/api/import', methods=['POST'])
def import_data():
    conn = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 既存データを削除
        cursor.execute('DELETE FROM equipment')
        
        # 新しいデータを挿入
        for item in data:
            if DATABASE_URL:
                cursor.execute('''
                    INSERT INTO equipment (
                        item_id, name, location, category, current_location,
                        user_location, status, note, image, history
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            else:
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
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'データがインポートされました'})
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"インポートエラー: {e}")
        return jsonify({'success': False, 'message': f'インポートに失敗しました: {str(e)}'}), 400

# データベース初期化エンドポイント
@app.route('/api/init-db')
def init_database():
    try:
        init_db()
        return jsonify({'status': 'success', 'message': 'データベースが初期化されました'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'初期化失敗: {str(e)}'}), 500
# 管理者ログイン認証
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        username = data.get('username', 'admin')
        password = data.get('password', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute('SELECT password_hash FROM admin_users WHERE username = %s', (username,))
        else:
            cursor.execute('SELECT password_hash FROM admin_users WHERE username = ?', (username,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and check_password_hash(result['password_hash'] if DATABASE_URL else result[0], password):
            return jsonify({'success': True, 'message': 'ログイン成功'})
        else:
            return jsonify({'success': False, 'message': 'ユーザー名またはパスワードが違います'}), 401
            
    except Exception as e:
        print(f"ログインエラー: {e}")
        return jsonify({'success': False, 'message': 'ログインに失敗しました'}), 500
        
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0' if os.environ.get('ENVIRONMENT') == 'production' else '127.0.0.1'
    app.run(debug=app.config['DEBUG'], host=host, port=port)
