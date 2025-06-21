from flask import Flask, request, jsonify, send_from_directory, redirect, session
from flask_cors import CORS
from flask_session import Session
import json
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)

# セッション設定を追加
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
Session(app)

CORS(app, supports_credentials=True)

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
            # 施設テーブルを追加
        if DATABASE_URL:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facilities (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    address VARCHAR(500) DEFAULT '',
                    phone VARCHAR(50) DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    facility_id INTEGER REFERENCES facilities(id) ON DELETE CASCADE,
                    username VARCHAR(50) NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(20) DEFAULT 'staff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(facility_id, username)
                )
            ''')
        else:
            # SQLite用（ローカル開発）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    facility_id INTEGER,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'staff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (facility_id) REFERENCES facilities (id),
                    UNIQUE(facility_id, username)
                )
            ''')
            # 既存のequipmentテーブルにfacility_idカラムを追加
        try:
            if DATABASE_URL:
                cursor.execute('''
                    ALTER TABLE equipment 
                    ADD COLUMN facility_id INTEGER REFERENCES facilities(id) ON DELETE CASCADE
                ''')
            else:
                cursor.execute('''
                    ALTER TABLE equipment 
                    ADD COLUMN facility_id INTEGER
                ''')
        except Exception as e:
            # カラムが既に存在する場合はエラーを無視
            print(f"facility_idカラム追加スキップ: {e}")
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

