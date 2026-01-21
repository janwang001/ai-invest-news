#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H5 应用本地开发服务器

在本地启动一个简单的 HTTP 服务器来预览 H5 应用。
"""

import http.server
import os
import socketserver

PORT = 8080
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), "..", "webapp")


class Handler(http.server.SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBAPP_DIR, **kwargs)

    def end_headers(self):
        # 添加 CORS 头，方便开发调试
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


def main():
    """启动开发服务器"""
    os.chdir(WEBAPP_DIR)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n{'=' * 50}")
        print("AI投资新闻 H5 应用开发服务器")
        print(f"{'=' * 50}")
        print(f"\n服务已启动，访问地址：http://localhost:{PORT}")
        print(f"应用目录：{WEBAPP_DIR}")
        print("\n按 Ctrl+C 停止服务器\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务器已停止")


if __name__ == "__main__":
    main()
