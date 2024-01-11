import socket  # Creating socket purpose 
import sys   # exit purpose 
import os   # finding file path purpose / check wehther file is existing. 

# https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# importing other class's method to use inside cache.py 
from tcp_transport import TCPTransport
from stop_and_wait import snw

def main():
    if len(sys.argv) != 5:  # look at number of input length. 
        print("Retype: cache.py port  server_IP  server_port  transport_protocol ")
        return

    port, server_ip, server_port, transport_protocol = sys.argv[1:5]  # divide inputs into each info 
   # print("Cache is running ... ")

    if transport_protocol == 'tcp':  # check which transportation we need to use. 
        transport = TCPTransport(server_ip, int(server_port), cache_port=int(port))  # make sure cast string into int type 
    elif transport_protocol == 'snw':
        transport = snw(server_ip, int(server_port), cache_port=int(port))
    else:
        print("Invalid transport protocol")    # take care invalid transport protocol case 
        return

    cache_files_dir = "../cache_files"  # set path for cach_file_directory - we will store .txt file in here. 
    # https://www.w3schools.com/python/ref_os_mkdir.asp - used this website to learn about make directory. 
    os.makedirs(cache_files_dir, exist_ok=True)  # if this directory is not created, then create. 
    
    
    cache_socket = transport.start()   # creates cache socket, bind ,and listen 
    
    while True:  # infinite loop until user type quit. 
        if transport_protocol == 'tcp': 
            client_socket, client_addr = cache_socket.accept()  
            client_ip = client_addr[0];
        
            #print(f"client addr : {addr}")
           # print("[+] Cache TCP : connection established ")
            TCP_handle_client(client_socket, server_ip, int(server_port), client_ip, int(port))   # TCP case 
        elif transport_protocol == 'snw': 
            # stop_and_wait_receive(self, buffer_size): 
            received_data, client_addr = transport.receive_data(1000)  # cache_socket.recvfrom(1000) # recv client request 
            #print(f"SNW client addr : {client_addr}")
            filename = received_data
          #  print(f"[+] transport_protocol: {transport_protocol}, finame : { filename}, client_addr : {client_addr} , server_ip : {server_ip}, server_port: {int(server_port)}")
            handle_get_request(transport, filename, client_addr, server_ip, server_port)  # stop and wait case 
           
    
# handling client's request with TCP protocol. 
# https://alexanderell.is/posts/simple-cache-server-in-python/
# I got an idea from above resource about how I want to approach to cache 
def TCP_handle_client (client_socket, server_ip, server_port, client_ip, client_port):
    client_request = client_socket.recv(1000).decode()  # recieve client request and decode it. 
    #print("[+] Received client request :  ", client_request)
    
    words = client_request.split()   #split, so divide. 
    action = words[0]
    filename = words[1]
    cache_files_dir = "../cache_files"   # indicate cache file_dir location. 
    

    if action.lower() == 'get':   # TCP transport and when user type get 
       # print("Filename: ", filename)
        file_path = os.path.join(cache_files_dir , filename)  # set file_path for specific file. 
        #print("Found ", filename ," path : ", file_path)

        try:
            with open(file_path, "rb") as file:  # open file. 
               # print("[+] We opened", filename, "in cache folders")
                file_data = file.read()
                #print(file_data) # print out file_data to see 
                
              #  print("File read. Length: ", len(file_data)) # check lenght of data 
            client_socket.send(file_data)
           # print("[+] Cache is sending data to client_socket")
            # if we opend file_data then close it after sending file to client. 
            #file_data.close() 
        except FileNotFoundError: 
            client_socket.send(b"File not found")
           # print("[+] File not found in the cache")
            
            transport =  TCPTransport (); 
            server_response = transport.fetch_from_server(filename, server_ip, server_port)
            tcp_cache_received_file(client_ip, int(client_port), server_response, filename) # write data into cache_files_directory. 
            
           # print("[+] forward client request to server ... ")

 
   # client_socket.close()
   # print("[+] Closing client socket ... ")


