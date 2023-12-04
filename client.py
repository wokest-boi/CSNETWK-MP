'''
Machine Project - File Exchange System

Written by:
GO, Michael Joseph
HERCE, Dominic Marcus R.
SINGSON, Keith Railey C.
'''

# import socket library
import socket

"""
    Send a file to the server over the given socket.

    Parameters:
    - socket (socket): The socket used for communication.
    - filename (str): The name of the file to be sent.

    Raises:
    - FileNotFoundError: If the specified file does not exist.

    The function sends the file's content to the server in chunks of 1024 bytes,
    notifying the server about the file using a specific protocol ("/store <filename>\n").
    After sending the file, it waits for the server's response and prints it.

    Note: The file is sent with an "EOF" marker to indicate the end of the file.
"""
def send_file(socket, filename):
    
    try:
        with open(filename, 'rb') as file:
            # Notify server about the file
            socket.sendall(f"/store {filename}\n".encode())

            # Send file content in chunks
            while True:
                data = file.read(1024)
                if not data:
                    # Send EOF in a separate packet
                    socket.sendall(b'EOF')
                    break
                socket.sendall(data)

            # Wait for the server's response
            response = socket.recv(1024)
            print(response.decode())

    except FileNotFoundError:
        print("File not found")  



"""
    Receive a file from the server using the given socket.

    Parameters:
    - socket (socket): The socket used for communication.
    - filename (str): The name of the file to be received and saved.

    The function continuously receives data from the server in chunks of 1024 bytes.
    It checks for the "EOF" marker in the received data to indicate the end of the file.
    If there is data before the "EOF" marker, it is written to the specified file
    (excluding the "EOF" marker). The function breaks out of the loop when the entire
    file has been received.

    After successfully receiving the file, a message is printed indicating the
    successful reception of the file.

    Note: The function assumes that the server sends the "EOF" marker to signify the end of the file.
"""
def receive_file(socket, filename):
    
    with open(filename, 'wb') as file:
        while True:
            data = socket.recv(1024)
            if b'EOF' in data:
                # Check if there's data before the "EOF" marker
                if data[:-3]:
                    # Write data excluding the "EOF" marker
                    file.write(data[:-3])
                break
            # Write received data to the file
            file.write(data)

    print(f"File {filename} received")



"""
    Process a command received from the user and communicate with the server.

    Parameters:
    - client_socket (socket): The socket connected to the server.
    - command (str): The command received from the user.

    The function takes a command and performs the corresponding action:
    - If the command starts with '/store ', it extracts the filename and uses the
      send_file function to send the file to the server.
    - If the command starts with '/get ', it extracts the filename, sends the command
      to the server, and uses the receive_file function to receive the file from the server.
    - If the command is '/dir' or '/register', it sends the command to the server,
      receives the server's response, and prints it.
    - If the command is '/leave', it closes the client socket and exits the program.
    - For any other command, it sends the command to the server, receives the response,
      and prints it.

    Note: The function assumes that the send_file and receive_file functions are defined
    to handle file sending and receiving.

    Note: The server is expected to handle the specified commands and respond accordingly.
    """
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
