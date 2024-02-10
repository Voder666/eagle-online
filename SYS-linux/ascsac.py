from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='build')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# 通用捕获，用于前端路由
@app.route('/<path:path>')
def catch_all(path):
    # 如果路径是静态文件（如 CSS 或 JavaScript 文件），则从 static_folder 提供
    if path.startswith("static/") or "." in path:
        return send_from_directory(app.static_folder, path)
    # 否则，返回 index.html 并让前端路由处理路径
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
