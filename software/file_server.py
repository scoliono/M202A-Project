import socket
import os
import json
import base64  # Added for encoding/decoding binary data
from typing import Callable, List


class FileTransferServer:
    def __init__(self, package: 'Package', callback: Callable):
        """
        Initialize the server with diff dictionary, and a callback function.
        :param diff: A dictionary representing the files to process (key: file name, value: file data).
        :param callback: A function to call with success=True/False upon completion or termination.
        """
        self.host = '192.168.4.1'
        self.port = 65432
        self.package = package
        self.callback = callback
        self.success = True  # Will be set to False if the connection terminates early

    def handle_message(self, message, conn):
        """
        Handle received messages and perform appropriate actions.
        :param message: The received JSON message.
        :param conn: The socket connection object.
        """
        if message['type'] == 'request':
            # Process file chunk request from other peer
            file_path = message['content']['file_path']
            block_number = message['content']['block_number']
            version = message.get('version', 1)
            
            # Read chunk from package
            chunk_data = self.package.read_chunk(file_path, block_number, version)
            
            if chunk_data:
                response = {
                    'type': 'file',
                    'content': {
                        'file_path': file_path,
                        'block_number': block_number,
                        'version': version,
                        'data': base64.b64encode(chunk_data).decode('utf-8')
                    }
                }
            else:
                response = {
                    'type': 'error',
                    'content': f"Chunk not found: {file_path}, block {block_number}"
                }
            
            conn.sendall(json.dumps(response).encode())
        elif message['type'] == 'file':
            # Process received file chunk
            file_path = message['content']['file_path']
            block_number = message['content']['block_number']
            version = message['content'].get('version', 1)
            
            # Decode base64 chunk data
            chunk_data = base64.b64decode(message['content']['data'])
            
            # Write chunk to package
            self.package.write_chunk(file_path, block_number, chunk_data, version)
            print(f"Chunk '{file_name}' received and saved.")
        elif message['type'] == 'error':
            # Log errors
            print(f"Error: {message['content']}")

    def start_client(self, diff: List['ChunkVersion']):
        """
        Start the client, connect to the server, and handle messages.
        :param diff: The remaining packages to get.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((self.host, self.port))
                print(f"Connected to server at {self.host}:{self.port}")

                # Request out-of-sync chunks from server
                for chunk in diff:
                    request_msg = {
                        'type': 'request',
                        'content': {
                            'file_path': chunk.file_path,
                            'block_number': chunk.block_number,
                            'version': chunk.version,
                        }
                    }
                    client_socket.send(json.dumps(request_msg).encode('utf-8'))

                while True:
                    try:
                        # Receive data from the server
                        data = client_socket.recv(10240).decode()
                        if not data:
                            # Connection terminated early
                            self.success = False
                            break

                        response_msg = json.loads(data)
                        print(f"Received: {message}")
                        self.handle_message(response_msg, client_socket)
                    except Exception as e:
                        print(f"Error: {e}")
                        self.success = False
                        break
        finally:
            # Call the callback with the success status
            self.callback(self.success)

    def start_server(self):
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
                    # Request out-of-sync chunks from peer
                    for chunk in diff:
                        request_msg = {
                            'type': 'request',
                            'content': {
                                'file_path': chunk.file_path,
                                'block_number': chunk.block_number,
                                'version': chunk.version,
                            }
                        }
                        client_socket.send(json.dumps(request_msg).encode('utf-8'))

                    while True:
                        try:
                            data = conn.recv(10240).decode()
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
