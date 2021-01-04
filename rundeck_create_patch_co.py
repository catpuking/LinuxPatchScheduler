#!/usr/bin/python
# -*- coding: utf-8 -*-

import   requests, lxml, xmlrpclib, datetime, sys, os
import xml.etree.ElementTree as xml
from SOAPpy import SOAPProxy
import PatchSchedule


#SNC Creds
instance='sample_company'
username='sample_user'
password='sample_pass'


snc_url = "https://sample_company.service-now.com/"
proxy = 'https://%s:%s@%s.service-now.com/change_request.do?SOAP' % (username, password, instance)
#SPW Creds
satellite_url = "http://spacewalk.sample_company.com/rpc/api"
satellite_login = "sample_user"
satellite_password = "sample_pass"
#Report file location
run_date = datetime.datetime.now().strftime('%b-%G')
report_file = "/mnt/LinuxPatchReports/Linux_Patch_Report-%s.xlsx" % run_date
report_file_location = "U:\\Systems\\Linux Patch Reports\\Linux_Patch_Report-%s.xlsx" % run_date

# SNC search query
def sn_query(query):
    instance
    query_url = snc_url + "/" +query
    response = requests.get(query_url, auth=(username, password)).content
    root = xml.fromstring(response)
    return root

# Get patch group info from service-now
missing_cmdb_ci = []
def get_patch_group_info(patch_group):
    cmdb_patch_group = sn_query("cmdb_ci_group.do?XML&sysparm_query=name=%s" % patch_group)
    if len(cmdb_patch_group) != 1:
        missing_cmdb_ci.append(patch_group)
        patch_group_name = patch_group
        description = "Patch Group Does Not Exist in CMDB"
    else:
        for tag in cmdb_patch_group:
            patch_group_name = tag.find("name").text
            description = tag.find("short_description").text
    return patch_group_name, description

# Get hosts from spacewalk and assign them to patch groups
def get_hosts_from_spacewalk():
    patch_groups = {}
    patch_group_not_set = []
    client = xmlrpclib.Server(satellite_url, verbose=0)
    key = client.auth.login(satellite_login, satellite_password)
    list = client.system.list_systems(key)
    for system in list:
        system_id = system['id']
        system_name = system['name']
        custom_values = client.system.getCustomValues(key, system_id)
        try:
            patch_group = custom_values['patchCO']
            if not patch_group in patch_groups:
                patch_groups[patch_group] = []
                patch_groups[patch_group].append(system_name)
            else:
                patch_groups[patch_group].append(system_name)
        except Exception as error:
            patch_group = "Patch Group Not Set"
            patch_group_not_set.append(system_name)

    client.auth.logout(key)
    return patch_groups, patch_group_not_set

def create_change_sys_not_incl(patch_group_not_set):

    server = SOAPProxy(proxy, snc_url)
    cmdb_ci = "MISC_Patch_Group"
    assignment_group = 'Unix Admins'
    u_service_impacting = 'No'
    patch_group_not_set = '\n'.join(patch_group_not_set)
    type = 'Routine'
    risk = 4 #Medium risk change - Low(4) risk change will not allow CHG start button.
    u_reason_for_change = 'Update Spacewalk Fields to Include Patch Info'
    co_description = ("The following servers do not have the patch field set in spacewalk.\n\n"
                    "AFFECTED SERVERS:\n\n"
                    "%s") % (patch_group_not_set)
    short_description = "Update Patch Field in Spacewalk"
    u_change_class = "Production Environment - Change"

    response = server.insert(
                            u_service_impacting = u_service_impacting,
                            cmdb_ci = cmdb_ci,
                            type = type,
                            assignment_group = assignment_group,
                            description = co_description,
                            risk = risk,
                            short_description = short_description,
                            u_change_class = u_change_class,
                            )

    return response['number']

