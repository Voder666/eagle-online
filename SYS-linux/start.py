import subprocess
import threading
import sys
import os

# 记录脚本的进程对象和线程对象
processes = []

def run_script(script_name, port=None):
    script_dir = os.path.dirname(__file__)  # 获取当前脚本所在的文件夹路径
    script_path = os.path.join(script_dir, script_name)  # 拼接脚本路径
    cmd = [sys.executable, script_path]
    if port:
        cmd.extend(['--port', str(port)])
        print(f"{script_name} 应用将在 localhost:{port} 上运行...")  # 增加的输出
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    def read_output(proc):
        while True:
            output = proc.stdout.readline()
            if not output and proc.poll() is not None:
                break
            if output:
                print(f"{script_name}: {output.strip()}")

    # 创建并启动一个线程来读取输出
    thread = threading.Thread(target=read_output, args=(process,))
    thread.start()
    processes.append((process, thread))
    return process, thread

def exit_program():
    print("Exiting...")
    for proc, thread in processes:
        try:
            proc.kill()  # 强制终止进程
        except Exception as e:
            print(f"Error killing process: {e}")

        thread.join()  # 等待线程结束
    sys.exit()

def main():
    # 启动lookupapi.py（不需要特别指定端口）
    proc1, thread1 = run_script('lookupapi.py')

    # 启动ascsac.py，并指定端口5001
    proc2, thread2 = run_script('ascsac.py', 5001)

    # 等待脚本运行完成
    try:
        for proc, _ in processes:
            proc.wait()
    except KeyboardInterrupt:
        exit_program()

if __name__ == '__main__':
    main()
