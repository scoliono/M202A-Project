import socket
import json
import os

# Configuration
HOST = '192.168.4.1'  # IP of the server
PORT = 65432          # Port
FILE_DIR = "./downloads"  # Directory for files

# Ensure the directory exists
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)

# Function to handle received messages
def handle_message(message, conn=None):
    if message['type'] == 'request':
        file_name = message['content']
        file_path = os.path.join(FILE_DIR, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                file_content = f.read()
            response = {
                'type': 'file',
                'content': {
                    'file_name': file_name,
                    'data': file_content
                }
            }
            if conn:
                conn.sendall(json.dumps(response).encode())
        else:
            response = {
                'type': 'error',
                'content': f"File '{file_name}' not found."
            }
            if conn:
                conn.sendall(json.dumps(response).encode())
    elif message['type'] == 'file':
        file_name = message['content']['file_name']
        file_data = message['content']['data']
        save_path = os.path.join(FILE_DIR, file_name)
        with open(save_path, 'w') as f:
            f.write(file_data)
        print(f"File '{file_name}' received and saved.")

# Start the client
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    print(f"Connected to server at {HOST}:{PORT}")

    while True:
        action = input("Enter 'send' to send a file, 'request' to request a file, or 'quit' to exit: ").strip().lower()

        if action == 'send':
            file_name = input("Enter the name of the file to send: ")
            file_path = os.path.join(FILE_DIR, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    file_data = f.read()
                message = {
                    'type': 'file',
                    'content': {
                        'file_name': file_name,
                        'data': file_data
                    }
                }
                client_socket.sendall(json.dumps(message).encode())
            else:
                print(f"File '{file_name}' not found in '{FILE_DIR}'.")

        elif action == 'request':
            file_name = input("Enter the name of the file to request: ")
            message = {
                'type': 'request',
                'content': file_name
            }
            client_socket.sendall(json.dumps(message).encode())
            response = client_socket.recv(1024).decode()
            if response:
                handle_message(json.loads(response))

        elif action == 'quit':
            print("Exiting...")
            break
