
def populate_free_interfaces_by_test_element_name(interface_elements, available_ports):
    for interface in [x for x in interface_elements if not hasattr(x, 'flag_ignore')]:
        for port in list(available_ports):
            if interface.virtual_host_name == port.logical_name:
                interface.text = port.interface_id
                available_ports.remove(port)
                interface.flag_ignore = True
                break


def populate_free_interfaces_by_test_element_interface(interface_elements, available_ports):
    for interface in [x for x in interface_elements if not hasattr(x, 'flag_ignore')]:
        for port in list(available_ports):
            if interface.virtual_host_name == port.logical_name:
                interface.text = port.interface_id
                available_ports.remove(port)
                interface.flag_ignore = True
                break


def populate_free_interfaces_arbitrarily(interface_elements, available_ports):
    for interface in _get_unpopulated_interfaces(interface_elements):
        port = available_ports.pop()
        interface.text = port.interface_id
        interface.flag_ignore = True


def _get_unpopulated_interfaces(interface_elements):
    return [x for x in interface_elements if not hasattr(x, 'flag_ignore')]
