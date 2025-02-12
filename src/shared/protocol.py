#   'Silent net' project protocol
#   
#       Contains main message types and 
#       Socket handling
#
#   Omer Kfir (C)

import socket
from typing import Optional, Tuple, Union

__author__ = "Omer Kfir"

DEBUG_PRINT_LEN = 50
DEBUG_FLAG = False

class MessageParser:
    PROTOCOL_SEPARATOR = b"\x1f"
    PROTOCOL_DATA_INDEX = 1

    SIG_MSG_INDEX = 0

    # Message types
    CLIENT_MSG_SIG = "C"
    CLIENT_MSG_AUTH = "CAU"
    CLIENT_PROCESS_OPEN = "CPO"
    CLIENT_PROCESS_CLOSE = "CPC"
    CLIENT_INPUT_EVENT = "CIE"

    # Manager commands
    MANAGER_MSG_SIG = "M"
    MANAGER_GET_CLIENTS = "MGC"
    MANAGER_GET_CLIENT_DATA = "MGD"


    """
        Decorator staticmethod does not block a function to be called through an instance
        Rather it ensures that simply not pass a self object to the function even if function called through instance
    """
    
    @staticmethod
    def encode_str(msg : Union[bytes, str]) -> bytes:
        """ Encodes a message """
    
        if type(msg) == str:
            msg = msg.encode()
        
        return msg
    
    @staticmethod
    def protocol_message_construct(msg_type : str, *args):
        """
            Constructs a message to be sent by protocol rules
            
            INPUT: msg_type, *args (Uknown amount of arguments)
            OUTPUT: None
            
            @msg_type -> Message type of the message to be sent
            @args -> The rest of the data to be sent in the message
        """
        
        msg_buf = MessageParser.encode_str(msg_type)
        
        for argument in args:
            msg_buf += MessageParser.PROTOCOL_SEPARATOR + MessageParser.encode_str(argument)
        
        return msg_buf
        
    @staticmethod
    def protocol_message_deconstruct(msg : bytes, part_split : int = -1) -> list[bytes]:
        """
            Constructs a message to be sent by protocol rules
            
            INPUT: msg, part_split
            OUTPUT: List of fields in msg seperated by protocol
            
            @msg -> Byte stream
            @part_split -> Number of fields to seperate from start of message
        """
        
        if msg != b'':
            msg = msg.split(MessageParser.PROTOCOL_SEPARATOR, part_split)
        
        return msg
        

