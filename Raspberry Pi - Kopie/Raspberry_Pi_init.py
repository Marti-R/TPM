import socket

# Create a Server Socket and wait for a client to connect
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 6666))
print("UDPServer Waiting for client on port 6666")
server_socket.listen(2)
con, client = server_socket.accept()
print(con, client)


def Func1():
    con.send("0".encode())
    print("Func1")


def Func2():
    print("Func2")


def Stop():
    con.send("shutdown".encode())
    server_socket.close()
    quit()


options = {"0": Func1,
           "3": Func2,
           "4": Stop,
           }

# Recive data from client and decide which function to call
while True:
    dataFromClient, address = con.recvfrom(256)
    try:
        options[dataFromClient.decode()]()
    except KeyError as error:
        con.send("Unknown byte received.".encode())

