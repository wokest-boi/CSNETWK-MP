import socket
import os
import threading

file_storage_path = 'file_storage'
clients = {}  # Dictionary to store client information

def handle_client_connection(client_socket, client_address):
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            if data.startswith('/store '):
                filename = data.split()[1]
                store_file(client_socket, filename)
            elif data == '/dir':
                list_files(client_socket)
            elif data.startswith('/get '):
                filename = data.split()[1]
                send_file(client_socket, filename)
            elif data.startswith('/register '):
                handle = data.split()[1]
                register_client(client_address, handle)
            else:
                client_socket.sendall("Unknown command".encode())
        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"Client {client_address} disconnected")
    client_socket.close()
    if client_address in clients:
        del clients[client_address]

def store_file(client_socket, filename):
    with open(os.path.join(file_storage_path, filename), 'wb') as f:
        while True:
            data = client_socket.recv(1024)
            if b'EOF' in data:
                f.write(data.replace(b'EOF', b''))  # Write data excluding the EOF marker
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
                    client_socket.sendall(b'EOF')  # Send EOF marker after file data
                    break
                client_socket.sendall(data)
    else:
        client_socket.sendall('File not found'.encode())


def register_client(client_address, handle):
    """
    Register a client with a unique handle.

    Parameters:
    - client_address: The address of the client.
    - handle: The handle (alias or name) of the client.

    The function checks if the handle is already in use by another client.
    If the handle is not in use, it registers the client with the given handle.
    If the handle is already in use, it suggests an alternative handle.

    Note: The function assumes a global 'clients' dictionary is defined to store client information.
    """
    if handle in clients.values():
        # Handle already in use, suggest an alternative
        suggested_handle = generate_unique_handle(handle)
        print(f"Error: Registration Failed. Handle '{handle}' is already in use.\nSuggestion: try using '{suggested_handle}' instead.")
    else:
        # Register the client with the given handle
        clients[client_address] = handle
        print(f"Client {client_address} registered as {handle}")

def generate_unique_handle(handle):
    """
    Generate a unique handle by appending a number to the original handle.

    Parameters:
    - handle: The original handle.

    Returns:
    - str: A unique handle.
    """
    count = 1
    while f"{handle}_{count}" in clients.values():
        count += 1
    return f"{handle}_{count}"



def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('', 10000)  # Listen on all interfaces
    server_socket.bind(server_address)
    server_socket.listen(5)

    if not os.path.exists(file_storage_path):
        os.makedirs(file_storage_path)

    print("Server is running and waiting for connections...")

    while True:
        connection, client_address = server_socket.accept()
        print(f"Connected to {client_address}")
        client_thread = threading.Thread(target=handle_client_connection, args=(connection, client_address))
        client_thread.start()

if __name__ == "__main__":
    main()
