from pyVmomi import vim

 
def rename_object(self, object_name, new_object_name):
    root_folder = self.content.rootFolder
    entity_stack = root_folder.childEntity

    obj = None
    while entity_stack:
        entity = entity_stack.pop()
        if entity.name == object_name:
            obj = entity
            break
        elif isinstance(entity, vim.Datacenter):
            # add this vim.DataCenter's folders to our search
            # we don't know the entity's type so we have to scan
            # each potential folder...
            entity_stack.append(entity.datastoreFolder)
            entity_stack.append(entity.hostFolder)
            entity_stack.append(entity.networkFolder)
            entity_stack.append(entity.vmFolder)
        elif isinstance(entity, vim.Folder):
            # add all child entities from this folder to our search
            entity_stack.extend(entity.childEntity)

    if obj is None:
        self.logger.info("reanme failed: A object named %s could not be found" % object_name)
        return "A object named %s could not be found" % object_name
         
    # rename creates a task...
    task = obj.Rename(new_object_name)     
    state = task.info.state
    while task.info.state != vim.TaskInfo.State.success:
        if task.info.state == vim.TaskInfo.State.error:
            self.logger.info("reanme failed: object name:%s, %s" % (object_name,task.info.error.msg))
            return task.info.error.msg

    self.logger.info("object %s rename success" % object_name)
    message = new_object_name

    return message
