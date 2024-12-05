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
        self.host = '192.168.4.1'
        self.port = 65432
        self.package = package
        self.callback = callback
        self.success = True
        self.diff = None
        
        # Tracking variables
        self.remaining_chunks = set()
        self.last_activity_time = None
        self.inactivity_timeout = 5  # 5 seconds
        self.connection_active = False
        
        # Create SocketIO server
        self.sio = socketio.Server()
        self.app = socketio.WSGIApp(self.sio)
        
        # Register event handlers
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """
        Set up SocketIO event handlers for different types of messages.
        """
        @self.sio.on('connect')
        def on_connect(sid, environ):
            print(f"Client connected: {sid}")
            self.connection_active = True
            self.last_activity_time = time.time()
            
            # If diff is set, start processing chunks after connection
            if hasattr(self, 'diff') and self.diff:
                # Convert diff to set of remaining chunks
                self.remaining_chunks = set(
                    (chunk.file_path, chunk.block_number, chunk.version) 
                    for chunk in self.diff
                )
                self.process_diff(sid)
                
                # Start inactivity timeout thread
                self.start_inactivity_monitor(sid)

        @self.sio.on('request')
        def on_request(sid, data):
            """
            Handle file chunk request from client.
            """
            # Update last activity time
            self.last_activity_time = time.time()
            
            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data.get('version', 1)
            
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
                self.sio.emit('file', response, room=sid)
            else:
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
            # Update last activity time
            self.last_activity_time = time.time()
            
            file_path = data['content']['file_path']
            block_number = data['content']['block_number']
            version = data['content'].get('version', 1)
            
            # Decode base64 chunk data
            chunk_data = base64.b64decode(data['content']['data'])
            
            # Write chunk to package
            self.package.write_chunk(file_path, block_number, chunk_data, version)
            print(f"Chunk '{file_path}' received and saved.")
            
            # Remove this chunk from remaining chunks
            remaining_key = (file_path, block_number, version)
            if remaining_key in self.remaining_chunks:
                self.remaining_chunks.remove(remaining_key)
                print(f"Remaining chunks: {len(self.remaining_chunks)}")

        @self.sio.on('disconnect')
        def on_disconnect(sid):
            print(f"Client disconnected: {sid}")
            self.connection_active = False
            self.finalize_transfer()

    def start_inactivity_monitor(self, sid):
        """
        Monitor connection for inactivity and potential closure
        """
        def monitor():
            while self.connection_active:
                # Check for inactivity
                current_time = time.time()
                if (current_time - self.last_activity_time > self.inactivity_timeout and 
                    len(self.remaining_chunks) == 0):
                    print("Inactivity timeout reached. Closing connection.")
                    self.connection_active = False
                    self.sio.disconnect(sid)
                    self.finalize_transfer()
                    break
                
                # Check every second
                time.sleep(1)
        
        # Start monitoring in a separate thread
        threading.Thread(target=monitor, daemon=True).start()

    def finalize_transfer(self):
        """
        Finalize the transfer and call the callback
        """
        # Ensure this is only called once
        if not hasattr(self, '_finalized'):
            self._finalized = True
            self.success = len(self.remaining_chunks) == 0
            print(f"Transfer {'successful' if self.success else 'failed'}. "
                  f"Remaining chunks: {len(self.remaining_chunks)}")
            self.callback(self.success)

    def process_diff(self, sid):
        """
        Process the diff by requesting chunks
        """
        if not self.diff:
            print("No diff to process")
            return

        # Request out-of-sync chunks
        for chunk in self.diff:
            request_msg = {
                'type': 'request',
                'content': {
                    'file_path': chunk.file_path,
                    'block_number': chunk.block_number,
                    'version': chunk.version,
                }
            }
            self.sio.emit('request', request_msg, room=sid)

    def start_client(self, diff: List['ChunkVersion']):
        """
        Start the client and request out-of-sync chunks.
        :param diff: The remaining packages to get
        """
        try:
            # Store diff for later processing
            self.diff = diff

            # Connect to server
            client = socketio.Client()
            
            # Set up client-side event handlers
            @client.on('connect')
            def on_connect():
                # Track connection state
                self.connection_active = True
                self.last_activity_time = time.time()
                
                # Convert diff to set of remaining chunks
                self.remaining_chunks = set(
                    (chunk.file_path, chunk.block_number, chunk.version) 
                    for chunk in diff
                )
                
                # Process diff after connection
                self.process_diff(client.sid)
                
                # Start inactivity monitor
                self.start_inactivity_monitor(client.sid)
            
            # Connect to the server
            client.connect(f'http://{self.host}:{self.port}', wait_timeout=10)
            
            # Keep the client running
            client.wait()
        except Exception as e:
            print(f"Client error: {e}")
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
        try:
            # Store diff for later processing if provided
            if diff:
                self.diff = diff

            # Import WSGI server (eventlet or threading)
            import eventlet
            eventlet.wsgi.server(
                eventlet.listen((self.host, self.port)), 
                self.app
            )
        except Exception as e:
            print(f"Server error: {e}")
            self.success = False
            self.finalize_transfer()
        finally:
            # Ensure callback is called
            self.finalize_transfer()