import socket
import paramiko
import os
import select

# raspi_ip = '192.168.178.84'
# raspi_ip = '192.168.178.47'
raspi_ip = '169.254.233.213'
# raspi_ip = '169.254.110.250'
username = 'root'
password = 'TPM'
port = 6666

path_raspi = '/home/pi/Desktop/TPM/'
path_pc = ''

#ssh = paramiko.SSHClient()
#ssh.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
#ssh.connect(raspi_ip, username=username, password=password)

#ssh_transp = ssh.get_transport()
#outdata, errdata = '', ''
#chan = ssh_transp.open_session()
#chan.setblocking(0)
#chan.exec_command('sudo python /home/pi/Desktop/TPM/TEST3.py')
#retcode = chan.recv_exit_status()
#ssh_transp.close()
#print("Client finished with exit code: %s" % str(retcode))
# Reading from output streams
#while chan.recv_ready():
#    outdata += str(chan.recv(1000))
#while chan.recv_stderr_ready():
#    errdata += str(chan.recv_stderr(1000))
#if chan.exit_status_ready():  # If completed
#    break

#ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo python3 /home/pi/Desktop/TPM/TEST3.py')
#ssh.close()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.connect((raspi_ip, port))
client_socket.setblocking(False)

try:
    while 1:
        data = input("Enter Data :")
        client_socket.send(data.encode())
        print("Sending request")

        ready = select.select([client_socket], [], [], 3)
        if ready[0]:
            msgReceived = client_socket.recv(1024)
            print("At client: %s" % str(msgReceived.decode()))
            if msgReceived.decode() == 'shutdown':
                client_socket.close()
                quit()


except Exception as ex:
    print(ex)
