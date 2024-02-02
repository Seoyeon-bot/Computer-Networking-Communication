import socket
import os

class TCPTransport:
    # https://www.educative.io/answers/socket-programming-in-python
    # I learned from above online resource to create init and start so that I could simply call this functions and class in client.py cache.py , and server.py
    def __init__(self, server_ip=None, server_port=None, cache_port=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.cache_port = cache_port
        self.server_socket = None
        self.client_socket = None # create client socket as instance.
        self.cache_socket = None

    def start(self):
        if not self.server_socket:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create TCP socket 
            self.server_socket.bind(('0.0.0.0', self.cache_port)) # bind with host, port
            self.server_socket.listen(5)
            
            return self.server_socket
        
        # if server files , cache files, client files doesn't exit then create one
    
    # TCP get method. 
    def get(self, filename, server_ip, server_port):
        # Check if the file exists in the cache
        cache_files_dir = "../cache_files"
        cache_file_path = os.path.join(cache_files_dir, filename)   # find cache path 
        if os.path.isfile(cache_file_path):
            with open(cache_file_path, "rb") as cache_file:    # open cache file for reading binary 
                cache_data = cache_file.read()    # read file. 
           # print("File delivered from cache:", filename)
            return cache_data    # return cache's data 

        # If the file is not found in the cache, fetch it from the server
        server_response = self.fetch_from_server(filename, server_ip, server_port)

        if server_response and server_response != b"File not found":   # case when server_reponse is not None or empty. 
            # Store the file in the cache
            with open(cache_file_path, "wb") as cache_file:   # open cache_file_path and write down server's response. 
                cache_file.write(server_response)
           # print("File fetched from server and stored in the cache.")
            return server_response
       # else:
           # print("File is not on the server. We can't get the file!")

# I will use this fetch method in Cache.py's TCP_handle() method. 
# Use this method to retrive file data from server to cache. if server has client's requested file. 
    def fetch_from_server(self, filename, server_ip, server_port):
        try:
            # Create a socket for sending and receiving data over TCP
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((server_ip, int(server_port)))

            # Send a "GET" request to request the file
            request_msg = f"GET {filename}\n".encode()
            server_socket.send(request_msg)

            # Receive the file data from the server
            server_response = server_socket.recv(550000)  # Adjust the buffer size as needed
            #self.client_socket.send(server_response) # send recieved response to client socket. 
            
            #server_socket.close()
           # print(f"[tcp fetch from server] : {server_response}")
            return server_response
        except Exception as e:
            print(f"Error fetching file from server: {e}")
            return None
    
    
      
        # Send a "get" request to request the file
         # Receive the file data and return it
 

    def put(self, filename, server_ip, server_port,  data):
       
        try:
            sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sender_socket.connect((server_ip, int(server_port)))
         #   print("[+]Connected .. for put method ")
            
            request_msg = f"PUT {filename}\n"
            sender_socket.send(request_msg.encode())
         #   print("TCP data type : " ,type(data))
         #   print("\nTCP trying to send data : ", data )
            sender_socket.send(data)
          #  print("[+] sending data from client to server ... ")
            
            #sender_socket.close()
            #print("[+]Closing client socket ... ")
        except Exception as e:
            print(f"Error: {e}")
       

    def quit(self):
        # close server socket 
        if self.server_socket:
            self.server_socket.close()
            

    def accept(self):
        if not self.server_socket:
            self.start()

        client_socket, addr = self.server_socket.accept()  # connect server socket with client socket.
        # Implement server logic using TCP

    def connect_tcp_socket (self, host, port): 
        self.server_socket.connect((host, port))
    
    # sending 10000 size of data, break down big file into chunk -> may solve my problem 
    def send_data(self, socket, data, chunk_size = 1000):
       # try : 
            size = 0 
            while size < len(data): 
                chunk = data[size : size + chunk_size ]
                
                # error handling 
                if (sent := socket.send(chunk)) == 0: 
                    raise RuntimeError("[-] Socket connection is broken -> Need to be reconnected. ")
                size+=sent 
             #   print("[+] TCP is sending data ... ")
        #except Exception as ex: 
           # print("[-] TCP Eerror sending data : ", ex)
        
    
    def receive_data(self,socket , buffer_size):
        return socket.recv(buffer_size)
    
   
