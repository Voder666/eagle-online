import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading

def start_script():
    threading.Thread(target=start_script_thread).start()

def start_script_thread():
    try:
        process = subprocess.Popen(["python", "manage_sys.py", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, errors = process.communicate()
        console_text.insert(tk.END, output.decode("utf-8"))
        console_text.insert(tk.END, errors.decode("utf-8"))
        console_text.see(tk.END)
    except Exception as e:
        console_text.insert(tk.END, f"Error occurred: {str(e)}")
        console_text.see(tk.END)

def stop_script():
    threading.Thread(target=stop_script_thread).start()

def stop_script_thread():
    try:
        process = subprocess.Popen(["python", "manage_sys.py", "stop"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, errors = process.communicate()
        console_text.insert(tk.END, output.decode("utf-8"))
        console_text.insert(tk.END, errors.decode("utf-8"))
        console_text.see(tk.END)
    except Exception as e:
        console_text.insert(tk.END, f"Error occurred: {str(e)}")
        console_text.see(tk.END)

def minimize_to_taskbar(window):
    window.iconify()

def create_window():
    window = tk.Tk()
    window.title("Eagle Online")
    window.configure(bg="#001529")
    window.geometry("600x400")

    # 设置窗口图标
    window.iconbitmap("icon.ico")

    style = ttk.Style()
    style.configure("Custom.TButton", padding=10, relief="flat", background="#1890ff", foreground="black")  # 设置按钮文字颜色为黑色
    style.map("Custom.TButton", background=[("active", "#40a9ff")])

    frame_buttons = tk.Frame(window, bg="#001529")
    frame_buttons.pack(side="left", fill="y")

    start_button = ttk.Button(frame_buttons, text="Start Script", style="Custom.TButton", command=start_script)
    start_button.pack(pady=10, padx=20, anchor="w")

    stop_button = ttk.Button(frame_buttons, text="Stop Script", style="Custom.TButton", command=stop_script)
    stop_button.pack(pady=10, padx=20, anchor="w")

    minimize_button = ttk.Button(frame_buttons, text="Minimize", style="Custom.TButton", command=lambda: minimize_to_taskbar(window))
    minimize_button.pack(pady=10, padx=20, anchor="w")

    frame_console = tk.Frame(window, bg="#001529")
    frame_console.pack(side="right", fill="both", expand=True)

    global console_text
    console_text = tk.Text(frame_console, bg="#001529", fg="white")  # 设置字体颜色为黑色
    console_text.pack(fill="both", expand=True)

    window.mainloop()

if __name__ == "__main__":
    create_window()
