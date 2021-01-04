#!/usr/bin/python
# -*- coding: UTF-8 -*-# enable debugging

import requests, os
import xml.etree.ElementTree as xml
import datetime
import pytz
import json

username = "sample_user"
password = "sample_pass"
snc_url = "servicenow URL"

date_list = []
apikey = ""

jobid = "RUNDECK JOBID HERE"

# Define the SN query
def sn_query(query):
    # Simple SN query
    query_url = snc_url+query
    response = requests.get(query_url, auth=(username, password)).text
    #Uncomment below to see what other variables can be parsed from the SN call
    #print response
    root = xml.fromstring(response)
    return root

# gets sn tickets with start and end dates for CHG.
# Format is list of [Dict[CHG]:start datetime object].
def get_sn_ticket():
    # This grabs the approved tickets from SN, then pulls out: patch, ticket, and start info
    data = []
    dates = {}
    patch_groups = {}
    sn_tickets_xml = sn_query("change_request.do?XML&sysparm_query=active=true^state!=6^short_descriptionLIKERedhat/CentOS OS Patching^approval=approved^short_descriptionNOT LIKEP_INFRA^start_date>javascript:gs.endOfToday()")
    for tag in sn_tickets_xml:
        ticket_number = tag.find("number").text
        start_date = tag.find("start_date").text
        patch_group = tag.find("cmdb_ci").text
        try:
            datetime_object = datetime.datetime.strptime( start_date, '%Y-%m-%d  %H:%M:%S')
        except:
            datetime_object = None
        patch_groups[ticket_number] = patch_group
        dates[ticket_number] = datetime_object
    return dates, patch_groups

def get_sn_patchgroup(sys_id):
    # This turns the sys_id object for the CHG group name into a human readable name
    sn_cmdb_object = sn_query("cmdb_ci_group.do?XML&sysparm_query=sys_id=" + sys_id)
    for tag in sn_cmdb_object:
        name = tag.find("name").text
    return name

def ticket_within_week (date):
    # Ensures the CHG is within a week and not before today
    today = datetime.datetime.today()
    nextweek = today + datetime.timedelta(days=7)
    try:
        if nextweek > date:
            if date > today:
                return True
            else:
                return False
        else:
            return False
    except:
        return False

def rundeck_post (apikey, json_data, job_id):
    for k,v in json_data.items():
        #This block will add 10 minutes to a start time conflict and convert the datetime object to string
        if k == "runAtTime" and v in date_list:
            time = v + datetime.timedelta(minutes=10)
            if time in date_list:
                time = time + datetime.timedelta(minutes=10)
            date_list.append(time)
            str_date = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            json_data[k] = str_date
        elif k == "runAtTime":
            str_date = v.strftime("%Y-%m-%dT%H:%M:%S%z")
            json_data[k] = str_date
    # make dict we've been working with a json package, mostly updates the single quotes to double quotes
    json_data_package = json.dumps(json_data)
    url = 'https://rundeck.samplecompany.com/api/21/job/' + job_id + '/run'
    headers = {"Accept": "application/json", "Content-type": "application/json","X-Rundeck-Auth-Token": apikey}
    # send request
    print json_data_package
    r = requests.post(url, json_data_package, headers=headers)
    print r.content

def rundeck_json_build (date, chg, duration = 1, waittorecover= "20m"):
    # Build json package
    patchgroup = get_sn_patchgroup(patchgroups[chg])
    json_data = {"runAtTime": date, "options": {"LinuxPatchTicket": chg, "Duration": duration, "PatchGroup": patchgroup, "WaitToRecoverTime" : waittorecover}}
    return json_data


if __name__ == "__main__":
    dates, patchgroups = get_sn_ticket()
    for key in dates:
        value = ticket_within_week(dates[key])
        if value == True:
            start_date = dates[key]
            # Add timezone info for api call
            timezone = pytz.timezone("UTC")
            d_aware = timezone.localize(start_date)
            # build json package, can use some variables to change things depending on CHG group name
            if "P_MD" in get_sn_patchgroup(patchgroups[key]):
                json_data = rundeck_json_build(d_aware, key, waittorecover="45m")
            else:
                json_data = rundeck_json_build(d_aware, key)
            # Send job to rundeck
            rundeck_post(apikey,json_data, jobid)
            # this step tracks what time a job has been sent to rundeck for to prevent overlap
            date_list.append(d_aware)
