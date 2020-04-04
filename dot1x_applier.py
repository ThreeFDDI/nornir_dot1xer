#!/usr/local/bin/python3
'''
This script is to apply dot1x config to Catalyst switch stacks
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks import text
from pprint import pprint as pp
from ttp import ttp


# Get info from switches
def get_info(task):

    # get software version; use TextFSM
    sh_version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    # save show version output to task.host
    task.host['sh_version'] = sh_version.result[0]
    # pull model from show version
    sw_model = task.host['sh_version']['hardware'][0].split("-")
    # save model to task.host
    task.host['sw_model'] = sw_model[1]

    # get interfaces; use TextFSM
    interfaces = task.run(
        task=netmiko_send_command,
        command_string="show interface switchport",
        use_textfsm=True,
    )

    # save interfaces to task.host
    task.host['intfs'] = interfaces.result
    

# render IBNS global configs
def ibns_global(version, vlan_list):
    _stuff = None


# render IBNS interface configs
def ibns_intf(version, intfs, vlans, uplinks, excluded_intfs):
    _stuff = None


# render switch configs
def render_configs(task):

    # print hostname and switch model
    print(task.host)
    print(task.host['sw_model'])

    # choose template based on switch model
    if "3750" in task.host['sw_model']:
        # 3750's use IBNSv1
        ibnsv1_dot1x(task)

    else:
        # all other switches use IBNSv2
        ibnsv2_dot1x(task)


# Apply IBNSv1 dot1x config template
def ibnsv1_dot1x(task):

    # init lists of interfaces
    access_interfaces = []
    uplink_interfaces = []

    # iterate over all interfaces 
    for intf in task.host['intfs']:

        # uplink interfaces
        if intf['interface'] in task.host['uplinks']:
            uplink_interfaces.append(intf)

        # other non-excluded access ports 
        elif intf['interface'] not in task.host['excluded_intf']:
            access_interfaces.append(intf)

    task.host['uplink_interfaces'] = uplink_interfaces

    uplink_intf_cfg = task.run(
        task=text.template_file, 
        template="IBNS_uplink_intf.j2", 
        path="templates/", 
        **task.host
    )
    
    task.host['access_interfaces'] = access_interfaces

    access_intf_cfg = task.run(
        task=text.template_file, 
        template="IBNSv1_access_intf.j2", 
        path="templates/", 
        **task.host
    )

    print(uplink_intf_cfg.result + access_intf_cfg.result)


# Main function
def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn to get info
    nr.run(task=get_info)
    # run The Norn to apply dot1x config
    nr.run(task=render_configs)


if __name__ == "__main__":
    main()