def tcp_cache_received_file(client_ip, client_port, data, filename):
    cache_files_dir = "../cache_files"
    file_path = os.path.join(cache_files_dir, filename)
    
   
    file_data=b''; 
    if data is not None:
        with open(file_path, "wb") as file:
            file.write(data)
            file_data+= data
    
        send_file_to_client(client_ip, int(client_port), filename, file_data)
    
    else:
        print("Received 'None' data from the server. Nothing to write to the cache.")
    

        
# we got file from server to cache and stored that file in cache_files now we will send that file to client 
def send_file_to_client( client_ip, client_port, filename, data):
    try:
        # Create a socket for communication with the client
        
        cache_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cache_socket.connect((client_ip, int(client_port)))       # Connect to the client#
      
        client_files_dir = "../client_files"
        file_path = os.path.join(client_files_dir, filename)
    
        #print(f"data: {data}")
        
        if data is not None: 
            with open(file_path, "wb") as file:
                file.write(data)
        
        cache_socket.send(data) # Send the file data to the client
        #cache_socket.close()  # Close the socket
        
      #  print(f"File '{filename}' sent to the client {client_ip}:{client_port}")

    except Exception as e:   # handle exception
        print(f"Error in send_file_to_client(): {e}")
        
        
# UDP + Stop and Wait protocol :  take care client's request.     
def handle_get_request(transport, Filename, client_addr, server_ip, server_port):
    cache_files_dir = "../cache_files"
    chunk_size = 1000   # init chunk_size

    # Extract the filename from the client request
    words = Filename.decode().split()
    if len(words) < 2:
        sys.exit(1)  # Exit if there is no filename

        
    filename = words[1]
    file_path = os.path.join(cache_files_dir, filename)  # find file_path 

    if os.path.isfile(file_path):  # if file_path and file is existing. 
        # File exists in the cache
        with open(file_path, "rb") as file:  # open file for reading binary
          #  print(f"[Cache -client] Opening file_path : {file_path}")
            data = file.read()    # read data from file. 
            data_length = len(data)   # sender cacluate length of data
            length_msg = f"LEN:{data_length}".encode()
            transport.send_data(length_msg, client_addr)   # send length message to client socket. 
            #transport.stop_and_wait_send(len_msg, client_addr)
          #  print(f"[Cache] Sent length message using send() ")
            
            transport.stop_and_wait_send(data, client_addr)    # stop_and_wait_send() will split big chunk into 1000 bytes chunk, 
          #  print(f"[Cache]sent data using send() ")
            
            transport.stop_and_wait_send("FIN".encode(), client_addr)   # no more data to send to  client -> send FIN message to client  to terminate 
            #transport.send_data("FIN-ACK".encode(), client_addr)
            
            FIN_ack , _ = transport.receive_data(1000)   # recieve FIN-ACK from client then terminate 
            if FIN_ack.decode() == "FIN-ACK": 
                file.close()
                #transport.quit()  # close terminate
                sys.exit(1) 
        print(f"Server repsonse: File Delivered from cache")            
            
       # print("Data transfer completed.")

    else:
        # File not in cache, forward the request to the server
       # print(f"[Cache] Cashe doesn't have requested file {filename}. So Search in Server side! ")
        response = transport.get(filename, server_ip, int(server_port))  # Forward request to server
        # reponse will hold file_data. and file is already saved in cache_files folder 
        if response:
            # Send the data to the client - same as Client-Cashe communication. 
            data_length = len(response)
            length_msg = f"LEN:{data_length}".encode()
            transport.send_data(length_msg, client_addr)  # send len_msg
            transport.stop_and_wait_send(response, client_addr)  # send recieved data from server. 
            
            transport.stop_and_wait_send("FIN".encode(), client_addr)  # send FIN message 
            transport.send_data("FIN-ACK".encode(), client_addr)
            
            #print("Data transfer completed.")
        print(f"Server repsonse: File Delivered from origin")
        


if __name__ == "__main__":
    main()
