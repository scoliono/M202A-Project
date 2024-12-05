import socket
import os
import json
import base64  # Added for encoding/decoding binary data


class FileTransferClient:
    def __init__(self, diff, callback):
        """
        Initialize the client with diff dictionary, and a callback function.
        :param diff: A dictionary representing the files to process (key: file name, value: file data).
        :param callback: A function to call with success=True/False upon completion or termination.
        """
        self.server_host = '192.168.4.1'
        self.port = 65432
        self.file_dir = './downloads'
        self.diff = diff
        self.callback = callback
        self.success = True  # Will be set to False if the connection terminates early or errors occur

        # Ensure the directory exists
        os.makedirs(self.file_dir, exist_ok=True)

    def handle_message(self, message, conn):
        """
        Handle received messages and perform appropriate actions.
        :param message: The received JSON message.
        :param conn: The socket connection object.
        """
        if message['type'] == 'request':
            # Process file request
            file_name = message['content']
            file_path = os.path.join(self.file_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:  # Open in binary mode
                    file_content = base64.b64encode(f.read()).decode('utf-8')  # Encode binary to base64
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
            # Save received file
            file_name = message['content']['file_name']
            file_data = base64.b64decode(message['content']['data'])  # Decode base64 to binary
            save_path = os.path.join(self.file_dir, file_name)
            with open(save_path, 'wb') as f:  # Write in binary mode
                f.write(file_data)
            print(f"File '{file_name}' received and saved.")
        elif message['type'] == 'error':
            # Log errors
            print(f"Error: {message['content']}")

    def start(self):
        """
        Start the client, connect to the server, and handle messages.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((self.server_host, self.port))
                print(f"Connected to server at {self.server_host}:{self.port}")

                while True:
                    try:
                        # Receive data from the server
                        data = client_socket.recv(1024).decode()
                        if not data:
                            # Connection terminated early
                            self.success = False
                            break

                        message = json.loads(data)
                        print(f"Received: {message}")
                        self.handle_message(message, client_socket)
                    except Exception as e:
                        print(f"Error: {e}")
                        self.success = False
                        break
        finally:
            # Call the callback with the success status
            self.callback(self.success)
