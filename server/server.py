import os
import socket
import sys

# https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir
# learned from above link regrading sys.path.append()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from tcp_transport import TCPTransport
from stop_and_wait import snw

def main():
    if len(sys.argv) != 3:
        print("Retype: server.py  port transport_protocol")
        return

    port, transport_protocol = sys.argv[1:3]
    #print("Server is running ... ")

    if transport_protocol == 'tcp':
        transport = TCPTransport(cache_port=int(port)) #  I just naemd as cache_port so in TCP start() it can use given port number to create socket.
    elif transport_protocol == 'snw':
        transport = snw(cache_port=int(port))
      
    else:
        print("Invalid transport protocol")
        return
   
    server_files_dir = "../server_files"  # path 
    os.makedirs(server_files_dir, exist_ok=True)

    
    server_socket = transport.start()  # create server socket, bind , listen 
    
    while True: 
        if transport_protocol == 'tcp': 
            
           client_socket, addr = server_socket.accept()  # server accept client socket 
           TCP_handle_client(client_socket)  # call handle client method to perform get , put method for TCP transport
        elif transport_protocol == 'snw': 
            data, client_address = transport.receive_data(1000)
           # print("[+] Received data from client:", client_address)
            if data is not None:  # Check if data is received
                SNW_client_handle(data, client_address, transport)
    
def TCP_handle_client(client_socket): 
    
    client_request = client_socket.recv(1000).decode() 
   # print("client request : ", client_request)
    words = client_request.split()
    
    method = words[0] # get put quit 
    filename = words[1]
    transport = TCPTransport(); 
    server_files_dir = "../server_files"  # path 
    
    
    if method.lower() == "get":
        file_path = os.path.join(server_files_dir , filename)
        if os.path.isfile(file_path): 
            try: 
                
               # print("File path:", file_path)
               # print("Filename:", filename)
                    
                with open(file_path, "rb") as file: 
                  #  print("Opening ", filename , " in file path : ", file_path)
                    data = file.read() 
                 #   print("File read. Length:", len(data))
                client_socket.send(data) # send to clinet socket ( =cache socket )
                # close file 
                file.close()
                # check length of data 
                if len(data)> 0: 
                    # read all and send data to client (client could be cache)
                    transport.send_data(client_socket,data)
                  #  print("[+] Sending data from server to client socket(=Cache socket). ")
            except Exception as ex: 
                print("[-] Error while reading file " , ex)
  
        else:
            # case we couldn't find file in server 
            transport.send_data(client_socket,b"File not found")
           # print("[+] Sending empty data to client socket ... ")
    # case when client request  is put 
    elif method.lower() == "put": 
        file_path = os.path.join(server_files_dir, filename)

        with open(file_path, "wb") as file:
           # print(f"[+]Sever opening file { filename} in file_path { file_path}")
            while True:
                data = client_socket.recv(50000)  # Receive data from the client
              #  print("Server Received data:", data)
                
                if not data:
                    break
                file.write(data)

        print("Server response: File successfully uploaded.")

    client_socket.close()  


##### stop and wait implementation ##########
def SNW_client_handle(data, client_address, snw_instance):
    # I will use snw_instance to send data and receive data. 
    cache_request = data.decode() # change received data from client to string 
   # print("Server: cache_request:", cache_request)
  #  print(f"clinet_address : {client_address}")
    
    server_files_dir = "../server_files"  # path
    words = cache_request.split() # extract 
    method = words[0]
    if len(words) < 2:
        sys.exit(1)  # Exit if there is no filename

    filename = words[1]
    
# case method is get. 
    # Use snw_instance to send and receive data
    if method.lower() == "get": # check method 
         # Received request from the cache
        file_path = os.path.join(server_files_dir, filename)

        if os.path.isfile(file_path):
            with open(file_path, "rb") as file:
                # Read the file data
               # print(f"[Server-Cache] Opening file_path : {file_path}")
                data = file.read()
                data_length = len(data)
                len_msg = f"LEN:{data_length}".encode()
                
                # Send the data length to the cache
                snw_instance.send_data(len_msg, client_address) # client_address is cache address 
               # print(f"Server: Sending data length message: {len_msg} to cache")

                # Send data from server to cache. stop and wait send() will take care of split data into 1000bytes and ACKS, timeout.
                snw_instance.stop_and_wait_send(data, client_address)
                snw_instance.stop_and_wait_send("FIN".encode(), client_address)  # no more data to send to cache -> send FIN -> wait for cache's FIN-ACK
                
                try:
                    FIN_ack , _ = snw_instance.receive_data(1000) # receive data 
                    if FIN_ack.decode() == "FIN-ACK": 
                        #file.close()
                      #  print("[Sender]: received FIN-ACk from Cache ")
                        sys.exit(1)
                    
                except socket.error:
                    print("[Server]  Timeout - Did not receive FIN from cache. Retransmitting FIN-ACK...")
                    snw_instance.stop_and_wait_send("FIN-ACK".encode(), client_address)
             
      
        else:
            print("File not found in the server.")               
                   
   # case method is put 
    elif method.lower() == "put":
        # Parse the filename and length information
    
        file_path = os.path.join(server_files_dir, filename)
        with open(file_path, "wb") as file:
          #  print(f"[+]Sever opening file { filename} for writing in file_path { file_path}")
            # while loop until we receive all data from client. recv data from clinet -> send ACK to client 
            # client will recv ACK -> send next chunk -> server recv data from client -> send CK to client 
            
            while True:
                chunk, client_address = snw_instance.receive_data(1000)  # Adjust buffer size as needed
                
                if chunk is None: # case chunk is empty -> don't write on file. 
                    break
                
                # case chunk is FIN msg -> terminate 
                if chunk == "FIN".encode():
                    fin_msg = "FIN-ACK".encode()
                    snw_instance.send_data(fin_msg, client_address)  # Send a "FIN-ACK" message 
                    #snw_instance.server_socket.close()  # Close the client socket
                    break  # Terminate the loop
                
              #  print("[+] we received chunk from client. ")
        
                file.write(chunk)
               # print("[+]Writing chunk on file...")
                # send ACK to client so we can recieve next chunk
                ack_msg = "ACK".encode(); 
                snw_instance.send_data(ack_msg, client_address); 
                
        file.close()
        print(f"Server response: File successfully uploaded.")
        
    else:
        print("Unsupported method:", method)
   
           
if __name__ == "__main__":
    main()
