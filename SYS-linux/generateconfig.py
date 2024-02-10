import os
import json
import platform

def get_config_path():
    """获取配置文件路径"""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_dir, 'config', 'config.json')

def load_config():
    """从配置文件中加载参数"""
    config_path = get_config_path()
    with open(config_path, 'r', encoding='utf-8') as config_file:
        return json.load(config_file)

def update_config(config):
    """更新配置文件"""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, indent=4)

def extract_paths(static_folder, config):
    """使用 static_folder 从配置中提取路径和库名，并更新配置"""
    directory_path = os.path.join(static_folder, "images")
    library_index = static_folder.rfind(".library")

    if library_index != -1:
        library_name = static_folder[:library_index].split(os.sep)[-1] + ".library"
        base_path = os.path.join(library_name, "images")
    else:
        base_path = "images"
        library_name = ""

    flask_base_path = "/" + base_path.replace(os.sep, "/")  # 直接使用URL路径分隔符

    # 更新配置字典
    config['flask_base_path'] = flask_base_path
    config['directory_path'] = directory_path
    config['library_name'] = library_name

    return config

# 加载配置
config = load_config()
static_folder = config.get('static_folder', '')

# 提炼路径和库名，并更新配置
updated_config = extract_paths(static_folder, config)

# 更新配置文件
update_config(updated_config)

print("Updated configuration:")
print(json.dumps(updated_config, indent=4))
