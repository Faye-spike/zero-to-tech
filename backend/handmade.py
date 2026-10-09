from http.server import BaseHTTPRequestHandler, HTTPServer
import json

profile = {
    "heroTitle": "关于我",
    "herosubTitle": "项目，创意，灵感，心得，我的作品",
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/profile":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            body = json.dumps(profile, ensure_ascii=False) #ensure_ascii=False 解决中文乱码问题
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

print("后端服务已启动：http://localhost:8000/profile")
HTTPServer(("", 8000), Handler).serve_forever()