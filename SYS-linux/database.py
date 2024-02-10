import json
import sqlite3
import os
from tqdm import tqdm
import platform

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.realpath(__file__))
# 构建数据库文件路径
db_path = os.path.join(script_dir, 'metadata.db')
# 构建配置文件路径
config_path = os.path.join(script_dir, 'config', 'config.json')

# 获取当前操作系统的名称
def get_os_name():
    return platform.system()

# 读取配置文件
def load_config():
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

# 更新配置文件
def update_config(config):
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, indent=4)

# 使用 static_folder 从配置中提取路径和库名，并更新配置
def extract_paths(static_folder, config, os_name):
    directory_path = os.path.join(static_folder, "images")

    library_index = static_folder.rfind(".library")
    if library_index != -1:
        library_name = static_folder[:library_index].split(os.sep)[-1] + ".library"
        base_path = os.path.join(library_name, "images")
    else:
        base_path = "images"
        library_name = ""

    # 根据不同的操作系统来调整路径分隔符
    if os_name == "Windows":
        flask_base_path = "/" + base_path.replace(os.sep, "/")
    else:
        flask_base_path = "/" + base_path.replace(os.sep, "/")

    # 更新配置字典
    config['flask_base_path'] = flask_base_path
    config['directory_path'] = directory_path
    config['library_name'] = library_name

    # 返回更新后的配置
    return config

# 删除原先的数据表
def drop_table():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS metadata;")
    conn.commit()
    conn.close()

# 收集所有metadata.json文件的路径
def collect_metadata_files(directory_path):
    metadata_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file == 'metadata.json':
                full_path = os.path.join(root, file)
                metadata_files.append(full_path)
    return metadata_files

# 使用tqdm创建进度条
def process_files(metadata_files):
    # 连接或创建SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建数据库表，如果表已经存在则跳过
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        id TEXT PRIMARY KEY,
        name TEXT,
        size INTEGER,
        btime INTEGER,
        mtime INTEGER,
        ext TEXT,
        tags TEXT,
        folders TEXT,
        isDeleted BOOLEAN,
        url TEXT,
        annotation TEXT,
        modificationTime INTEGER,
        height INTEGER,
        width INTEGER,
        palettes TEXT,
        lastModified INTEGER,
        star INTEGER,
        origurl TEXT,
        thumburl TEXT
    );
    """)
    conn.commit()

    # 准备批量插入的数据
    insert_data = []

    with tqdm(total=len(metadata_files), desc="Processing metadata files") as progress_bar:
        for file_path in metadata_files:
            # 初始化URL字段
            orig_url = None
            thumb_url = None
            
            # 获取当前文件夹内的所有文件
            current_folder = os.path.dirname(file_path)
            image_files = [f for f in os.listdir(current_folder) if os.path.isfile(os.path.join(current_folder, f))]
            
            # 检查图片文件并设置origurl和thumburl
            for image_file in image_files:
                if 'thumbnail' in image_file:
                    thumb_url = f'{flask_url}{flask_base_path}/{os.path.basename(current_folder)}/{image_file}'
                else:
                    # 检查图片文件是否是metadata.json，如果是则跳过
                    if image_file == 'metadata.json':
                        continue
                    orig_url = f'{flask_url}{flask_base_path}/{os.path.basename(current_folder)}/{image_file}'

            # 如果没有找到带有'thumbnail'的图片，则两个URL字段都设置为同一个值
            if not thumb_url:
                thumb_url = orig_url

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 转换tags字段为铭文编码
                tags = json.dumps(metadata['tags'], ensure_ascii=False).encode('utf-8').decode('utf-8')

                # 使用get方法检查star字段是否存在，不存在时设置默认值为0
                star_value = metadata.get('star', 0)
                        
                insert_data.append((
                    metadata['id'], metadata['name'], metadata['size'], metadata['btime'],
                    metadata['mtime'], metadata['ext'], tags,  # 使用转换后的tags
                    json.dumps(metadata['folders']), metadata['isDeleted'], metadata['url'],
                    metadata['annotation'], metadata['modificationTime'], metadata['height'],
                    metadata['width'], json.dumps(metadata['palettes']), metadata['lastModified'], star_value,
                    orig_url,
                    thumb_url
                ))
            except json.JSONDecodeError:
                print(f"JSON解析错误: {file_path}，跳过此文件。")
                continue
            except Exception as e:
                print(f"处理文件时发生错误: {file_path}，错误信息: {e}")
                continue
            finally:
                progress_bar.update(1)

    cursor.executemany("""
    INSERT INTO metadata (id, name, size, btime, mtime, ext, tags, folders, isDeleted, url, 
                        annotation, modificationTime, height, width, palettes, lastModified, 
                        star, origurl, thumburl)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,
        size=excluded.size,
        btime=excluded.btime,
        mtime=excluded.mtime,
        ext=excluded.ext,
        tags=excluded.tags,
        folders=excluded.folders,
        isDeleted=excluded.isDeleted,
        url=excluded.url,
        annotation=excluded.annotation,
        modificationTime=excluded.modificationTime,
        height=excluded.height,
        width=excluded.width,
        palettes=excluded.palettes,
        lastModified=excluded.lastModified,
        star=excluded.star,
        origurl=excluded.origurl,
        thumburl=excluded.thumburl;
    """, insert_data)
    conn.commit()
    conn.close()

# 获取当前操作系统的名称
os_name = get_os_name()

# 加载配置
config = load_config()
flask_url = config["flask_url"]
flask_base_path = config["flask_base_path"]
static_folder = config["static_folder"]

# 提炼路径和库名，并更新配置
updated_config = extract_paths(static_folder, config, os_name)

# 更新配置文件
update_config(updated_config)

# 删除原先的数据表
drop_table()

# 收集所有metadata.json文件的路径
metadata_files = collect_metadata_files(updated_config["directory_path"])

# 开始处理文件
process_files(metadata_files)

print("所有文件处理完成.")
