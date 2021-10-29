import paramiko
from scp import SCPClient, SCPException

class SSHManager:
    def __init__(self):
        self.ssh_client = None

    def create_ssh_client(self, hostname, username, password):
        if self.ssh_client is None:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(hostname, username=username, password=password)
        else:
            print('SSH client session exists.')
    
    def close_ssh_client(self):
        self.ssh_client.close()
    
    def send_file(self, local_path, remote_path):
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.put(local_path, remote_path, preserve_times=True)
        except SCPException:
            raise SCPException.message

    def send_directory(self, local_path, remote_path):
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.put(local_path, remote_path, preserve_times=True, recursive=True)
        except SCPException:
            raise SCPException.message
    
    def get_file(self, remote_path, local_path):
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(remote_path, local_path)
        except SCPException:
            raise SCPException.message
    
    def send_command(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command.strip())
        return stdout.readlines()

    def send_command2(self, command):
        self.ssh_client.exec_command(command.strip())
        return command

