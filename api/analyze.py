from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# 외부 라이브러리(FastAPI, Mangum 등)를 전혀 쓰지 않는 순수 파이썬 핸들러입니다.
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send_response()

    def do_POST(self):
        self._send_response()

    def _send_response(self):
        # 현재 설치된 패키지 목록을 훔쳐봅니다.
        try:
            # pkg_resources는 setuptools의 일부로, 설치된 패키지 확인용입니다.
            import pkg_resources
            installed_packages = [d.project_name for d in pkg_resources.working_set]
        except ImportError:
            installed_packages = ["확인 불가 (pkg_resources 없음)"]

        # 현재 경로와 파일 목록 확인
        current_dir = os.getcwd()
        files = os.listdir(current_dir)

        response_data = {
            "status": "alive",
            "message": "파이썬은 살아있습니다! (Python is running)",
            "debug_info": {
                "python_version": sys.version,
                "current_directory": current_dir,
                "files_in_current_dir": files,
                "installed_packages": installed_packages,  # 🚨 여기에 fastapi, mangum이 없으면 설치가 안 된 겁니다!
                "sys_path": sys.path
            }
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))