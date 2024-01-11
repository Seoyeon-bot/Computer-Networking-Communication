import socket
import os
import sys

# https://pythontic.com/modules/socket/recvfrom
# I used above link and textbook codes to understand/implement stop and wait protocol with udp.
class snw:
    # https://codereview.stackexchange.com/questions/159553/python-udp-class-to-control-drone
    # I used above link to learn how udp communicates.  
    def __init__(self, server_ip=None, server_port=None, cache_port=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.cache_port = cache_port
        self.server_socket = None
        self.client_socket = None # create client socket as instanec so we can use 
        self.timer = None # creat timer instance so I can use in other methods. 
        

    def start(self):
        if not self.server_socket:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # create UDP socket 
            self.server_socket.bind(('0.0.0.0', self.cache_port))  # bind 
           # print("[+]Successfully binded...")
            
            return self.server_socket
    
    # client send GET File2.txt data to server. 
    # server receive chunk and sent ACK to client. (regarding put method )
    def send_data(self, data, destination_address):
        self.server_socket.sendto(data, destination_address)
       # print(f"[+]Sending data : {data} TO server  addr : {destination_address}")


    # stop and wait receive data 
    # ex) In put ,server receive 1000 bytes from client.
    def receive_data(self, buffer_size):
        data, client_address = self.server_socket.recvfrom(buffer_size)
       # print(f"[SNW _ receive_data method] Receiving data { data} from clent-addr : { client_address}")
        return data, client_address  # Return both data and client address
    
    # use this method to get file from server to cashe. 
    def get(self, filename, destination_ip, destination_port):
        
        # cache will pass filename , server ip and server port
        dest_addr = (destination_ip, int(destination_port)) # server _address 
        cache_request = f"GET {filename}".encode() # create cache request 
        cache_files_dir = "../cache_files"
        # send cache request from cache to server 
        snw.send_data(self, cache_request, dest_addr) 
       # print(f"[+ Cache]: GET request sent")
        
        # recieve and handle data from server ( communication is between server(sender)- cache(receiver))
        file_path = os.path.join(cache_files_dir, filename)   # find path 
        file_data= b''    # init 
        with open(file_path, "wb") as file: # open file to write binary 
            try:
                self.server_socket.settimeout(1)  # after sending LEN msg, set timeout for 1 second for receving data
                while True: 
                    data, addr = snw.receive_data(self, 1000) # receive data of 1000 bytes 
                # print("[Cache] received data : ", data)
                    
                    if data == "FIN".encode() :    # case whe nreceived ata is FIN
                            # Received FIN message, break to terminate
                            snw.send_data(self, "FIN-ACK".encode(), addr)   # send FIN-ACK back. 
                        # print("FIle received successfully")
                            #return
                            #sys.exit(1)
                            file.close()   # close file. 
                            break
                    else:
                        snw.send_data(self, "ACK".encode(), dest_addr) # same with addr    # else receive data and send ACK back. 
                        
                    if data.startswith(b"LEN:"):
                            # This is a length message, extract the expected data length
                            continue
                    file.write(data)  #  else write on file
                    file_data+=data
                #  print("[+] Writing chunk to file...")
            except socket.timeout:
                print("Did not receive data. Terminating.")  # timeout case1 : Timeout after LEN message
            
                
        return file_data        
        
        
    
#   Stop and wait protocol put method. 
    def put(self, filename, destination_ip, destination_port, data):
        try:
            # Create a socket for sending and receiving data over UDP
            sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Define the destination address
            destination_address = (destination_ip, int(destination_port)) # Always convert string type port  into integer 
          # print(f"destination_addr : {destination_address}") # server IP, port#

            data_length = len(data)   # calculate sending data's length. 
          #  print(f"[SNW PUT(): data length : {data_length}]")
            request_msg = f"PUT {filename} LEN:{data_length}".encode()  # create put request method and encode(change to string type )
            sender_socket.sendto(request_msg, destination_address)  # send request message 
           # print(f"[Client-SNW PUT()] : Sending request_msg : {request_msg} to destination address { destination_address}")

            # Split and send the data in chunks
            chunk_size = 1000
            chunk_list = []  # Create an empty list to store data chunks
           # print("Split data into 10000 bytes chunk")
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]  # split data from index i to index i+chuck_size and set that data as chunk 
                chunk_list.append(chunk)  # Add the chunk to the list of chunks

            for chunk in chunk_list:  # iterate over chunk list 
                sender_socket.sendto(chunk, destination_address)  # Send the chunk to the destination
              #  print(f"[SNW PUT()]: Sending chuck to dest addr { destination_address}")
                sender_socket.settimeout(1) # wait for ACK with 1 second timeout 
                try:
                    ack_msg, _ = sender_socket.recvfrom(5)  # Receive ACK
                    

                    if ack_msg.decode() != "ACK":
                    # print("Acknowledgment not received")
                        return
                #  print("[SNW PUT()] : Received ACK from server socket.")
                except socket.timeout:
                    print("“Did not receive ACK. Terminating.") # timeout case2: Timeout after a data packet
                    return

            # Send a "FIN" message to signal connection termination
            fin_msg = "FIN".encode()
            sender_socket.sendto(fin_msg, destination_address)
          #  print("[SNW PUT client side ] : send FIN to close connection.")
            
            # Wait for an acknowledgment (ACK) from the receiver
            ack_msg, source_address = sender_socket.recvfrom(5)  # Receive ACK (e.g., "FIN-ACK")

            if ack_msg.decode() == "FIN-ACK":
              #  print("Received FIN-ACK from the receiver. Connection terminated.")
                return # or quit terminate 
           # else:
               # print("Did not receive FIN-ACK. Connection termination failed.")

        except Exception as e:
            print("Data transmission terminated prematurely.")

    
    # quit, close socket. 
    def quit(self):
        if self.server_socket:
            self.server_socket.close() 
    
    
    # UDP transfortation with stop and wait 
    # need to calculate total bytes of data using LEN :Bytes 
    # sencond sender splis data into 1000 bytes each. then receiver sends ACK
    # once sender received ACK, we can send other chucks. 


    def receive_data_with_snw(self, client_addr, length):
        received_data = b''  # Initialize an empty bytes object to store received data
        chunk_size = 1000  # The expected size of each chunk
       # print(f"[SNW receive_data_with snw] length : {length}")
        
        while len(received_data) < length:
            # Receive a chunk of data from the sender
            chunk, sender_addr = self.server_socket.recvfrom(chunk_size) # sneder address is cache addr
          #  print(f"[SNW receive_Data_with snw] Received chunk from client addr : {sender_addr}")
          #  print(f"[SNW get() ] chunk : {chunk}")
            
            # FIN message -> terminate 
            if chunk == "FIN-ACK".encode():
              #  print("Received FIN, data transfer completed")
                #self.stop_and_wait_send("FIN-ACK".encode(), client_addr)  # send FIN msg to sender(cache)
                #print(f"Sent FIN to server {sender_addr}")
                break
            
            # use this to not inclued LEN message in client file. 
            if not chunk.startswith(b"LEN:"):
                received_data += chunk
        
            # Send an acknowledgment (ACK) back to the sender (cache)
            ack = "ACK".encode()
            self.server_socket.sendto(ack, sender_addr) # self.client_addr
           # print(f"[+] Sent ACK to sender {sender_addr}")

       # print("we received data")
        return received_data
    
    # In get File : Cache send FIN to client 
    # In get File: Cache sends FIN to the client
    def stop_and_wait_send(self, data, addr):
        chunk_size = 1000

        if data == "FIN".encode():
            ack_received = True  # Terminate the connection
            return
        # calcualte data's total length to split data into 1000 bytes using for loop 
        total_length = len(data)
        #print(f"[SNW stop and wait send() ]: toal length of data : {total_length}")
        
        # Split chunk into 10000 bytes
        for i in range(0, total_length, chunk_size):
            chunk = data[i:i + chunk_size] # i : starting point  , i+chunk : next 1000bytes data
            
            if not chunk : # chuck is empty,there are no more chunk to send 
                break
            
            # handle LEN: message that need to be sent by sender ( cache/ server)
            length_msg = f"LEN:{len(chunk)}".encode()
            ack_received = False # defulat 
        
            while not ack_received:
                self.server_socket.sendto(length_msg, addr)  # Send length message to client.
              #  print(f"[SNW stop and wait send()]: Sending length msg {length_msg} to addr {addr}")
                # wait for ACK from client side( receiver)
                try:
                    self.server_socket.settimeout(1)  # wait 1 second
                    ack, sender_addr = self.server_socket.recvfrom(1000) # recv ack from server/cache regarding leght_msg 
                    ack = ack.decode()
                  #  print(f"[SNW send()] we got ACK : {ack}")

                    if ack == "ACK":
                        ack_received = True
                      #  print("[Stop and Wait Send()]  Received ACK")
                    # additional
                    elif ack == "FIN-ACK":
                        self.server_socket.sendto("FIN-ACK".encode(), addr)
                        break

                except socket.timeout:
                    print("[SNW stop and wait send()]: ACK (X) Retransmitting...")
            
            self.server_socket.sendto(chunk, addr)  # Send the chunk
          #  print(f"[send()]: Sending chuck {chunk} to  receiver addr { addr }")
            ack_received = False

            while not ack_received:
                try:
                    self.server_socket.settimeout(1)  # Set a timer for receiving ACKs for data chunks
                    ack, sender_addr = self.server_socket.recvfrom(1000)
                    ack = ack.decode()

                    if ack == "ACK":
                        ack_received = True
                      #  print(f"[send()]Received ACK from receiver {addr }")

                except socket.timeout:
                    print("Did not receive ACK for chunk. Retransmitting...")

        # After sending all data chunks, send a "FIN" message to indicate the end of data
        fin_msg = "FIN".encode()
        self.server_socket.sendto(fin_msg, addr)
     #   print(f"[send()] Done send FIN to receiver addr {addr }")



            
    
