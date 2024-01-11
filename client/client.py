import socket
import sys
import os


# https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tcp_transport import TCPTransport
from stop_and_wait import snw  # class name




def main():
    # https://gaia.cs.umass.edu/kurose_ross/programming/Python_code_only/Web_Proxy_programming_only.pdf 
    # I use umass.edu's approach of spliting input arguments. 
    if len(sys.argv) != 6:
        print("Retype client.py server_IP  server_port  cache_IP  cache_port  transport_protocol ")
        return

    server_ip, server_port, cache_ip, cache_port, transport_protocol = sys.argv[1:6]
    #print("Running Client ... ")

    if transport_protocol == 'tcp':
        transport = TCPTransport(server_ip, int(server_port), int(cache_port))
        
        
    elif transport_protocol == 'snw':
        #transport = snw(server_ip, int(server_port), int(cache_port))
        transport = snw(server_ip, int(server_port), 54321)  # I used random client port number to test. 
    else:
        print("Invalid input transport protocol")
        return

    # create client_files if it doesn't exist 
    client_files_dir = "../client_files"  # path 
    os.makedirs(client_files_dir, exist_ok=True)

# continusly loop over until input is quit 
    while True:
        #print(f"server ip : {server_ip} server port : {server_port}")
       # print(f"cache ip: {cache_ip} cache port : {cache_port}")
        #print(f"client socket : {client_socket}")
        
        command = input("Enter command: ").strip()
        words = command.split()
        # then words[0] = get , words[1] = file3
        if len(words) > 2:
            print("Invalid command")
            continue
        elif len(words) == 1: 
            if words[0].lower() == 'quit': 
                print("Exiting program!")
                transport.quit()
                break
            else: 
                command = input("Enter command: ")
        elif len(words) == 2: 
            action =  words[0]
            filename = words[1]

       
# Handle the GET request in the stop-and-wait protocol
        if transport_protocol == 'snw' and action.lower() == 'get':
            # Create an SNWTransport instance (assuming it's already created)
            client_socket = transport.start()
            destination_address = (cache_ip, int(cache_port))
           # print(f"[+]client : destination addr {destination_address}")
            client_request = f"GET {filename}".encode()
           # print(f"[+] Client: Sending GET request for file {filename} to destination address {destination_address}")

            # Send the GET request to the cache
            transport.send_data(client_request, destination_address)
           # print(f"[+] Client: GET request sent")
            
        
            # Receive and handle data from the cache
            file_path = os.path.join(client_files_dir, filename)
            with open(file_path, "wb") as file: 
                while True:
                    data, addr  = transport.receive_data(1000)  # Provide the buffer size
                  #  print("[Client] received data: ", data)
                    # Send an ACK message to the cache
                    
                    if data == "FIN".encode() :
                        # Received FIN message, break to terminate
                        transport.send_data("FIN-ACK".encode(), addr)
                     #   print("FIle received successfully")
                        sys.exit(1)
                        return
                        break
                    else:
                        transport.send_data("ACK".encode(), destination_address) # change to addr?
                    
                    if data.startswith(b"LEN:"):
                        continue
                    
                    # write on file 
                    file.write(data)
                   # print("[+] Writing chunk to file...")
                    
                    
        print("[+] File received successfully.")
      

# TCP get() case 
        if action.lower() == 'get':
                
            # else TCP get() case 
            file_data = transport.get(filename, cache_ip, int(cache_port))
            
           # print("[+] Recieved file ... ")
            if file_data is not None:
                if file_data:
                    file_path = os.path.join(client_files_dir, filename)
                #  print("file path : ", file_path)

                    # open file
                    with open(file_path, "wb") as file:
                        file.write(file_data)
                    print("Server response: File delivered from cache.")
            else:
                print("Server response: File delivered from origin")
            

# take care of put method  for TCP and snw. 
        elif action.lower() == 'put' :
            file_path = os.path.join(client_files_dir , filename)
            
            if os.path.isfile(file_path):
                with open(file_path , "rb") as file:
                   # print(f"[+]Opening file : { filename} in file_path : { file_path}")
                    data = file.read()
               # print(f"Client data length : {len(data)} ")
                transport.put(filename,server_ip, server_port,  data)
                print("Awaiting server response")
                
    
if __name__ == "__main__":
    main()
