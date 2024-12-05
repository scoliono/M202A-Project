import socket
import os
import json

# Configuration
SERVER_HOST = '192.168.4.1'  # IP of the server
PORT = 65432                 # Port for communication
FILE_DIR = "./downloads"     # Directory for files

# Ensure the directory exists
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)

# Function to handle received messages
def handle_message(message, conn):
    if message['type'] == 'request':
        # Handle file request
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
        if conn:
            conn.sendall(json.dumps(response).encode())
    elif message['type'] == 'file':
        # Handle file reception
        file_name = message['content']['file_name']
        file_data = message['content']['data']
        save_path = os.path.join(FILE_DIR, file_name)
        with open(save_path, 'w') as f:
            f.write(file_data)
        print(f"File '{file_name}' received and saved.")
    elif message['type'] == 'error':
        # Handle error messages
        print(f"Error: {message['content']}")

# Start the client
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((SERVER_HOST, PORT))
    print(f"Connected to server at {SERVER_HOST}:{PORT}")

    while True:
        try:
            # Receive data from the server
            data = client_socket.recv(1024).decode()
            if not data:
                break
            message = json.loads(data)
            print(f"Received: {message}")
            handle_message(message, client_socket)
        except Exception as e:
            print(f"Error: {e}")
            break
