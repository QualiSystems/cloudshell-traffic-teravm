from cloudshell.traffic.teravm.common import i18n as c


def get_vsphere_credentials(api, resource):
        vcenter_name = resource.VmDetails.CloudProviderFullName
        vcenter = api.GetResourceDetails(vcenter_name)
        vcenter_address = vcenter.Address
        vcenter_attr = {attribute.Name: attribute.Value for attribute in vcenter.ResourceAttributes}
        vsphere_user = vcenter_attr[c.ATTRIBUTE_NAME_USER]
        vsphere_password = api.DecryptPassword(vcenter_attr[c.ATTRIBUTE_NAME_PASSWORD]).Value
        return vcenter_address, vsphere_password, vsphere_user