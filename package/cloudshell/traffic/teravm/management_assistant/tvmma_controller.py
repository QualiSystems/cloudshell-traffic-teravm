from socket import error
import paramiko
from paramiko import BadHostKeyException, AuthenticationException, SSHException
import re


class TVMManagerController:
    def __init__(self, host):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(host, 22, 'vi-admin', 'TeraVM', timeout=60)
        except (BadHostKeyException, AuthenticationException, SSHException, EOFError, error) as e:
            raise Exception('Could not connect to host: ' + host)

    def get_configuration(self, file):
        sftp = self.ssh_client.open_sftp()
        configuration = {}
        with sftp.open(file) as f:
            for line in f:
                if not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    configuration[k] = v.replace('\n', '')
        if sftp:
            sftp.close()

        return configuration

    def set_configuration(self, configuration, tvm_deployment_settings_file='/home/vi-admin/cloudshell_deployment.cfg'):
        sftp = self.ssh_client.open_sftp()
        content = '\n'.join(sorted('{0}="{1}"'.format(k, v) for k, v in configuration.items()))
        with sftp.open(tvm_deployment_settings_file, 'wb') as f:
            f.write(content)
        if sftp:
            sftp.close()

    def deploy(self, tvm_deployment_settings_file='/home/vi-admin/cloudshell_deployment.cfg'):
        command = './vmutil.bash Deploy --config ' + tvm_deployment_settings_file + ' --Force'
        output = self._run_command(command)
        return scrubbed(output)

    def dry_run(self, tvm_deployment_settings_file='/home/vi-admin/cloudshell_deployment.cfg'):
        command = './vmutil.bash Deploy --DryRun ' + tvm_deployment_settings_file
        return scrubbed(self._run_command(command))

    def _run_command(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exec_command_output = stdout.readlines()
        exec_command_error = stderr.readlines()
        return ''.join(exec_command_output + exec_command_error)


def scrubbed(output):
    """ cleans passwords from output
    :type output: str
    :rtype: str
    """
    temp = re.sub(pattern='--Password="(.*?)"', repl='--Password="***"', string=output)
    scrubbed_output = re.sub(pattern='(?:vi:\/\/).*(?:@)', repl='vi:\\***:***@', string=temp)
    return scrubbed_output

# if __name__ == "__main__":
#     host = '192.168.26.27'
#     request = ConfigurationBuilder()
#
#     tvm = TVMManager(host)
#     tvm.set_configuration(request.get())
#
#     result = tvm.dry_run()
#     print 'Dry run result \n' + '\n'.join(result)
#
#     result = tvm.deploy()
#     print 'Deploy result \n' + '\n'.join(result)
