#! /usr/bin/python


from ical_dict import iCalDict
from datetime import datetime
from datetime import timedelta

mapping = {
    "DTSTART;TZID=America/Los_Angeles": "dt_start",
    "DTEND;TZID=America/Los_Angeles": "dt_end",
    "SUMMARY": "summary",
}

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))


def clean_up_ics(file, mapping):
    ''' Takes an ICS file and strips out everything but the summary, start and end times
    outputing a dictionary that places the key value pairs within their patching cycle'''

    # Create a blank dictionary
    patching_cycle_dict = {}

    # Use IcalDict to convert ics file to dict object
    patching_dict = iCalDict(file, mapping).convert()
    #print patching_dict
    # function to replace string date with datetime type
    str_to_dt = lambda x : datetime.strptime(i[x], "%Y%m%dT%H%M%S")
    list_str_to_dt =['dt_start', 'dt_end']

    # Create list of dictionary elements we don't need so they can be purged in the next loop
    data_to_remove = [key for key, value in patching_dict['data'][0].items() if key != "dt_end" if key != "dt_start" if
                      key != "summary"]

    # loop through the newly created dict and change type to datetime for some values
    # and remove unneccesary key/value pairs
    for i in patching_dict['data']:
        for y in list_str_to_dt:
            i[y] = str_to_dt(y)
        map(lambda x: i.pop(x, None), data_to_remove)

    # If the summary is labeled Cycle then populate a seperate dictionary patching_cycle_dict
        if "Cycle" in i['summary']:
            patching_cycle_dict[i['summary']] = i

    # append all the patching dates to the patching_cycle_dict
    # The output will allow you to call the dict with the key of a certain cycle
    # and have the list of all the patches that are contained in that cycle
    for key in patching_cycle_dict:
        for y in patching_dict['data']:
            try:
                if patching_cycle_dict["Cycle 1 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 2 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 1 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 2 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 3 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 2 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 3 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 4 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 3 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 4 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 5 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 4 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 5 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 6 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 5 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 6 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 7 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 6 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 7 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 8 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 7 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 8 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 9 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 8 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 9 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 10 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 9 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 10 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 11 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 10 Start"][y['summary']] = y
            except:
                pass
            try:
                if patching_cycle_dict["Cycle 11 Start"]['dt_start'] < y['dt_start'] < patching_cycle_dict["Cycle 12 Start"]['dt_start']:
                    patching_cycle_dict["Cycle 11 Start"][y['summary']] = y
            except:
                pass
            try:
                 if patching_cycle_dict["Cycle 12 Start"]['dt_start'] < y['dt_start'] < datetime(2045, 1, 1, 1, 0) :
                    patching_cycle_dict["Cycle 12 Start"][y['summary']] = y
            except:
                pass
    return patching_cycle_dict

def what_cycle_is_next(patch_schedule):
    cycle_date_list = []
    for key, value in patch_schedule.iteritems() :
        if patch_schedule[key]['dt_start'] > (datetime.now() - timedelta(days=7)):
            cycle_date_list.append(patch_schedule[key]['dt_start'])
    closest_date = nearest(cycle_date_list, datetime.now())
    for i in patch_schedule:
        if patch_schedule[i]['dt_start'] == closest_date:
            return i


def next_end (patchGroup):
    #time = patch_schedule[next_cycle][patchGroup]['dt_end'] - timedelta(hours=8)
    time = patch_schedule[next_cycle][patchGroup]['dt_end']
    return datetime.strftime(time,"%Y-%m-%d %H:%M:%S")
def next_start (patchGroup):
    #time = patch_schedule[next_cycle][patchGroup]['dt_start'] - timedelta(hours=8)
    time = patch_schedule[next_cycle][patchGroup]['dt_start']
    return datetime.strftime(time,"%Y-%m-%d %H:%M:%S")

# Run these when called from other scripts so useful data is available.
# Use this site to generate new ICS files: https://ical.marudot.com/
patch_schedule = clean_up_ics('LinuxPatching2021.ics', mapping)
next_cycle = what_cycle_is_next(patch_schedule)

if __name__ == "__main__":
    #print next_cycle
    #print patch_schedule
    #print datetime.strftime(patch_schedule[next_cycle]['Q_MD']['dt_start'],"%Y-%m-%d %H:%M:%S")
    print next_start("Q_MD")
	  #what_cycle_is_next(patch_schedule)
