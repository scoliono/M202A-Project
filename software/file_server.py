import socket
import os
import json

# Configuration
HOST = '192.168.4.1'  # Static IP
PORT = 65432          # Port
FILE_DIR = "./shared_files"  # Directory for files

# Ensure the directory exists
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)

# Function to handle received messages
def handle_message(message, conn):
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
        else:
            response = {
                'type': 'error',
                'content': f"File '{file_name}' not found."
            }
        conn.sendall(json.dumps(response).encode())
    elif message['type'] == 'file':
        file_name = message['content']['file_name']
        file_data = message['content']['data']
        save_path = os.path.join(FILE_DIR, file_name)
        with open(save_path, 'w') as f:
            f.write(file_data)
        print(f"File '{file_name}' received and saved.")

# Start the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")
        with conn:
            while True:
                try:
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                    message = json.loads(data)
                    print(f"Received: {message}")
                    handle_message(message, conn)
                except Exception as e:
                    print(f"Error: {e}")
                    break
