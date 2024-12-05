import socket
import os
import json
import base64  # Added for encoding/decoding binary data

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
            with open(file_path, 'rb') as f:  # Open in binary mode
                file_content = base64.b64encode(f.read()).decode('utf-8')  # Encode binary content to base64
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
        file_data = base64.b64decode(message['content']['data'])  # Decode base64 to binary
        save_path = os.path.join(FILE_DIR, file_name)
        with open(save_path, 'wb') as f:  # Write in binary mode
            f.write(file_data)
        print(f"File '{file_name}' received and saved.")
    elif message['type'] == 'error':
        print(f"Error: {message['content']}")

# Start the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")
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
