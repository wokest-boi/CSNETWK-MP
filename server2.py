import socket
import os
import threading
import logging

class FileExchangeServer:
    def __init__(self, port, max_connections=5, file_storage_path='file_storage'):
        self.port = port
        self.max_connections = max_connections
        self.file_storage_path = file_storage_path
        self.clients = {}  # Store client information
        self.setup_logging()
        self.prepare_file_storage()
        self.sockets = set()#Railey's edit


    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def prepare_file_storage(self):
        if not os.path.exists(self.file_storage_path):
            os.makedirs(self.file_storage_path)

    def start(self):
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.port))
        server_socket.listen(self.max_connections)
        logging.info("Server is running and waiting for connections...")

        while self.running:
            connection, client_address = server_socket.accept()
            self.sockets.add(connection)#Railey's edit ,adds clients to set
            logging.info(f"Connected to {client_address}")
            client_thread = threading.Thread(target=self.handle_client_connection, args=(connection, client_address))
            client_thread.start()
            
        server_socket.close()
        logging.info("Server has been shut down.")

    def handle_client_connection(self, client_socket, client_address):
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                if data.startswith('/store '):
                    filename = data.split()[1]
                    self.store_file(client_socket, client_address, filename)
                elif data == '/dir':
                    self.list_files(client_socket, client_address)
                elif data.startswith('/get '):
                    filename = data.split()[1]
                    self.send_file(client_socket, client_address, filename)
                elif data.startswith('/register '):
                    handle = data.split()[1]
                    self.register_client(client_socket, client_address, handle)
                elif data.startswith('/msg '):
                    # Unicast messaging to a specific user
                    _, recipient, message = data.split(' ', 2)
                    self.unicast_message(client_socket, client_address, recipient, message)
                elif data.startswith('/all '):
                    # Broadcast messaging to all users
                    _, message = data.split(' ', 1)
                    self.broadcast_message(client_socket, client_address, message)
                elif data == '/shutdown':
                    self.shutdown_server()
                else:
                    client_socket.sendall("Unknown command".encode())
            except Exception as e:
                logging.error(f"Error handling client {client_address}: {e}")
                break
            
    def shutdown_server(self):
        self.running = False
        # Notify connected clients about the shutdown
        for socket in self.sockets:
            try:
                socket.sendall("Server is shutting down.".encode())
                socket.close()
            except Exception as e:
                logging.error(f"Error closing client socket: {e}")

        logging.info("Server shutdown process initiated.")

    def unicast_message(self, client_socket, client_address, recipient, message):
        if client_address in self.clients:
            sender_handle = self.clients[client_address]
            response = f"<Msg> {sender_handle}: {message}"
            recipient_socket = self.find_socket_by_username(recipient)

            if recipient_socket:
                try:
                    # Send to recipient
                    recipient_socket.sendall(response.encode())
                    # Also send back to sender for confirmation
                    client_socket.sendall(response.encode())
                except Exception as e:
                    logging.error(f"Error sending unicast message: {e}")

    def broadcast_message(self, client_socket, client_address, message):
        # Implement logic to broadcast message to all connected users
        if client_address in self.clients:
            sender_handle = self.clients[client_address]
            response = f"<All> {sender_handle}: {message}"
            for socket in self.sockets:
                try:
                    socket.sendall(response.encode())
                except Exception as e:
                    logging.error(f"Error sending broadcast message: {e}")

    def find_socket_by_username(self, username):
        # Helper method to find socket by username
        for address, handle in self.clients.items():
            if handle == username:
                for socket in self.sockets:
                    if socket.getpeername() == address:
                        return socket
        return None

    def store_file(self, client_socket, client_address, filename):
        if client_address in self.clients:
            try:
                with open(os.path.join(self.file_storage_path, filename), 'wb') as f:
                    while True:
                        data = client_socket.recv(1024)
                        if b'EOF' in data:
                            f.write(data.replace(b'EOF', b''))
                            break
                        f.write(data)
                client_socket.sendall('File stored successfully'.encode())
            except Exception as e:
                error_message = f"Error storing file: {e}"
                logging.error(error_message)
                client_socket.sendall(error_message.encode())
        else:
            response = "You have not yet registered. Please do /register [name]"
            logging.error(response)
            client_socket.sendall(response.encode())
            client_socket.close()
            return  # Exit the method to prevent further operations on the closed socket



    def list_files(self, client_socket, client_address):
        if client_address in self.clients:
            try:
                files = os.listdir(self.file_storage_path)
                files_list = '\n'.join(files)
                client_socket.sendall(files_list.encode())
            except Exception as e:
                error_message = f"Error listing files: {e}"
                logging.error(error_message)
                client_socket.sendall(error_message.encode())
        else:
            response = "You have not yet registered. Please do /register [name]"
            logging.error(response)
            client_socket.sendall(response.encode())


    def send_file(self, client_socket, client_address, filename):
        if client_address in self.clients:
            filepath = os.path.join(self.file_storage_path, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    while True:
                        data = f.read(1024)
                        if not data:
                            client_socket.sendall(b'EOF')
                            break
                        client_socket.sendall(data)
            else:
                client_socket.sendall('File not found'.encode())
        else:
            response = "You have not yet registered. Please do /register [name]"
            logging.error(response)
            client_socket.sendall(response.encode())
            client_socket.close()


    def register_client(self, client_socket, client_address, handle):
        response = ""
        if handle in self.clients.values():
            suggested_handle = self.generate_unique_handle(handle)
            response = f"Registration Failed. Handle '{handle}' is already in use. Suggestion: '{suggested_handle}'"
            logging.error(response)
        else:
            self.clients[client_address] = handle
            response = f"Client {client_address} registered as {handle}"
            logging.info(response)
        client_socket.sendall(response.encode())

    def generate_unique_handle(self, handle):
        count = 1
        while f"{handle}_{count}" in self.clients.values():
            count += 1

        return f"{handle}_{count}"
    
    def message(self, client_socket, client_address, message, is_broadcast=False):
        if client_address in self.clients:
            sender_handle = self.clients[client_address]
            response = f"{sender_handle} : {message}"
            logging.info(response)

            # Check if it's a broadcast message
            if is_broadcast:
                response = "Broadcast from " + response
                for socket in self.sockets:
                    try:
                        socket.sendall(response.encode())
                    except Exception as e:
                        logging.error(f"Error sending broadcast message: {e}")
            else:
                # Unicast message
                target_user = message.split()[0]
                response = "Unicast from " + response
                message_sent = False  # Flag to check if message was sent to recipient
                for address, handle in self.clients.items():
                    if handle == target_user:
                        try:
                            for socket in self.sockets:
                                if self.clients.get(socket.getpeername()) == target_user:
                                    socket.sendall(response.encode())
                                    message_sent = True
                                    break
                        except Exception as e:
                            logging.error(f"Error sending unicast message: {e}")
                        break
                if message_sent:
                    try:
                        client_socket.sendall(response.encode())
                    except Exception as e:
                        logging.error(f"Error sending confirmation to the sender: {e}")
        else:
            response = "You have not yet registered. Please do /register [name]"
            logging.error(response)
            client_socket.sendall(response.encode())

if __name__ == "__main__":
    server = FileExchangeServer(port=12345)
    server.start()
