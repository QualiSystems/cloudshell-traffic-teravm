class VmWareObjectNotFoundException(Exception):
    """custom exception for cases which objects are not found in vmware"""
    def __init__(self, object_name):
        message = "Cannot find object %s" %(object_name)
        super(VmWareObjectNotFoundException, self).__init__(message)
        self.object_name = object_name
        self.message = message


