import socket
import os
import json
import base64  # Added for encoding/decoding binary data


class FileTransferServer:
    def __init__(self, config, diff, callback):
        """
        Initialize the server with configuration, diff dictionary, and a callback function.
        :param config: A dictionary containing HOST, PORT, and FILE_DIR.
        :param diff: A dictionary representing the files to process (key: file name, value: file data).
        :param callback: A function to call with success=True/False upon completion or termination.
        """
        self.host = config.get('HOST', '192.168.4.1')
        self.port = config.get('PORT', 65432)
        self.file_dir = config.get('FILE_DIR', './shared_files')
        self.diff = diff
        self.callback = callback
        self.success = True  # Will be set to False if the connection terminates early

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
        Start the server, accept connections, and handle messages.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((self.host, self.port))
                server_socket.listen()
                print(f"Server listening on {self.host}:{self.port}")

                conn, addr = server_socket.accept()
                print(f"Connected by {addr}")

                with conn:
                    while True:
                        try:
                            data = conn.recv(1024).decode()
                            if not data:
                                # Connection terminated early
                                self.success = False
                                break

                            message = json.loads(data)
                            print(f"Received: {message}")
                            self.handle_message(message, conn)
                        except Exception as e:
                            print(f"Error: {e}")
                            self.success = False
                            break
        finally:
            # Call the callback with the success status
            self.callback(self.success)