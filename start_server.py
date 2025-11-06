#!/usr/bin/env python3
"""
StockEasy - ローカルHTTPサーバー起動スクリプト
同じネットワーク内の他のPCからアクセス可能
"""

import http.server
import socketserver
import os
import socket

# 設定
PORT = 8080
DIRECTORY = "frontend"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # CORSヘッダーを追加（必要に応じて）
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        # ダミー接続を作成してローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    # ディレクトリが存在するか確認
    if not os.path.exists(DIRECTORY):
        print(f"❌ エラー: {DIRECTORY} ディレクトリが見つかりません")
        exit(1)

    # サーバー起動
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        local_ip = get_local_ip()

        print("=" * 60)
        print("🚀 StockEasy サーバー起動")
        print("=" * 60)
        print(f"📁 ディレクトリ: {DIRECTORY}")
        print(f"🌐 ポート: {PORT}")
        print()
        print("📱 アクセス方法:")
        print(f"  - このPC: http://localhost:{PORT}")
        print(f"  - 同じネットワーク内の他のPC: http://{local_ip}:{PORT}")
        print()
        print("⚠️  注意:")
        print("  1. Supabaseの環境変数を設定してください")
        print("     (frontend/index.html の20行目あたり)")
        print("  2. ファイアウォールでポート8080を開放してください")
        print()
        print("🛑 停止: Ctrl+C")
        print("=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 サーバーを停止しました")
