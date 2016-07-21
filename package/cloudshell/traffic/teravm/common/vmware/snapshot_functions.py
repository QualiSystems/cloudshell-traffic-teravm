class SnapshotFunctions:
    def create_snapshot(self, typed_moref, snapshot_name, snapshot_description):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + typed_moref)
        vm._stub = si._stub

        desc = None
        if snapshot_description:
            desc = snapshot_description

        task = vm.CreateSnapshot_Task(name=snapshot_name,
                                      description=desc,
                                      memory=True,
                                      quiesce=False)


        print("Snapshot Completed.")

    def get_list_of_snapshots(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        vm = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if vm is None:
            raise SystemExit("Unable to find VirtualMachine " + typed_moref)
        vm._stub = si._stub
        snap_info = vm.snapshot
        list_of_snapshots = []
        list_of_snapshots.append(str(snap_info.rootSnapshotList[0].snapshot).strip("'"))
        childSnapshot = snap_info.rootSnapshotList[0]
        while(childSnapshot.childSnapshotList):
            list_of_snapshots.append(str(childSnapshot.childSnapshotList[0].snapshot).strip("'"))
            childSnapshot = childSnapshot.childSnapshotList[0]
        return list_of_snapshots

    def delete_snapshot(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        snapshot = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if snapshot is None:
            raise SystemExit("Unable to find Snapshot " + typed_moref)
        snapshot._stub = si._stub
        snapshot.RemoveSnapshot_Task(removeChildren=False)
        print("Snapshot " + typed_moref + " removed.")

    def restore_from_snapshot(self, typed_moref):
        si = self.si
        typed_moref_elems = typed_moref.split(':')
        snapshot = eval(typed_moref_elems[0])(typed_moref_elems[1])
        if snapshot is None:
            raise SystemExit("Unable to find Snapshot " + typed_moref)
        snapshot._stub = si._stub
        snapshot.RevertToSnapshot_Task()
        print("Restored vm to snapshot " + typed_moref)