@app.route('/api/equipment', methods=['POST'])
def create_equipment():
    # 管理者権限チェック
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    conn = None
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'データが送信されていません'}), 400
        
        # 入力値検証を追加
        validation_errors = validate_equipment_data(data)
        if validation_errors:
            return jsonify({
                'success': False, 
                'message': '入力エラー: ' + ', '.join(validation_errors)
            }), 400
        
        # データをサニタイズ
        sanitized_data = {
            'id': sanitize_string(data.get('id', '')),
            'name': sanitize_string(data.get('name', '')),
            'location': data.get('location', ''),  # 選択肢なのでサニタイズ不要
            'category': data.get('category', ''),  # 選択肢なのでサニタイズ不要
            'image': data.get('image', ''),
            'history': data.get('history', [])
        }
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO equipment (
                    item_id, name, location, category, image, history
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                sanitized_data['id'],
                sanitized_data['name'],
                sanitized_data['location'],
                sanitized_data['category'],
                sanitized_data['image'],
                json.dumps(sanitized_data['history'])
            ))
        else:
            cursor.execute('''
                INSERT INTO equipment (
                    item_id, name, location, category, image, history
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sanitized_data['id'],
                sanitized_data['name'],
                sanitized_data['location'],
                sanitized_data['category'],
                sanitized_data['image'],
                json.dumps(sanitized_data['history'])
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
    #管理者権限チェック(編集・削除のみ)
    data=request.json

    # 借用・返却処理（職員も可能）は権限チェックなし
    if set(data.keys()).issubset({'user', 'current', 'status', 'history', 'note'}):
        pass
    else:
        auth_check = require_admin()
        if auth_check:
            return auth_check
    
    conn = None
    try:
        # 更新データの検証（一部のフィールドのみ）
        errors = []
        # 名前が送信されている場合のみチェック
        if 'name' in data:
            name = data.get('name', '')
            if not name or not name.strip():
                errors.append('備品名は必須です')
            elif len(name) > 200:
                errors.append('備品名は200文字以内で入力してください')
            elif '<' in name or '>' in name or '"' in name or "'" in name:
                errors.append('備品名に使用できない文字が含まれています')
        
        # カテゴリが送信されている場合のみチェック
        if 'category' in data:
            allowed_categories = ['車いす', '歩行器・シルバーカー', '家具', 'エアマット', 'その他']
            if data.get('category') not in allowed_categories:
                errors.append('無効なカテゴリです')
        
        # 場所が送信されている場合のみチェック
        if 'location' in data:
            allowed_locations = ['事務所', '1F', '2F', '3F', '4F', '5F', '地域交流室', '機能訓練室']
            if data.get('location') not in allowed_locations:
                errors.append('無効な保管場所です')
        
        if errors:
            return jsonify({
                'success': False, 
                'message': '入力エラー: ' + ', '.join(errors)
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # 安全なフィールドマッピングを追加
        safe_fields = {
            'name': 'name',
            'location': 'location',
            'category': 'category',
            'current': 'current_location',
            'user': 'user_location',
            'status': 'status',
            'note': 'note',
            'image': 'image',
            'history': 'history'
}
        # 新しい安全なフィールド処理
        update_fields = []
        values = []

        if DATABASE_URL:
            param_placeholder = '%s'
        else:
            param_placeholder = '?'

        # 安全なフィールドのみ処理
        for field_key, db_column in safe_fields.items():
            if field_key in data:
                if field_key == 'history':
                    update_fields.append(f'{db_column} = {param_placeholder}')
                    values.append(json.dumps(data[field_key]))
                else:
                    update_fields.append(f'{db_column} = {param_placeholder}')
                    values.append(data[field_key])

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

@app.route('/api/equipment/<item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    # 管理者権限チェック
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    conn = None
    try:
        # 以下は既存コードのまま
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
            # セッションに管理者情報を保存
            session['user_type'] = 'admin'
            session['username'] = username
            session['logged_in'] = True
            return jsonify({'success': True, 'message': 'ログイン成功'})
        else:
            return jsonify({'success': False, 'message': 'ユーザー名またはパスワードが違います'}), 401
            
    except Exception as e:
        print(f"ログインエラー: {e}")
        return jsonify({'success': False, 'message': 'ログインに失敗しました'}), 500

# 職員ログイン処理
@app.route('/api/staff/login', methods=['POST'])
def staff_login():
    try:
        print("=== 職員ログイン処理開始 ===", flush=True)
        
        # セッションに保存
        session['user_type'] = 'staff'
        session['username'] = 'staff'
        session['logged_in'] = True

        print(f"=== セッション保存後: {dict(session)} ===", flush=True)

        return jsonify({'success': True, 'message': 'ログイン成功'})
    except Exception as e:
        print(f"=== 職員ログインエラー: {e} ===", flush=True)
        return jsonify({'success': False, 'message': 'ログインに失敗しました'}), 500

# セッション状態確認
@app.route('/api/session/check', methods=['GET'])
def check_session():
    try:
        print(f"=== セッション確認: {dict(session)} ===", flush=True)
        
        if session.get('logged_in') and session.get('user_type') == 'admin':
            return jsonify({
                'success': True, 
                'logged_in': True,
                'user_type': session.get('user_type'),
                'username': session.get('username')
            })
        elif session.get('logged_in') and session.get('user_type') == 'staff':
            return jsonify({
                'success': True,
                'logged_in': True,
                'user_type': session.get('user_type'),
                'username': session.get('username')
            })
        else:
            return jsonify({
                'success': True,
                'logged_in': False,
                'user_type': None
            })
    except Exception as e:
        print(f"=== セッション確認エラー: {e} ===", flush=True)
        return jsonify({'success': False, 'message': 'セッション確認に失敗しました'}), 500

# 管理者権限チェック用デコレータ
def require_admin():
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': '管理者権限が必要です'}), 403
    return None

# 入力値検証関数
def validate_equipment_data(data):
    errors = []
    
    # 備品名チェック
    name = data.get('name', '')
    if not name or not name.strip():
        errors.append('備品名は必須です')
    elif len(name) > 200:
        errors.append('備品名は200文字以内で入力してください')
    elif '<' in name or '>' in name or '"' in name or "'" in name:
        errors.append('備品名に使用できない文字が含まれています')
    
    # IDチェック
    item_id = data.get('id', '')
    if not item_id or not item_id.strip():
        errors.append('IDは必須です')
    elif len(item_id) > 50:
        errors.append('IDは50文字以内で入力してください')
    elif not item_id.replace('-', '').replace('_', '').isalnum():
        errors.append('IDは英数字、ハイフン、アンダースコアのみ使用可能です')
    
    # カテゴリチェック
    allowed_categories = ['車いす', '歩行器・シルバーカー', '家具', 'エアマット', 'その他']
    category = data.get('category', '')
    if not category:
        errors.append('カテゴリは必須です')
    elif category not in allowed_categories:
        errors.append('無効なカテゴリです')
    
    # 場所チェック
    allowed_locations = ['事務所', '1F', '2F', '3F', '4F', '5F', '地域交流室', '機能訓練室']
    location = data.get('location', '')
    if not location:
        errors.append('保管場所は必須です')
    elif location not in allowed_locations:
        errors.append('無効な保管場所です')
    
    return errors

# 文字列サニタイズ関数
def sanitize_string(text):
    if not text:
        return ''
    # 危険な文字を無害化
    return str(text).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')

# ログアウト機能
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'ログアウトしました'})
    except Exception as e:
        print(f"ログアウトエラー: {e}")
        return jsonify({'success': False, 'message': 'ログアウトに失敗しました'}), 500
# データベース初期化を強制実行（テスト用）
@app.route('/api/init-admin-table', methods=['GET'])
def init_admin_table():
    try:
        print("管理者テーブル初期化開始")
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'データベース接続失敗'}), 500
            
        cursor = conn.cursor()
        
        # 管理者テーブル作成
        if DATABASE_URL:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("PostgreSQL用テーブル作成")
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("SQLite用テーブル作成")
        
        # デフォルト管理者作成
        hashed_password = generate_password_hash('admin123')
        print(f"ハッシュ化パスワード: {hashed_password[:20]}...")
        
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
        print("管理者テーブル初期化完了")
        return jsonify({'success': True, 'message': '管理者テーブルを作成しました'})
        
    except Exception as e:
        print(f"テーブル作成エラー: {e}")
        return jsonify({'success': False, 'message': f'エラー: {str(e)}'}), 500
        
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0' if os.environ.get('ENVIRONMENT') == 'production' else '127.0.0.1'
    app.run(debug=app.config['DEBUG'], host=host, port=port)
