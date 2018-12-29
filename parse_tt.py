#! /usr/bin/env python3
# $Id$

from xml.etree import ElementTree as et

r_dict = {}

def printInfos (elt):
    print ("Tag: <" + elt.tag + ">")
    print ("Text: <" + elt.text + ">")
    print ("Attribs:")
    print (elt.attrib)
    print ("Keys :")
    print (elt.keys ())
    print ("Children:")
    print (elt.getchildren ())

def getProperty (elt, prop):
    return elt.find(prop)

def getPropertyList (elt, prop):
    return elt.findall(prop)
    
def getPropertyText (elt, prop):
    return elt.find(prop).text

def getName (elt):
    return getPropertyText (elt, 'Name')

def active (elt):
    return getPropertyText (elt, 'Active') == 'true'

def permanentlyLocked (elt):
    return getPropertyText (elt, 'Permanently_Locked') == 'true'

def emptyDay ():
    return {h : set() for h in r_dict ['hours']}

def emptyWeek ():
    return {d : emptyDay() for d in r_dict ['days']}
    
def P_Unknown (elt):
    pass
    #print ("Unknown element: <" + elt.tag + ">")

def Tree_Parse (elt, tree_dict):
    for e in elt.getchildren():
        if tree_dict.get(e.tag):
            tree_dict.get(e.tag)(e)
        else:
            P_Unknown (e)
    
def P_Institution_Name (elt):
    print ("Parsing Institution Name: <" + elt.text + ">")

def P_Comments (elt):
    print ("Parsing Comments: <" + elt.text + ">")

def P_Day (elt):
    r_dict ['days'].add(getName (elt))
    
def P_Days_List (elt):
    r_dict['days'] = set()
    Tree_Parse (elt, {'Day' : P_Day})

def P_Hour (elt):
    r_dict ['hours'].add(getName (elt))
    
def P_Hours_List (elt):
    r_dict['hours'] = set()
    Tree_Parse (elt, {'Hour' : P_Hour})

def P_Subject (elt):
    r_dict ['subjects'].add(getName (elt))

def P_Subjects_List (elt):
    r_dict['subjects'] = set ()
    Tree_Parse (elt, {'Subject' : P_Subject})

def P_Activity_Tag (elt):
    r_dict ['activity_tags'].add(getName (elt))
    
def P_Activity_Tags_List (elt):
    r_dict['activity_tags'] = set ()
    Tree_Parse (elt, {'Activity_Tag' : P_Activity_Tag})

def P_Teacher (elt):
    t_dict = {'activities' : [], 'timetable' : emptyWeek()}
    r_dict ['teachers'][getName (elt)] = t_dict
    
def P_Teachers_List (elt):
    r_dict['teachers'] = {}
    Tree_Parse (elt, {'Teacher' : P_Teacher})

stud_stack = []

def P_Subgroup (elt):
    g_name = stud_stack[-1]
    r_dict ['groups'][g_name]['sgroups'].add (getName(elt))
    r_dict ['sgroups'][getName(elt)] = {
        'group'      : g_name,
        'activities' : [],
        'timetable'  : emptyWeek()
    }

def P_Group (elt):
    y_name = stud_stack [-1]
    r_dict ['years'][y_name]['groups'].add (getName(elt))
    r_dict ['groups'][getName (elt)] = {
        'year'       : y_name,
        'activities' : [],
        'sgroups'    : set()
    }
    stud_stack.append (getName (elt))
    Tree_Parse (elt, {'Subgroup' : P_Subgroup})
    stud_stack.pop ()
    
def P_Year (elt):
    r_dict['years'][getName (elt)] = {
        'activities' : [],
        'groups'     : set()
    }
    stud_stack.append (getName (elt))
    Tree_Parse (elt, {'Group' : P_Group})
    stud_stack.pop()
    
def P_Students_List (elt):
    r_dict['years']   = {}
    r_dict['groups']  = {}
    r_dict['sgroups'] = {}
    Tree_Parse (elt, {'Year' : P_Year})

def InsertActivity (a_id, x):
    if x in r_dict ['teachers']:
        r_dict ['teachers'][x]['activities'].append (a_id)
    elif x in r_dict ['years']:
        r_dict ['years'][x]['activities'].append (a_id)
    elif x in r_dict ['groups']:
        r_dict ['groups'][x]['activities'].append (a_id)
    elif x in r_dict ['sgroups']:
        r_dict ['sgroups'][x]['activities'].append (a_id)
    else:
        raise Exception ('InsertActivity', x)
    
