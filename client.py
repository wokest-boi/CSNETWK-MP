import socket

def main():
    client_socket = None

    while True:
        command = input()  # User input without a prompt

        if command.startswith('/join '):
            if client_socket:
                client_socket.close()  # Close existing connection if any
            _, server_ip, server_port = command.split()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, int(server_port)))
            print(f"Connected to {server_ip}:{server_port}")

        elif command == '/leave':
            if client_socket:
                client_socket.close()
                client_socket = None
                print("Disconnected from the server.")
            break

        elif client_socket:
            # Send other commands to the server
            if command.startswith('/store '):
                filename = command.split()[1]
                send_file(client_socket, filename)
            elif command.startswith('/get '):
                filename = command.split()[1]
                receive_file(client_socket, filename)
            else:
                client_socket.sendall(command.encode())
                response = client_socket.recv(1024)
                print(response.decode())
        else:
            print("Not connected to any server. Use /join to connect.")

    if client_socket:
        client_socket.close()

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
    except FileNotFoundError:
        print("File not found")


def receive_file(socket, filename):
    with open(filename, 'wb') as f:
        while True:
            data = socket.recv(1024)
            if data.endswith(b'EOF'):
                data = data[:-3] 
                f.write(data)
                break
            f.write(data)
    print(f"File {filename} received")


if __name__ == "__main__":
    main()
