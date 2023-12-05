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
        self.root.iconbitmap(r'Logo.ico')

        # Chat display area

        self.chat_display = tk.Text(self.root, state='disabled', height=28, width=60)
        self.chat_display.bind('<MouseWheel>', lambda event: self.chat_display.yview_scroll(int(event.delta/-60),"units"))
        

        #scrollBar 
        self.scroll = tk.Scrollbar(orient='vertical', command=self.chat_display.yview)
        self.scroll.place(relx = 1, rely= 0, relheight= 1, anchor= 'ne')
        self.chat_display.configure(yscrollcommand=self.scroll)
        self.chat_display.pack()

        # Input area
        self.box1 = tk.Canvas(width=477, height=55)
        self.box1.configure(bg='light gray')
        self.box1.pack()
        self.box1.place(x=3, y=442)

        self.typebox = tk.Entry(self.root, width=66)
        self.box1.create_window(215, 25, window=self.typebox)
        

        # Submit button
        self.send_button = tk.Button(self.root, text='Submit', command=self.process_command_gui)
        self.box1.create_window(445, 25, window= self.send_button)

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
            if command.startswith('/store ') or command.startswith('/get '):
                threading.Thread(target=self.handle_file_operations, args=(command,)).start()
            else:
                self.handle_other_commands(command)
        except Exception as e:
            self.update_chat_display(f"Error: {e}")


    def handle_file_operations(self, command):
        try:
            if command.startswith('/store '):
                filename = command.split(maxsplit=1)[1]
                self.send_file(filename)
            elif command.startswith('/get '):
                filename = command.split(maxsplit=1)[1]
                self.client_socket.sendall(command.encode())
                self.receive_file(filename)
        except Exception as e:
            self.update_chat_display(f"File operation error: {e}")

    def handle_other_commands(self, command):
        try:
            self.client_socket.sendall(command.encode())
            if command in ['/dir', '/register', '/msg']:
                response = self.receive_full_response(self.client_socket)
            elif command == '/leave':
                self.close_connection()
                return
            else:
                response = self.client_socket.recv(1024).decode()
            self.update_chat_display(response)
        except Exception as e:
            self.update_chat_display(f"Error: {e}")

    def receive_full_response(self, client_socket):
        response = ""
        while True:
            part = client_socket.recv(4096).decode()
            response += part
            if len(part) < 4096:  # No more data left or buffer wasn't filled completely
                break
        return response

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

                try:
                    response = self.client_socket.recv(1024)
                    self.update_chat_display(response.decode())
                except socket.error as e:
                    self.update_chat_display(f"Connection error: {e}")
                    self.close_connection()
        except FileNotFoundError:
            self.update_chat_display("File not found")

    def receive_file(self, filename):
        try:
            with open(filename, 'wb') as file:
                while True:
                    data = self.client_socket.recv(1024)
                    if b'EOF' in data:
                        if data[:-3]:
                            file.write(data[:-3])
                        break
                    file.write(data)
            self.update_chat_display(f"File {filename} received")
        except socket.error as e:
            self.update_chat_display(f"Connection error: {e}")
            self.close_connection()


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
