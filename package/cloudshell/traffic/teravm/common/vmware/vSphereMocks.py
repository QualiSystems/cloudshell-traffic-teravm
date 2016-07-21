import pyVmomi
import mock
from pyVmomi import vim
from mock import Mock, MagicMock,create_autospec
import pyVim
import datetime

def get_success_task():
    task = Mock()
    task.info = Mock()
    task.info.state = vim.TaskInfo.State.success
    return task    

def get_error_task(message):
    task = Mock()
    task.info = Mock()
    task.info.state = vim.TaskInfo.State.error
    task.info.error.msg = message
    return task   

def set_search(self, host_name, side_effect=None):
    host = None
    if(host_name != None):
        host = create_autospec(vim.HostSystem)
        host.config = create_autospec(vim.host.ConfigInfo)
        host.name = host_name

    searchIndex = self.session.content.searchIndex
    searchIndex.FindByDnsName = Mock(return_value=host)
    if side_effect != None:
        searchIndex.FindByDnsName.side_effect = side_effect

    return host

def set_start_program_in_guest(self):
    self.session.content.guestOperationsManager = Mock()
    self.session.content.guestOperationsManager.processManager = Mock()
    self.session.content.guestOperationsManager.processManager.StartProgramInGuest = Mock(return_value = 20)

def set_list_processes_success(self):
    proc_info = create_autospec(vim.vm.guest.ProcessManager.ProcessInfo)
    proc_info.endTime = datetime.datetime.now() 
    proc_info.exitCode = 0
    self.session.content.guestOperationsManager.processManager.ListProcesses = Mock(return_value = [proc_info])
        
def set_list_processes_fail(self, err_code = 1):
    proc_info = create_autospec(vim.vm.guest.ProcessManager.ProcessInfo)
    proc_info.endTime = datetime.datetime.now() 
    proc_info.exitCode = 1
    self.session.content.guestOperationsManager.processManager.ListProcesses = Mock(return_value = [proc_info])
        
