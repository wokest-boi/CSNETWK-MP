import socket
import os

file_storage_path = 'file_storage'

def handle_command(command, client_socket):
    if command.startswith('/store '):
        filename = command.split()[1]
        store_file(client_socket, filename)
    elif command == '/dir':
        list_files(client_socket)
    elif command.startswith('/get '):
        filename = command.split()[1]
        send_file(client_socket, filename)
    else:
        response = "Unknown command".encode()
        client_socket.sendall(response)

def store_file(client_socket, filename):
    with open(os.path.join(file_storage_path, filename), 'wb') as f:
        while True:
            data = client_socket.recv(1024)
            if not data or data.endswith(b'EOF'):
                break
            f.write(data)
    client_socket.sendall('File stored successfully'.encode())


def list_files(client_socket):
    files = os.listdir(file_storage_path)
    files_list = '\n'.join(files)
    client_socket.sendall(files_list.encode())

def send_file(client_socket, filename):
    filepath = os.path.join(file_storage_path, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                client_socket.sendall(data)
        client_socket.sendall(b'EOF')
    else:
        client_socket.sendall('File not found'.encode())

def get_server_ip():
    """Get the server's local IP address."""
    try:
        # Create a temporary socket to determine the local IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
            # Connect the socket to a public DNS server
            temp_socket.connect(("8.8.8.8", 80))
            # Get the socket's own address
            server_ip = temp_socket.getsockname()[0]
            return server_ip
    except Exception:
        # Fallback in case the above method fails
        return 'localhost'

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_port = 10000  # Port to listen on

    # Bind the socket to all interfaces
    server_socket.bind(('', server_port))
    server_socket.listen(1)

    if not os.path.exists(file_storage_path):
        os.makedirs(file_storage_path)

    # Get the server's IP and announce it
    server_ip = get_server_ip()
    print(f"Server is running on IP {server_ip} and waiting for connections on port {server_port}")

    while True:
        connection, client_address = server_socket.accept()
        try:
            print(f"Connected to {client_address}")
            while True:
                data = connection.recv(1024).decode()
                if data:
                    handle_command(data, connection)
                else:
                    break
        finally:
            print(f"Disconnected from {client_address}")
            connection.close()

if __name__ == "__main__":
    main()
