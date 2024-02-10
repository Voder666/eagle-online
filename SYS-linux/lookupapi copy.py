import os
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import subprocess

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.realpath(__file__))
# 构建配置文件路径
config_path = os.path.join(script_dir, 'config', 'config.json')

# 初始化全局配置变量
config = {}

# 从配置文件中加载参数到全局变量
def load_config():
    global config
    print("正在重新加载配置文件...")
    with open(config_path, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    print("配置已更新为:", config)

db_path = os.path.join(script_dir, 'metadata.db')

# 初始加载配置
load_config()

app = Flask(__name__)
CORS(app)

# 设置全局变量用于限制加载频率
last_load_time = 0

def get_db_connection():
    conn = sqlite3.connect(db_path)  # 使用全局配置变量
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route(f'{config["flask_base_path"]}/<path:filename>')  # 注意这里的动态路由可能需要调整
def external_files(filename):
    return send_from_directory(config["directory_path"], filename)  # 使用全局配置变量

@app.route('/config/flask-url', methods=['GET'])
def get_flask_url():
    return jsonify({"flask_url": config["flask_url"]})  # 使用全局配置变量

@app.route('/metadata', methods=['GET'])
def get_metadata():
    query_parameters = request.args
    conditions = []
    args = []

    foldersIds = query_parameters.get('foldersIds')
    if foldersIds:
        foldersIds_list = foldersIds.split(',')
        folder_conditions = [f"folders LIKE ?" for _ in foldersIds_list]
        conditions.append(f"({' OR '.join(folder_conditions)})")
        args.extend([f"%{folder_id}%" for folder_id in foldersIds_list])

    stars = query_parameters.get('stars')
    if stars:
        stars_list = stars.split(',')
        placeholders = ','.join('?' for _ in stars_list)
        conditions.append(f"star IN ({placeholders})")
        args.extend(stars_list)

    tags = query_parameters.get('tags')
    if tags:
        tags_list = tags.split(',')
        tag_conditions = [f"tags LIKE ?" for _ in tags_list]
        conditions.append(f"({' OR '.join(tag_conditions)})")
        args.extend([f"%{tag}%" for tag in tags_list])

    per_page = 10  # 设置每页的结果数量
    page = int(query_parameters.get('page', '1'))
    offset = (page - 1) * per_page

    query = 'SELECT DISTINCT * FROM metadata'  # 使用 DISTINCT 确保唯一性
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY id'  # 确保有一致的排序依据
    query += ' LIMIT ? OFFSET ?'
    args.extend([per_page, offset])

    results = query_db(query, args)
    return jsonify([dict(row) for row in results])


@app.route('/getTags', methods=['GET'])
def getTags():
    arr = []
    query = 'select tags from metadata'
    results = query_db(query)
    for res in results:
        # print('res:',res)
        for e in res:
            # print('e:',e)
            e = json.loads(e)
            for a in e:
                # print('a:',a)
                arr.append(a)
    
    # print(arr)
    arr = list(set(arr))

    # return jsonify([dict(row) for row in arr])
    return jsonify(arr)

@app.route('/getExt', methods=['GET'])
def getExt():
    sql = 'select ext from metadata'
    results = query_db(sql)

    return jsonify([dict(row) for row in results])


@app.route('/getImageByIds', methods=['GET'])
def getImageByIds():
      # 获取URL参数
        query_parameters = request.args
        ids = query_parameters.get('ids')

        # 将字符串解析为列表
        id_list = ids.split(',')
        sql = 'SELECT * FROM metadata WHERE'
        sql += " and id in (%s)" % ','.join(["'%s'" % id for id in id_list])
        results = query_db(sql)

        # 返回一个空的响应
        return jsonify([dict(row) for row in results])

@app.route('/random_images', methods=['GET'])
def get_random_images():
    per_page = 10  # Change this to 10 images per request
    page = request.args.get('page', 1, type=int)  # Get the page number from the request, default to 1 if not provided

    offset = (page - 1) * per_page  # Calculate the offset for the SQL query

    query = 'SELECT * FROM metadata ORDER BY RANDOM() LIMIT ? OFFSET ?'
    results = query_db(query, [per_page, offset])

    return jsonify([dict(row) for row in results])



@app.route('/getByStar',methods=['GET'])
def getByStar():
    sql = "SELECT star FROM metadata"
    results = query_db(sql)

    return jsonify([dict(row) for row in results])


@app.route('/getColor')
def getColor():
    query_parameters = request.args
    color = query_parameters.get('color')
    # print('发送的color:',color)
    color = '[' + ', '.join(color[1:-1].split(',')) + ']'
    
    # print('修改后的color',color)
    sql = "select * from metadata"
    results = query_db(sql)

    palettes_list = []

    for res in results:
        json_str = res['palettes']  # 使用索引方式获取字段值
        json_str = json.loads(json_str)
        for js in json_str:
            print(json.dumps(js.get('color')))
            if(json.dumps(js.get('color')) == color):
                print('有一样的')
                palettes_list.append(res)
    # 返回 palettes_list 列表作为 JSON 响应
    return jsonify([dict(row) for row in palettes_list])

@app.route('/byTags')
def byTags():
    query_parameters = request.args
    tags = query_parameters.get('tags')
    tags = tags.split(',')
    print('传递进来的参数：',tags)

    aa = []
    for tag in tags:
        tag = tag.encode('unicode_escape').decode('utf-8')
        sql = "SELECT * FROM metadata WHERE tags LIKE '%"+tag+"%'"
        res = query_db(sql)
        print('执行的qsl：',sql)
        aa.extend([dict(row) for row in res])
 
    return jsonify(aa)

@app.route('/byFoldersIds')
def byFoldersIds():
    query_parameters = request.args
    tags = query_parameters.get('foldersIds')
    tags = tags.split(',')
    print('传递进来的参数：',tags)

    aa = []
    for tag in tags:
        # tag = tag.encode('unicode_escape').decode('utf-8')
        sql = "SELECT * FROM metadata WHERE folders LIKE '%"+tag+"%'"
        res = query_db(sql)
        print('执行的qsl：',sql)
        aa.extend([dict(row) for row in res])
 
    return jsonify(aa)

@app.route('/getFoldersName')
def getFoldersName():
    # 查询数据库获取所有文件夹的ID和名称
    query = 'SELECT folder_id, folder_name FROM folders'
    results = query_db(query)

    # 将查询结果转换为字典列表
    id_name_list = [{"id": row["folder_id"], "name": row["folder_name"]} for row in results]

    return jsonify(id_name_list)


@app.route('/run-main', methods=['GET'])
def run_main_py():
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.realpath(__file__))
        # 构建脚本文件的绝对路径
        script_path = os.path.join(script_dir, 'main.py')

        result = subprocess.run(['python', script_path], text=True, capture_output=True, check=True)
        print("main.py 脚本执行完成，正在更新配置...")
        load_config()
        return jsonify({"output": result.stdout, "error": result.stderr})
    except subprocess.CalledProcessError as e:
        load_config()  # 即使出现错误也重新加载配置
        return jsonify({"error": e.stderr}), 500




