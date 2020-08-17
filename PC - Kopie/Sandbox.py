import os
import paramiko

raspi_ip = '192.168.178.84'
username = 'root'
password = 'TPM'

ssh = paramiko.SSHClient()
paramiko.util.log_to_file('test.txt')
# In case the server's key is unknown,
# we will be adding it automatically to the list of known hosts
ssh.load_host_keys(os.path.join(os.path.dirname(__file__), 'known_hosts'))
# Loads the user's local known host file.
ssh.connect(raspi_ip, username=username, password=password)
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('ls /tmp')
print("output", ssh_stdout.read()) # Reading output of the executed command
error = ssh_stderr.read() # Reading the error stream of the executed command
print("err", error, len(error))
ssh.close()