import json
import sqlite3
import os
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.realpath(__file__))

# 构建配置文件路径
config_path = os.path.join(script_dir, 'config', 'config.json')

def load_config():
    """读取配置文件"""
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        raise

def connect_db(db_path):
    """连接到SQLite数据库"""
    try:
        return sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logging.error(f"数据库连接失败: {e}")
        raise

def drop_folders_table(cursor):
    """删除旧的'folders'表"""
    try:
        cursor.execute("DROP TABLE IF EXISTS folders")
        logging.info("旧的'folders'表已删除。")
    except sqlite3.Error as e:
        logging.error(f"删除'folders'表失败: {e}")
        raise

def create_folders_table(cursor):
    """创建新的数据库表"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            folder_id TEXT PRIMARY KEY,
            folder_name TEXT,
            description TEXT,
            parent_folder_id TEXT,
            modificationTime INTEGER,
            tags TEXT,
            password TEXT,
            passwordTips TEXT,
            all_upper_folders TEXT,
            FOREIGN KEY (parent_folder_id) REFERENCES folders(folder_id)
        );
        """)
        logging.info("新的'folders'表已创建。")
    except sqlite3.Error as e:
        logging.error(f"创建'folders'表失败: {e}")
        raise

def get_metadata_json_path(directory_path):
    """定义metadata.json文件路径"""
    # 使用 os.path.dirname 获取上一级目录
    parent_directory = os.path.dirname(directory_path)
    return os.path.join(parent_directory, 'metadata.json')


def load_metadata_data(metadata_json_path):
    """读取metadata.json文件内容"""
    try:
        with open(metadata_json_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except Exception as e:
        logging.error(f"读取metadata.json文件失败: {e}")
        raise

def insert_folder_data(cursor, folder_data, parent_folder_id='0', upper_folders=[]):
    """提取文件夹结构和文件夹名称的函数"""
    folder_id = folder_data.get('id', '')
    folder_name = folder_data.get('name', folder_id)
    description = folder_data.get('description', '')
    modificationTime = folder_data.get('modificationTime', 0)
    tags = json.dumps(folder_data.get('tags', []))  # 将标签列表转换为JSON字符串
    password = folder_data.get('password', '')
    passwordTips = folder_data.get('passwordTips', '')
    all_upper_folders = ','.join(upper_folders)

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO folders (
                folder_id, folder_name, description, parent_folder_id,
                modificationTime, tags, password, passwordTips, all_upper_folders
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (folder_id, folder_name, description, parent_folder_id,
                  modificationTime, tags, password, passwordTips, all_upper_folders))
    except sqlite3.Error as e:
        logging.error(f"插入文件夹数据失败: {e}")
        raise

    new_upper_folders = upper_folders + [folder_id]  # 更新当前路径
    for child_folder_data in folder_data.get('children', []):
        insert_folder_data(cursor, child_folder_data, parent_folder_id=folder_id, upper_folders=new_upper_folders)

if __name__ == "__main__":
    try:
        # 加载配置
        config = load_config()
        directory_path = config["directory_path"]
        db_path = config["db_path"]

        # 连接SQLite数据库
        with connect_db(db_path) as conn:
            cursor = conn.cursor()

            # 删除旧的"folders"表并创建新表
            drop_folders_table(cursor)
            create_folders_table(cursor)

            # 定义并处理metadata.json文件
            metadata_json_path = get_metadata_json_path(directory_path)
            metadata_data = load_metadata_data(metadata_json_path)

            for folder in metadata_data.get("folders", []):
                insert_folder_data(cursor, folder)  # 对每个顶层文件夹项调用 insert_folder_data 函数

            conn.commit()
            logging.info("已成功处理metadata.json文件并更新SQLite数据库。")

    except Exception as e:
        logging.error(f"脚本运行时出现错误: {e}")
