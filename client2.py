import tkinter as tk
import threading
import socket

class FileExchangeClient:
    def __init__(self):
        self.client_socket = None
        self.create_gui()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.geometry("500x500")
        self.root.resizable(width=False, height=False)
        self.root.title("File Exchange System")

        # Chat display area
        self.chat_display = tk.Text(self.root, state='disabled', height=20, width=60)
        self.chat_display.pack()

        # Input area
        self.typebox = tk.Entry(self.root, width=40)
        self.typebox.pack(side=tk.LEFT)

        # Submit button
        self.send_button = tk.Button(self.root, text='Submit', command=self.process_command_gui)
        self.send_button.pack(side=tk.RIGHT)

        self.root.mainloop()

    def connect_to_server(self, server_ip, server_port):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            # Update GUI with connection status
            self.update_chat_display(f"Connected to {server_ip}:{server_port}")
        except Exception as e:
            error_message = f"Connection Error: {e}"
            print(error_message)
            # Update GUI with error message
            self.update_chat_display(error_message)

    def process_command_gui(self):
        command = self.typebox.get()
        self.typebox.delete(0, 'end')
        if command.startswith('/join '):
            _, server_ip, server_port = command.split()
            self.connect_to_server(server_ip, int(server_port))
        elif command.startswith('/store ') or command.startswith('/get '):
            threading.Thread(target=self.process_command, args=(command,)).start()
        else:
            self.process_command(command)

    def process_command(self, command):
        try:
            if command.startswith('/store '):
                filename = command.split()[1]
                self.send_file(filename)
            elif command.startswith('/get '):
                filename = command.split()[1]
                self.client_socket.sendall(command.encode())
                self.receive_file(filename)
            elif command in ['/dir', '/register']:
                self.client_socket.sendall(command.encode())
                response = self.client_socket.recv(4096)
                self.update_chat_display(response.decode())
            elif command == '/leave':
                self.close_connection()
            else:
                self.client_socket.sendall(command.encode())
                response = self.client_socket.recv(1024)
                self.update_chat_display(response.decode())
        except Exception as e:
            self.update_chat_display(f"Error: {e}")

    def send_file(self, filename):
        try:
            with open(filename, 'rb') as file:
                self.client_socket.sendall(f"/store {filename}\n".encode())
                while True:
                    data = file.read(1024)
                    if not data:
                        self.client_socket.sendall(b'EOF')
                        break
                    self.client_socket.sendall(data)
                response = self.client_socket.recv(1024)
                self.update_chat_display(response.decode())
        except FileNotFoundError:
            self.update_chat_display("File not found")

    def receive_file(self, filename):
        with open(filename, 'wb') as file:
            while True:
                data = self.client_socket.recv(1024)
                if b'EOF' in data:
                    if data[:-3]:
                        file.write(data[:-3])
                    break
                file.write(data)
        self.update_chat_display(f"File {filename} received")

    def close_connection(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self.update_chat_display("Disconnected from the server")

    def update_chat_display(self, message):
        def _update():
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, message + "\n")
            self.chat_display.config(state='disabled')
            self.chat_display.see(tk.END)

        self.root.after(0, _update)


# Run the client application
if __name__ == "__main__":
    client_app = FileExchangeClient()
