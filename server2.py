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

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def prepare_file_storage(self):
        if not os.path.exists(self.file_storage_path):
            os.makedirs(self.file_storage_path)

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self.port))
        server_socket.listen(self.max_connections)
        logging.info("Server is running and waiting for connections...")

        while True:
            connection, client_address = server_socket.accept()
            logging.info(f"Connected to {client_address}")
            client_thread = threading.Thread(target=self.handle_client_connection, args=(connection, client_address))
            client_thread.start()

    def handle_client_connection(self, client_socket, client_address):
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                if data.startswith('/store '):
                    filename = data.split()[1]
                    self.store_file(client_socket, filename)
                elif data == '/dir':
                    self.list_files(client_socket)
                elif data.startswith('/get '):
                    filename = data.split()[1]
                    self.send_file(client_socket, filename)
                elif data.startswith('/register '):
                    handle = data.split()[1]
                    self.register_client(client_socket, client_address, handle)
                else:
                    client_socket.sendall("Unknown command".encode())
            except Exception as e:
                logging.error(f"Error handling client {client_address}: {e}")
                break

        logging.info(f"Client {client_address} disconnected")
        client_socket.close()
        if client_address in self.clients:
            del self.clients[client_address]


    def store_file(self, client_socket, filename):
        with open(os.path.join(self.file_storage_path, filename), 'wb') as f:
            while True:
                data = client_socket.recv(1024)
                if b'EOF' in data:
                    f.write(data.replace(b'EOF', b''))
                    break
                f.write(data)
        client_socket.sendall('File stored successfully'.encode())


    def list_files(self, client_socket):
        files = os.listdir(self.file_storage_path)
        files_list = '\n'.join(files)
        client_socket.sendall(files_list.encode())


    def send_file(self, client_socket, filename):
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

        # Send the response back to the client
        client_socket.sendall(response.encode())



    def generate_unique_handle(self, handle):
        count = 1
        while f"{handle}_{count}" in self.clients.values():
            count += 1
        return f"{handle}_{count}"


if __name__ == "__main__":
    server = FileExchangeServer(port=10000)
    server.start()