def create_change(description, hosts, report_file_location, patch_group_name):

    server = SOAPProxy(proxy, snc_url)

    host_list = '\n'.join(hosts)

    assignment_group = 'Unix Admins'
    u_service_impacting = 'Yes'
    cmdb_ci = patch_group_name
    #check
    if "MD" in cmdb_ci:
        u_itil_watch_list = 'catpuking'
    else:
        u_itil_watch_list = ''
    type = 'Normal'
    risk = 4 #Low(4) risk change will not allow CHG start button.
    u_reason_for_change = 'Security and recommended OS updates.'
    try:
        start_date = PatchSchedule.next_start(patch_group_name)
        end_date = PatchSchedule.next_end(patch_group_name)
    except:
        start_date = None
        end_date = None
    if "P_" in cmdb_ci:
        co_description = ("%s\n\n"
                    "\n\n"
                    "IMPACT: A reboot is required after patches have been installed\n\n"
                    "LIST OF PATCHES: %s\n\n"
                    "AFFECTED SERVERS:\n\n"
                    "%s") % (description, report_file_location, host_list)
    else:
        co_description = ("%s\n\n"
                    "- QA patching tickets should only be closed after they are in the -Completed - Ready to verify- status.\n"
                    "- All INC related to QA patching should be spawned from the QA Patching ticket. \n"
                    "- All INC tickets from patching need to have listed in the description the PROD servers that they are QA for. \n"
                    "- INC Resolved status should include information on both the QA and PROD servers. \n"
                    "\n\n"
                    "IMPACT: A reboot is required after patches have been installed\n\n"
                    "LIST OF PATCHES: %s\n\n"
                    "AFFECTED SERVERS:\n\n"
                    "%s") % (description, report_file_location, host_list)

    short_description = "%s: RedHat/CentOS OS Patching - %s" % (patch_group_name, description)
    change_plan = ("1. Run chef-client -o systems-role to patch system config changes.\n"
                            "2. Stage patches on the server and install patches\n"
                            "3. Reboot Server if Yum indicates a reboot is necessary to update packages")
    backout_plan = "Use yum history to roll RPM's back to the pre-patching rpm versions."
    test_plan = "QA servers are already done first."
    if patch_group_name.startswith("Q"):
        u_change_class = "Test Enviroment - Change"
    else:
        u_change_class = "Production Environment - Change"

    response = server.insert(
                            u_service_impacting = u_service_impacting,
                            cmdb_ci = cmdb_ci,
                            type = type,
                            assignment_group = assignment_group,
                            description = co_description,
                            risk = risk,
                            short_description = short_description,
                            u_reason_for_change = u_reason_for_change,
                            u_change_class = u_change_class,
                            change_plan = change_plan,
                            backout_plan = backout_plan,
                            u_itil_watch_list = u_itil_watch_list,
                            test_plan = test_plan,
                            end_date = end_date,
                            start_date = start_date
                            )

    #return response['number']
    print "%s => %s (%s)" % (response['number'], patch_group_name, description)

if __name__ == "__main__":

    #if the report file was not generated by rundeck_create_patch_list_by_host.py, exit the script
    if not os.path.exists(report_file):
        sys.exit("Report file %s does not appear to exist. Exiting ..." % report_file)
    patch_groups, patch_group_not_set = get_hosts_from_spacewalk()

    #Create tickets
    for patch_group, hosts in patch_groups.items():
        patch_group_name, description = get_patch_group_info(patch_group)
        if description != "Patch Group Does Not Exist in CMDB" and patch_group_name != "EXP":
            create_change(description, hosts, report_file_location, patch_group_name)

    if patch_group_not_set:
        create_change_sys_not_incl(patch_group_not_set)
    # patch_group_not_set missing_cmdb_ci
if patch_group_not_set:
    print "\n\n------------------------------------------------------------------------------------------------------------------"
    print "The hosts in the list below do not have the patch group set (the patchCO key) in Spacewalk."
    print "Set the patch group for each host in Spacewalk: $HOST -> Custom Info -> create new value -> Update the patchCO key\n"
    print "\n".join(patch_group_not_set)
    print "\n------------------------------------------------------------------------------------------------------------------"
if missing_cmdb_ci:
    print "\n\n------------------------------------------------------------------------------------------------------------------"
    print "The patch groups in the list below do not exist in Service-Now."
    print "Verify that the group names are correct. If a group is new, create it in Service-Now first."
    print "If you need to create/update a group in SNC, go to this url https://central1.service-now.com/cmdb_ci_group_list.do\n"
    for group in missing_cmdb_ci:
        for host in patch_groups[group]:
            print "%s => %s" % (group, host)
    print "\n------------------------------------------------------------------------------------------------------------------"
