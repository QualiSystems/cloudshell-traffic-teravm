__author__ = 'ericr'
def find_target_ports(self, source, is_eligible_target_port=None, is_eligible_for_traversal=None):
    if is_eligible_target_port is None:
        is_eligible_target_port = lambda y: True
    if is_eligible_for_traversal is None:
        is_eligible_for_traversal = lambda y: True

    rv = []
    already = set()

    def f(x, is_direct):
        if x in already:
            return
        already.add(x)

        def g(fullpath):
            connport, connroot = self.get_resource_name_and_root(fullpath)

            if is_eligible_target_port(connport):
                rv.append((connport, is_direct))
            elif is_eligible_for_traversal(connroot):
                f(connroot, False)

        self.for_all_descendant_connectors(x, g)

    f(source, True)
    return rv

def filter_resources_by_root_predicate(self, resources, predicate):
    for r in list(resources):
        root = self.get_root_resource(r)
        if not predicate(root):
            resources.remove(r)

def filter_resources_by_availability(self, resid, resources):
    # rd = self.GetReservationDetails(resid).ReservationDescription
    for r in self.GetResourceAvailability(resources, showAllDomains=False).Resources:
        if r.ReservedStatus not in ['Shared', 'Not In Reservations'] or r.Excluded:
            resources.remove(r.FullName)
