import tkinter as tk
import threading
import socket

class FileExchangeClient:
    def __init__(self):
        self.client_socket = None
        self.isRegistered = False  # Track if the user is registered
        self.create_gui()

    def create_gui(self):
        self.root = tk.Tk()
        self.root.geometry("750x750")
        self.root.resizable(width=True, height=True)
        self.root.title("File Exchange System")
        #self.root.iconbitmap(r'Logo.ico')

        # Configure grid rows and columns
        self.root.grid_rowconfigure(0, weight=1)  # Chat display row
        self.root.grid_rowconfigure(1, weight=0)  # Input area row
        self.root.grid_columnconfigure(0, weight=1)  # Main column

        # Chat display with scrollbars
        self.chat_display = tk.Text(self.root, state='disabled', borderwidth=2, relief="sunken")
        self.chat_display.grid(row=0, column=0, sticky='nsew')

        # Vertical Scrollbar
        self.v_scroll = tk.Scrollbar(self.root, orient='vertical', command=self.chat_display.yview)
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.chat_display.configure(yscrollcommand=self.v_scroll.set)

        # Input area
        self.typebox = tk.Entry(self.root, width=60)
        self.typebox.grid(row=1, column=0, sticky='ew', padx=10, pady=10)

        # Submit button
        self.send_button = tk.Button(self.root, text='Submit', command=self.process_command_gui)
        self.send_button.grid(row=1, column=1, sticky='e', padx=10, pady=10)

        self.root.mainloop()
        self.isRegistered = False  # Railey's Edit

    def connect_to_server(self, server_ip, server_port):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self.update_chat_display(f"Connected to {server_ip}:{server_port}")
            threading.Thread(target=self.listen_for_messages, daemon=True).start()
        except Exception as e:
            error_message = f"Connection Error: {e}"
            print(error_message)
            self.update_chat_display(error_message)
            
    def listen_for_messages(self):
        while self.client_socket:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.update_chat_display(message)
                    self.check_registration_status(message)
            except OSError:  # Handle potential socket errors
                break
            
    def check_registration_status(self, message):
        # Check for a message pattern that indicates successful registration
        if "registered as" in message:
            self.isRegistered = True
            
    def handle_registration(self, command):
        self.client_socket.sendall(command.encode())
        # The response will be handled in listen_for_messages now

    def process_command_gui(self):
        command = self.typebox.get()
        self.typebox.delete(0, 'end')

        if command in ['/help', '/?']:
            self.display_help()
        elif command.startswith('/join ') or command.startswith('/leave') or command.startswith('/register') or command.startswith('/shutdown'):
            threading.Thread(target=self.process_command, args=(command,)).start()
        elif self.isRegistered:
            threading.Thread(target=self.process_command, args=(command,)).start()
        else:
            self.update_chat_display("You must register first. Use /register <username>")

    def process_command(self, command):
        try:
            if command in ['/help', '/?']:
                # Display help information
                self.display_help()
            elif command.startswith('/join '):
                _, server_ip, server_port = command.split()
                self.connect_to_server(server_ip, int(server_port))
            elif command.startswith('/register'):
                self.handle_registration(command)
            elif command.startswith('/shutdown'):
                # Handle shutdown command
                self.client_socket.sendall(command.encode())
            elif self.isRegistered:
                if command.startswith('/store ') or command.startswith('/get '):
                    threading.Thread(target=self.handle_file_operations, args=(command,)).start()
                else:
                    self.handle_other_commands(command)
            else:
                self.update_chat_display("You must register first. Use /register <username>")
        except Exception as e:
            self.update_chat_display(f"Error: {e}")
            
    def display_help(self):
        help_text = (
            "/join <ip> <port> - Connect to the server at the specified IP and port.\n"
            "/leave - Disconnect from the server.\n"
            "/register <username> - Register with the server using the specified username.\n"
            "/shutdown - Shut down the server (admin only).\n"
            "/store <filename> - Store a file on the server.\n"
            "/get <filename> - Retrieve a file from the server.\n"
            "/msg <username> <message> - Send a private message to the specified user.\n"
            "/all <message> - Send a broadcast message to all users.\n"
            "/help or /? - Show this help message.\n"
        )
        self.update_chat_display(help_text)


    def handle_registration(self, command):
        self.client_socket.sendall(command.encode())
        response = self.receive_full_response(self.client_socket)
        if "registered as" in response:
            self.isRegistered = True
        self.update_chat_display(response)
        
    def handle_file_operations(self, command):
        try:
            if command.startswith('/store ') and self.isRegistered == True:
                filename = command.split(maxsplit=1)[1]
                self.send_file(filename)
            elif command.startswith('/get ') and self.isRegistered == True:
                filename = command.split(maxsplit=1)[1]
                self.client_socket.sendall(command.encode())
                self.receive_file(filename)
        except Exception as e:
            self.update_chat_display(f"File operation error: {e}")

    def handle_other_commands(self, command):
        try:
            self.client_socket.sendall(command.encode())

            if command.startswith('/register '):
                response = self.receive_full_response(self.client_socket)
                if "registered as" in response:
                    self.isRegistered = True
            elif (command.startswith('/msg ') or command.startswith('/all ')) and self.isRegistered:
                return
            elif command == '/dir' and self.isRegistered:
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
            if len(part) < 4096: # If we received less than 4096 bytes, then we know that we have received the full response
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