def P_Activity (elt):
    a_dict = {
        'Subject'  : getProperty (elt, 'Subject').text,
        'teachers' : [x.text for x in getPropertyList (elt, 'Teacher')],
        'tags'     : [x.text for x in getPropertyList (elt, 'ActivityTags')],
        'students' : [x.text for x in getPropertyList (elt, 'Students')],
        'duration' : int (getProperty (elt, 'Duration').text),
        'day'      : None,
        'hour'     : None,
        'room'     : None,
    }
    a_id = getPropertyText (elt, 'Id')
    r_dict['activities'][a_id] = a_dict
    for t in a_dict ['teachers']:
        InsertActivity (a_id, t)
    for s in a_dict ['students']:
        InsertActivity (a_id, s)
    
def P_Activities_List (elt):
    r_dict['activities'] = {}
    Tree_Parse (elt, {'Activity' : P_Activity})

def P_Building (elt):
    r_dict ['buildings'][getName (elt)] = {'rooms' : set()}
    
def P_Buildings_List (elt):
    r_dict['buildings'] = {}
    Tree_Parse (elt, {'Building' : P_Building})

def P_Room (elt):
    r_name = getName (elt)
    b_name = getPropertyText (elt, 'Building')
    r_dict['rooms'][r_name] = {
        'timetable' : emptyWeek(),
        'building'  : b_name
    }
    r_dict['buildings'][b_name]['rooms'].add (r_name)
    
def P_Rooms_List (elt):
    r_dict ['rooms'] = {}
    Tree_Parse (elt, {'Room' : P_Room})

def P_ConstraintActivityPreferredStartingTime (elt):
    if active (elt):
        a_id = getPropertyText (elt, 'Activity_Id')
        day = getPropertyText (elt, 'Preferred_Day')
        hour = getPropertyText (elt, 'Preferred_Hour')

        r_dict ['activities'][a_id]['day'] = day
        r_dict ['activities'][a_id]['hour'] = hour

        for t in r_dict ['activities'][a_id]['teachers']:
            r_dict['teachers'][t]['timetable'][day][hour].add(a_id)

        for s in r_dict ['activities'][a_id]['students']:
            if s in r_dict ['sgroups']:
                # Apply the activity only to the subgroup
                r_dict['sgroups'][s]['timetable'][day][hour].add(a_id)
            elif s in r_dict ['groups']:
                # Apply the activity to all the group's subgroups
                for sg in r_dict ['groups'][s]['sgroups']:
                    r_dict['sgroups'][sg]['timetable'][day][hour].add(a_id)
            elif s in r_dict ['years']:
                #  Apply the activity to all the year's groups' subgroups
                for g in r_dict['years'][s]['groups']:
                    for sg in r_dict ['groups'][g]['sgroups']:
                        r_dict['sgroups'][sg]['timetable'][day][hour].add(a_id)
            else:
                raise Exception ('ConstraintActivityPreferredStartingTime', s)
    
def P_Time_Constraints_List (elt):
    Tree_Parse (elt, {'ConstraintActivityPreferredStartingTime' :
                      P_ConstraintActivityPreferredStartingTime})

def P_ConstraintActivityPreferredRoom (elt):
    # Take in account only constraints generated by Fet
    if active (elt):
        a_id = getPropertyText (elt, 'Activity_Id')
        room = getPropertyText (elt, 'Room')
        day = r_dict ['activities'][a_id]['day']
        hour = r_dict ['activities'][a_id]['hour']

        r_dict ['activities'][a_id]['room'] = room
        r_dict ['rooms'][room]['timetable'][day][hour].add(a_id)
    
def P_Space_Constraints_List (elt):
    Tree_Parse (elt, {'ConstraintActivityPreferredRoom' :
                      P_ConstraintActivityPreferredRoom})

xml = et.parse("2018-2019_Sem-2_ENIS_DGIMA_data_and_timetable.fet")

root = xml.getroot()

root_tree = {
    'Institution_Name'       : P_Institution_Name,
    'Comments'               : P_Comments,
    'Days_List'              : P_Days_List,
    'Hours_List'             : P_Hours_List,
    'Subjects_List'          : P_Subjects_List,
    'Activity_Tags_List'     : P_Activity_Tags_List,
    'Teachers_List'          : P_Teachers_List,
    'Students_List'          : P_Students_List,
    'Activities_List'        : P_Activities_List,
    'Buildings_List'         : P_Buildings_List,
    'Rooms_List'             : P_Rooms_List,
    'Time_Constraints_List'  : P_Time_Constraints_List,
    'Space_Constraints_List' : P_Space_Constraints_List
}

Tree_Parse (root, root_tree)
print (r_dict['rooms']['8103']['timetable']['Lundi'])
print (r_dict['teachers']['Bechir ZALILA']['timetable']['Lundi'])
print (r_dict['sgroups']['GI1-S1-G1']['timetable']['Lundi'])