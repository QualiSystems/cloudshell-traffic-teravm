

del "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Controller.zip" /F
del "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Management Assistant.zip" /F
del "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Test Module.zip" /F
del "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\Deploy TeraVM Instance.zip" /F

"C:\Program Files\7-Zip\7z.exe" a -r "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Controller.zip" -w C:\work\git\cloudshell-traffic-teravm\drivers\controller\src\*.* -mem=AES256
"C:\Program Files\7-Zip\7z.exe" a -r "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\Deploy TeraVM Instance.zip" -w C:\work\git\cloudshell-traffic-teravm\drivers\deployment_drivers\teravm_instance\*.* -mem=AES256
"C:\Program Files\7-Zip\7z.exe" a -r "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Management Assistant.zip" -w C:\work\git\cloudshell-traffic-teravm\drivers\teravm_management_assistant\src\*.* -mem=AES256
"C:\Program Files\7-Zip\7z.exe" a -r "C:\work\git\cloudshell-traffic-teravm\cloudshell_traffic_teravm_Package\Resource Drivers - Python\TeraVM Test Module.zip" -w C:\work\git\cloudshell-traffic-teravm\drivers\test_module\src\*.* -mem=AES256