@app.route('/update-flask-url', methods=['POST'])
def update_flask_url():
    try:
        new_flask_url = request.json.get('flask_url')
        if not new_flask_url:
            return jsonify({"error": "No flask_url provided"}), 400

        # 更新全局配置变量
        config['flask_url'] = new_flask_url

        # 将更新后的全局配置变量写回文件
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(config, config_file, indent=4)

        return jsonify({"message": "flask_url updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/database_summary', methods=['GET'])
def database_summary():
    # 连接数据库
    conn = get_db_connection()
    cur = conn.cursor()

    # 查询图片数量
    cur.execute('SELECT COUNT(*) FROM metadata')
    images_count = cur.fetchone()[0]

    # 查询文件夹数量
    # 假设您有一个名为 'folders' 的表格来存储文件夹信息
    cur.execute('SELECT COUNT(DISTINCT folder_id) FROM folders')
    folders_count = cur.fetchone()[0]

    # 查询表情数量
    # 假设表情存储在 'metadata' 表的某个字段中，您需要根据实际情况调整查询
    cur.execute('SELECT COUNT(DISTINCT tags) FROM metadata')
    tags_count = cur.fetchone()[0]

    # 关闭数据库连接
    conn.close()

    # 返回统计结果
    return jsonify({
        'images_count': images_count,
        'folders_count': folders_count,
        'tags_count': tags_count
    })

@app.route('/update-library-path', methods=['POST'])
def update_library_path():
    try:
        new_library_path = request.json.get('library_path')
        if not new_library_path:
            return jsonify({"error": "No library_path provided"}), 400

        # 直接更新全局配置变量中的 static_folder 字段
        config['static_folder'] = new_library_path

        # 将更新后的全局配置变量写回文件
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(config, config_file, indent=4)

        return jsonify({"message": "Library path updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/current-library-info', methods=['GET'])
def get_current_library_info():
    # 从全局配置变量中读取库信息
    library_path = config.get('static_folder', 'Not configured')
    library_name = config.get('library_name', 'Not configured')

    # 返回库名称和路径
    return jsonify({
        "library_name": library_name,
        "library_path": library_path
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)