class TCPsocket:
    MSG_LEN_LEN = 4

    def __init__(self, sock: Optional[socket.socket] = None):
        """
            Create TCP socket
            
            INPUT: sock (not necessary)
            OUTPUT: None
            
            @sock -> Socket object (socket.socket)
        """
        
        if sock is None:
            self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        else:
            self.__sock = sock
    
    def set_timeout(self, time):
        """
            Sets a timeout for a socket
            
            INPUT: time
            OUTPUT: None
            
            @time -> Amount of timeout time
        """

        self.__sock.settimeout(time)
    
    def create_server_socket(self, bind_ip : str, bind_port : int, server_listen : int) -> None:
        """
            Prepare a server tcp socket
            
            INPUT: bind_ip, bind_port, server_listen
            OUTPUT: None
            
            @bind_ip -> IP for server to bind
            @bind_port -> Port for server to bind
            @server_listen -> Max amount of client connecting at the same time
        """
        
        self.__sock.bind((bind_ip, bind_port))
        self.__sock.listen(server_listen)
    
    def server_socket_recv_client(self) -> socket.socket:
        """
            Server receives new client
            
            INPUT: None
            OUTPUT: None
            
            @dst_ip -> Destination IP of server
            @dst_port -> Destination Port of server
        """
        
        client_sock, _ = self.__sock.accept()
        return client_sock
        
    
    def client_socket_connect_server(self, dst_ip : str, dst_port : int) -> None:
        """
            Connect client socket to server
            
            INPUT: dst_ip, dst_port
            OUTPUT: None
            
            @dst_ip -> Destination IP of server
            @dst_port -> Destination Port of server
        """
        
        self.__sock.connect((dst_ip, dst_port))
    
    def close(self):
        """
            Closes socket
            
            INPUT: None
            OUTPUT: None
        """
        
        self.__sock.close()

    def log(self, prefix : str, data: Union[bytes, str], max_to_print: int=DEBUG_PRINT_LEN) -> None:
        """
            Prints 'max_to_print' amount of data from 'data'
            
            INPUT: prefix, data, max_to_print
            OUTPUT: None
            
            @prefix -> A prefix for every data to be printed
            @data -> Stream of data (Bytes | string)
            @max_to_print -> Amount of data to printed
        """
        
        if not DEBUG_FLAG:
            return
        
        data_to_log = data[:max_to_print]
        if type(data_to_log) == bytes:
            try:
                data_to_log = data_to_log.decode()
                
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\n{prefix}({len(data)})>>>{data_to_log}")


    def __recv_amount(self, size : int) -> bytes:
        """
            Recevies specified amount of data from connected side
            
            INPUT: None
            OUTPUT: Byte stream
            
            @data -> Stream of bytes
        """
        
        buffer = b''
        
        # Recv until 'size' amount of bytes is received
        while size:
        
            tmp_buf = self.__sock.recv(size)
            
            if not tmp_buf:
                return b''
            
            buffer += tmp_buf
            size -= len(tmp_buf)
        
        return buffer


    def recv(self) -> bytes:
        """
            Recevies data from connected side
            
            INPUT: None
            OUTPUT: Byte stream
            
            @data -> Stream of bytes
        """
        
        data = b''
        data_len = self.__recv_amount(self.MSG_LEN_LEN) #  Recv length of message

        if data_len == b'':
            return data_len
        
        data_len = int(data_len)

        # Recv actual message and log it
        data = self.__recv_amount(data_len)
        self.log("Receive", data)
        
        return data


    def send(self, data : Union[bytes, str]):
        """
            Sends data to connected side
            
            INPUT: data
            OUTPUT: None
            
            @data -> Stream of bytes (can also be a simple string)
        """
        
        length = len(data)
        
        if length == 0:
            return
            
        if type(data) != bytes:
            data = data.encode()
        
        # Pad data with its length
        len_data = str(length).zfill(self.MSG_LEN_LEN).encode()
        data = len_data + data
        
        # Send data and log it
        self.__sock.sendall(data)
        self.log("Sent", data)

    @staticmethod
    def get_free_port() -> int:
        """
            Get free internet port for binding

            INPUT: None
            OUTPUT: None
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Binding to port 0 gives random port
            port = s.getsockname()[1]
        
        return port
    

class client (TCPsocket):
    
    def __init__(self, sock: Optional[socket.socket] = None):
        """
            Create the client side socket
            socket type: TCP
            
            INPUT: sock (not necessary)
            OUTPUT: None
            
            @sock -> Socket object (socket.socket)
        """
        
        super().__init__(sock)
    
        # Add settings in order to get mac address
        self.__mac = ...
    
    def set_address(self, mac_addr) -> None:
        """
            Set client's mac addresss
            
            INPUT: mac_addr
            OUTPUT: None

            @mac_addr -> mac address of client
        """

        self.__mac = mac_addr

    def get_address(self) -> str:
        """
            Returns client's mac address
            
            INPUT: None
            OUTPUT: Address of client's mac
        """
        
        return self.__mac
    
    def connect(self, dst_ip : str, dst_port : int) -> bool:
        """
            Connect client to server
            
            INPUT: dst_ip, dst_port
            OUTPUT: Boolean value which indicated wether managed to connect
            
            @dst_ip -> Destination IP of server
            @dst_port -> Destination Port of server
        """
        
        try:
            self.client_socket_connect_server(dst_ip, dst_port)
            return True
        
        except (ConnectionRefusedError, socket.timeout):
            self.log("Error", "Failed to connect to server")
            self.close()

            return False
    
    def protocol_recv(self, part_split : int = -1) -> list[bytes]:
        """
            Recevies data from connected side and splits it by protocol
            
            INPUT: part_split
            OUTPUT: List of byte streams

            @part_split -> Number of fields to seperate from start of message
        """
        
        data = MessageParser.protocol_message_deconstruct(self.recv(), part_split)
        return data
        
    def protocol_send(self, msg_type, *args) -> None:
        """
            Sends a message constructed by protocll
            
            INPUT: msg_type, *args (Uknown amount of arguments)
            OUTPUT: None
            
            @msg_type -> Message type of the message to be sent
            @args -> The rest of the data to be sent in the message
        """
        
        constr_msg = MessageParser.protocol_message_construct(msg_type, *args)
        self.send(constr_msg)

class server (TCPsocket):
    SERVER_BIND_IP   = "0.0.0.0"
    SERVER_BIND_PORT = 6734

    def __init__(self, server_listen : int = 5):
        """
            Create the server side socket
            socket type: TCP
            
            INPUT: None
            OUTPUT: None
        """
        
        # Create TCP ipv4 socket
        super().__init__()
        
        # Bind socket and set max listen
        self.create_server_socket(self.SERVER_BIND_IP, self.SERVER_BIND_PORT, server_listen)
    
    
    def recv_client(self) -> client:
        """
            Receives a client from server socket
            
            INPUT: None
            OUTPUT: Client object
        """
        
        c = client(self.server_socket_recv_client())
        return c
