import socketio
import base64
import time
import threading
from typing import Callable, List

class FileTransferServer:
    def __init__(self, package: 'Package', callback: Callable):
        """
        Initialize the SocketIO server with package and callback.
        :param package: Package object for handling file chunks
        :param callback: Function to call upon completion or termination
        """
        print("[__init__] Initializing FileTransferServer")
        self.host = '192.168.4.1'
        self.port = 65432
        self.package = package
        self.callback = callback
        self.success = True
        self.diff = None
        
        # Tracking variables
        self.remaining_chunks = set()
        self.last_activity_time = None
        self.inactivity_timeout = 10  # 10 seconds
        self.connection_active = False
        
        # Create SocketIO server
        print("[__init__] Setting up SocketIO server")
        self.sio = socketio.Server(always_connect=True)
        self.app = socketio.WSGIApp(self.sio)
        
        # Register server-side event handlers
        self.setup_server_event_handlers()

    def setup_server_event_handlers(self):
        """
        Set up SocketIO event handlers for the server side.
        """
        print("[setup_server_event_handlers] Setting up server event handlers")

        @self.sio.on('connect')
        def on_connect(sid, environ):
            print(f"[on_connect] Client connected: {sid}")
            self.connection_active = True
            self.last_activity_time = time.time()
            print("[on_connect] Connection state updated")

            self.connection_active = True
            self.last_activity_time = time.time()
            
            # If diff is set, start processing chunks after connection
            if hasattr(self, 'diff') and self.diff:
                print("[on_connect] Processing diff on connection")
                # Convert diff to set of remaining chunks
                self.remaining_chunks = set(
                    (chunk.file_path, chunk.block_number, chunk.version) 
                    for chunk in self.diff
                )
                self.process_diff(sid)
                
                # Start inactivity timeout thread
                self.start_inactivity_monitor(sid)
            else :
                print("[on_connect] No diff to process")

        @self.sio.on('request')
        def on_request(sid, data):
            """
            Handle file chunk request from client.
            """
            print(f"[on_request] Received request: {data}")
            # Update last activity time
            self.last_activity_time = time.time()
            print("[on_request] Last activity time updated")
            
            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data.get('version', 1)
            print(f"[on_request] Request details - File Path: {file_path}, Block: {block_number}, Version: {version}")
            
            # Read chunk from package
            chunk_data = self.package.read_chunk(file_path, block_number, version)
            
            if chunk_data:
                print(f"[on_request] Sending chunk: {file_path}, block {block_number}, version {version}")
                response = {
                    'type': 'file',
                    'content': {
                        'file_path': file_path,
                        'block_number': block_number,
                        'version': version,
                        'data': base64.b64encode(chunk_data).decode('utf-8')
                    }
                }
                self.sio.emit('file', response, room=sid)
            else:
                print(f"[on_request] Chunk not found: {file_path}, block {block_number}")
                error_response = {
                    'type': 'error',
                    'content': f"Chunk not found: {file_path}, block {block_number}"
                }
                self.sio.emit('error', error_response, room=sid)

        @self.sio.on('file')
        def on_file(sid, data):
            """
            Process received file chunk.
            """
            print(f"[on_file] Received file chunk: {data}")
            # Update last activity time
            self.last_activity_time = time.time()
            print("[on_file] Last activity time updated")
            
            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data['content'].get('version', 1)
            print(f"[on_file] Processing chunk - File Path: {file_path}, Block: {block_number}, Version: {version}")
            
            # Decode base64 chunk data
            chunk_data = base64.b64decode(data['content']['data'])
            
            # Write chunk to package
            self.package.write_chunk(file_path, block_number, chunk_data, version)
            print(f"[on_file] Chunk '{file_path}' received and saved.")
            
            # Remove this chunk from remaining chunks
            remaining_key = (file_path, block_number, version)
            if remaining_key in self.remaining_chunks:
                self.remaining_chunks.remove(remaining_key)
                print(f"[on_file] Remaining chunks: {len(self.remaining_chunks)}")

        @self.sio.on('disconnect')
        def on_disconnect(sid):
            print(f"[on_disconnect] Client disconnected: {sid}")
            self.connection_active = False
            self.finalize_transfer()

    def setup_client_event_handlers(self, client):
        """
        Set up SocketIO event handlers for the client side.
        This is similar in spirit to the server handlers, 
        but uses the 'client' object and defines handlers for server-initiated events.
        """
        print("[setup_client_event_handlers] Setting up client event handlers")

        @client.on('connect')
        def on_connect():
            print("[client.on_connect] Client connected to server")
            self.connection_active = True
            self.last_activity_time = time.time()
            print("[client.on_connect] Connection state updated")

            # If we have a diff, process it after connection
            if self.diff:
                self.remaining_chunks = set(
                    (chunk.file_path, chunk.block_number, chunk.version) 
                    for chunk in self.diff
                )
                print(f"[client.on_connect] Remaining chunks set: {self.remaining_chunks}")

                # Request out-of-sync chunks from the server
                self.process_diff(client=client)

                # Start inactivity monitor
                self.start_inactivity_monitor(client.sid)

        @client.on('request')
        def on_server_request(data):
            """
            Handle 'request' event sent by the server.
            The server is requesting a file chunk from the client.
            """
            print("[client.on_server_request] Received request from server:", data)
            self.last_activity_time = time.time()

            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data['content'].get('version', 1)

            # If the client can provide chunks (assuming `self.package` exists on client)
            chunk_data = self.package.read_chunk(file_path, block_number, version) if self.package else None

            if chunk_data:
                print(f"[client.on_server_request] Sending chunk: {file_path}, block {block_number}, version {version}")
                response = {
                    'type': 'file',
                    'content': {
                        'file_path': file_path,
                        'block_number': block_number,
                        'version': version,
                        'data': base64.b64encode(chunk_data).decode('utf-8')
                    }
                }
                client.emit('file', response)
            else:
                print(f"[client.on_server_request] Chunk not found: {file_path}, block {block_number}")
                error_response = {
                    'type': 'error',
                    'content': f"Chunk not found: {file_path}, block {block_number}"
                }
                client.emit('error', error_response)

        @client.on('file')
        def on_server_file(data):
            """
            Handle 'file' event from the server.
            The server has sent a file chunk to this client.
            """
            print("[client.on_server_file] Received file chunk:", data)
            self.last_activity_time = time.time()

            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data['content'].get('version', 1)

            chunk_data = base64.b64decode(data['content']['data'])

            # If the client also stores chunks (assuming `self.package` is present)
            self.package.write_chunk(file_path, block_number, chunk_data, version)
            print(f"[client.on_server_file] Chunk '{file_path}' received and saved.")

            # Remove this chunk from remaining chunks if applicable
            remaining_key = (file_path, block_number, version)
            if remaining_key in self.remaining_chunks:
                self.remaining_chunks.remove(remaining_key)
                print(f"[client.on_server_file] Remaining chunks: {len(self.remaining_chunks)}")

        @client.on('error')
        def on_server_error(data):
            """
            Handle 'error' event from server.
            """
            print("[client.on_server_error] Received error from server:", data)

        @client.on('disconnect')
        def on_server_disconnect():
            print("[client.on_server_disconnect] Disconnected from server")
            self.connection_active = False
            self.finalize_transfer()


    def start_inactivity_monitor(self, sid):
        """
        Monitor connection for inactivity and potential closure.
        If no clients are connected and all chunks are processed, stop the server.
        """
        print("[start_inactivity_monitor] Starting inactivity monitor")

        def monitor():
            while True:
                # Check for inactivity or broken connection
                current_time = time.time()
                if not self.connection_active:
                    print("[monitor] Connection broken. Shutting down server.")
                    self.finalize_transfer()
                    break
                elif current_time - self.last_activity_time > self.inactivity_timeout:
                    print("[monitor] Inactivity timeout reached. Shutting down server.")
                    self.finalize_transfer()
                    break

                print("[monitor] Monitoring activity...")
                time.sleep(1)

        # Start monitoring in a separate thread
        threading.Thread(target=monitor, daemon=True).start()

    def finalize_transfer(self):
        """
        Finalize the transfer and call the callback
        """
        print("[finalize_transfer] Finalizing transfer")
        # Ensure this is only called once
        if not hasattr(self, '_finalized'):
            self._finalized = True
            self.success = len(self.remaining_chunks) == 0
            print(f"[finalize_transfer] Transfer {'successful' if self.success else 'failed'}. "
                  f"Remaining chunks: {len(self.remaining_chunks)}")
            self.callback(self.success)

    def process_diff(self, sid=None, client=None):
        """
        Process the diff by requesting chunks
        """
        print("[process_diff] Processing diff")
        if not self.diff:
            print("[process_diff] No diff to process")
            return

        # Determine if we are on the server or client
        on_server = sid is not None

        # Debug: Print whether we're client or server
        if on_server:
            print("[process_diff] Running on server side.")
            # On the server side, we have self.sio.eio.sockets, so we can check if sid is connected
            if hasattr(self.sio, 'eio') and hasattr(self.sio.eio, 'sockets'):
                print(f"[Debug - Server] Sockets connected: {list(self.sio.eio.sockets.keys())}")
                print(f"[Debug - Server] Is sid {sid} connected? {sid in self.sio.eio.sockets}")
            else:
                print("[Debug - Server] Unable to verify sid connection state (no eio.sockets).")
        else:
            print("[process_diff] Running on client side.")
            # On the client side, self.sio is typically a client instance
            print(f"[Debug - Client] Client namespaces: {getattr(self.sio, 'namespaces', 'N/A')}")
            print(f"[Debug - Client] Client SID: {getattr(self.sio, 'sid', 'N/A')}")
            print(f"[Debug - Client] Is client connected? {getattr(self.sio, 'connected', 'N/A')}")

        # Request out-of-sync chunks
        for chunk in self.diff:
            print(f"[process_diff] Requesting chunk: {chunk}")
            request_msg = {
                'type': 'request',
                'content': {
                    'file_path': chunk.file_path,
                    'block_number': chunk.block_number,
                    'version': chunk.version,
                }
            }

            # If on server, use room=sid to emit
            # If on client, just emit directly
            if on_server:
                print(f"[Debug - Server] Emitting 'request' to sid {sid}")
                self.sio.emit('request', request_msg, room=sid)
            else:
                print("[Debug - Client] Emitting 'request' directly to server (no room)")
                client.emit('request', request_msg)


    def start_client(self, diff: List['ChunkVersion']):
        """
        Start the client and request out-of-sync chunks.
        :param diff: The remaining packages to get
        """
        print("[start_client] Starting client")
        try:
            # Store diff for later processing
            self.diff = diff
            print("[start_client] Diff stored for processing")

            # Connect to server
            client = socketio.Client()

            # Set up client event handlers before connecting
            self.setup_client_event_handlers(client)

            print(f"[start_client] Connecting to server at {self.host}:{self.port}")
            client.connect(f'http://{self.host}:{self.port}', wait_timeout=15)
            
            # Keep the client running
            client.wait()
        except Exception as e:
            print(f"[start_client] Client error: {e}")
            self.success = False
            self.finalize_transfer()
        finally:
            # Ensure callback is called
            self.finalize_transfer()

    def start_server(self, diff: List['ChunkVersion'] = None):
        """
        Start the SocketIO server and listen for connections.
        :param diff: Optional diff to process when a client connects
        """
        print("[start_server] Starting server")
        try:
            # Store diff for later processing if provided
            if diff:
                self.diff = diff
                print(f"[start_server] Diff set for processing: {self.diff}")
            else:
                print("[start_server] No diff provided for processing")

            # Import WSGI server (eventlet or threading)
            import eventlet
            print(f"[start_server] Hosting server on {self.host}:{self.port}")
            eventlet.wsgi.server(
                eventlet.listen((self.host, self.port)), 
                self.app
            )
        except Exception as e:
            print(f"[start_server] Server error: {e}")
            self.success = False
            self.finalize_transfer()
        finally:
            # Ensure callback is called
            print("[start_server] Finalizing transfer")
            self.finalize_transfer()
