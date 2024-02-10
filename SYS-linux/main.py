import subprocess
import os
import sys  # 引入 sys 模块

def run_script(script_name):
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.realpath(__file__))
        # 构建脚本文件的绝对路径
        script_path = os.path.join(script_dir, script_name)

        # 使用当前 Python 解释器执行指定的 Python 脚本
        result = subprocess.run([sys.executable, script_path], check=True, text=True, capture_output=True)
        # 打印标准输出
        print(f"Output of {script_name}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        # 如果脚本执行失败，打印错误信息
        print(f"Error running {script_name}:\n{e.stderr}")

def main():
    scripts = ['generateconfig.py', 'foldersupate.py', 'database.py']
    
    for script in scripts:
        print(f"Running {script}...")
        run_script(script)

if __name__ == '__main__':
    main()
