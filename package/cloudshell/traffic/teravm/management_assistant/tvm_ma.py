from debug_utils import debugger


class TeraVMManagementAssistantHandler:
    def __init__(self):
        pass

    def deploy_tvm(self, context, request):
        debugger.attach_debugger()
        return 'lolz'
