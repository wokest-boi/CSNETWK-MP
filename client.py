import socket

def send_file(socket, filename):
    try:
        with open(filename, 'rb') as f:
            socket.sendall(f"/store {filename}\n".encode())  # Notify server about the file
            while True:
                data = f.read(1024)
                if not data:
                    socket.sendall(b'EOF')  # Send EOF in a separate packet
                    break
                socket.sendall(data)
        response = socket.recv(1024)  # Wait for the server's response
        print(response.decode())
    except FileNotFoundError:
        print("File not found")



def receive_file(socket, filename):
    with open(filename, 'wb') as f:
        while True:
            data = socket.recv(1024)
            if b'EOF' in data:
                if data[:-3]:  # Check if there's data before EOF
                    f.write(data[:-3])  # Write data excluding the EOF marker
                break
            f.write(data)
    print(f"File {filename} received")


def process_command(client_socket, command):
    if command.startswith('/store '):
        filename = command.split()[1]
        send_file(client_socket, filename)
    elif command.startswith('/get '):
        filename = command.split()[1]
        client_socket.sendall(command.encode())
        receive_file(client_socket, filename)
    elif command in ['/dir', '/register']:
        client_socket.sendall(command.encode())
        response = client_socket.recv(4096)
        print(response.decode())
    elif command == '/leave':
        client_socket.close()
        exit(0)
    else:
        client_socket.sendall(command.encode())
        response = client_socket.recv(1024)
        print(response.decode())

def main():
    client_socket = None

    while True:
        command = input("Enter command: ")

        if command.startswith('/join '):
            if client_socket:
                client_socket.close()
            _, server_ip, server_port = command.split()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, int(server_port)))
            print(f"Connected to {server_ip}:{server_port}")

        elif client_socket:
            process_command(client_socket, command)
        else:
            print("Not connected to any server. Use /join to connect.")

    if client_socket:
        client_socket.close()

if __name__ == "__main__":
    main()
