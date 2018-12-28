#! /usr/bin/env python3

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
    
def P_Unknown (elt):
    print ("Unknown element: <" + elt.tag + ">")

def Tree_Parse (elt, tree_dict):
    for e in elt.getchildren():
        if tree_dict.get(e.tag):
            tree_dict.get(e.tag)(e)
        else:
            P_Unknown (e)
    
def P_Institution_Name (elt):
    print ("Parsing Institution Name")

def P_Comments (elt):
    print ("Parsing Comments")

def P_Number_of_Days (elt):
    print ("Parsing Number of days")

def P_Day (elt):
    r_dict ['days'].add(getName (elt))
    print ("Parsing Day")
    
def P_Days_List (elt):
    r_dict['days'] = set()
    Tree_Parse (elt, {'Number_of_Days' : P_Number_of_Days, 'Day' : P_Day})
    print ("Parsing day list")

def P_Number_of_Hours (elt):
    print ("Parsing Number of hours")

def P_Hour (elt):
    r_dict ['hours'].add(getName (elt))
    print ("Parsing Hour")
    
def P_Hours_List (elt):
    r_dict['hours'] = set()
    Tree_Parse (elt, {'Number_of_Hours' : P_Number_of_Hours, 'Hour' : P_Hour})
    print ("Parsing hour list")

def P_Subject (elt):
    r_dict ['subjects'].add(getName (elt))
    print ("Parsing Subject")

def P_Subjects_List (elt):
    r_dict['subjects'] = set ()
    Tree_Parse (elt, {'Subject' : P_Subject})
    print ("Parsing Subject list")

def P_Activity_Tag (elt):
    r_dict ['activity_tags'].add(getName (elt))
    print ("Parsing Activity Tag")
    
def P_Activity_Tags_List (elt):
    r_dict['activity_tags'] = set ()
    Tree_Parse (elt, {'Activity_Tag' : P_Activity_Tag})
    print ("Parsing Activity Tags list")

def P_Teacher (elt):
    t_dict = {'activities' : []}
    r_dict ['teachers'][getName (elt)] = t_dict
    print ("Parsing Teachers")
    
def P_Teachers_List (elt):
    r_dict['teachers'] = {}
    Tree_Parse (elt, {'Teacher' : P_Teacher})
    print ("Parsing Teachers list")

stud_stack = []

def P_Subgroup (elt):
    g_name = stud_stack[-1]
    r_dict ['subgroups'][getName(elt)] = {'group' : g_name, 'activities' : []}
    print ("Parsing Subgroup")

def P_Group (elt):
    y_name = stud_stack [-1]
    r_dict ['groups'][getName (elt)] = {'year' : y_name, 'activities' : []}
    stud_stack.append (getName (elt))
    Tree_Parse (elt, {'Subgroup' : P_Subgroup})
    stud_stack.pop ()
    print ("Parsing Group")
    
def P_Year (elt):
    r_dict['years'][getName (elt)] = {'activities' : []}
    stud_stack.append (getName (elt))
    Tree_Parse (elt, {'Group' : P_Group})
    stud_stack.pop()
    print ("Parsing Year")
    
def P_Students_List (elt):
    r_dict['years']     = {}
    r_dict['groups']    = {}
    r_dict['subgroups'] = {}
    Tree_Parse (elt, {'Year' : P_Year})
    print ("Parsing Students list")

def InsertActivity (id, x):
    if x in r_dict ['teachers']:
        # This is a teacher
        r_dict ['teachers'][x]['activities'].append (id)
    elif x in r_dict ['years']:
        # This is a year
        r_dict ['years'][x]['activities'].append (id)
    elif x in r_dict ['groups']:
        # This is a group
        r_dict ['groups'][x]['activities'].append (id)
    elif x in r_dict ['subgroups']:
        # This is a subgroup
        r_dict ['subgroups'][x]['activities'].append (id)
    else:
        raise Exception ('InsertActivity', x)
    
def P_Activity (elt):
    a_dict = {
        'Subject'  : getProperty (elt, 'Subject').text,
        'teachers' : [x.text for x in getPropertyList (elt, 'Teacher')],
        'tags'     : [x.text for x in getPropertyList (elt, 'ActivityTags')],
        'students' : [x.text for x in getPropertyList (elt, 'Students')],
        'duration' : getProperty (elt, 'Duration').text
    }

    id = getPropertyText (elt, 'Id')
    r_dict['activities'][id] = a_dict
    
    for t in a_dict ['teachers']:
        InsertActivity (id, t)

    for s in a_dict ['students']:
        InsertActivity (id, s)

    print ("Parsing Activity")
    
def P_Activities_List (elt):
    r_dict['activities'] = {}
    Tree_Parse (elt, {'Activity' : P_Activity})
    print ("Parsing Activities list")

def P_Building (elt):
    r_dict ['buildings'][getName (elt)] = set()
    print ("Parsing Building")
    
def P_Buildings_List (elt):
    r_dict['buildings'] = {}
    Tree_Parse (elt, {'Building' : P_Building})
    print ("Parsing Buildings list")

def P_Room (elt):
    r_dict['buildings'][getPropertyText (elt, 'Building')].add (getName (elt))
    print ("Parsing Room")
    
def P_Rooms_List (elt):
    Tree_Parse (elt, {'Room' : P_Room})
    print ("Parsing Rooms list")

def P_Time_Constraints_List (elt):
    print ("Parsing Time Constraints list")

def P_Space_Constraints_List (elt):
    print ("Parsing Space Constraints list")

xml = et.parse("2018-2019_Sem-2_ENIS_DGIMA_data_and_timetable.fet")

root = xml.getroot()

root_tree = {
    'Institution_Name' : P_Institution_Name,
    'Comments' : P_Comments,
    'Days_List' : P_Days_List,
    'Hours_List' : P_Hours_List,
    'Subjects_List' : P_Subjects_List,
    'Activity_Tags_List' : P_Activity_Tags_List,
    'Teachers_List' : P_Teachers_List,
    'Students_List' : P_Students_List,
    'Activities_List' : P_Activities_List,
    'Buildings_List' : P_Buildings_List,
    'Rooms_List' : P_Rooms_List,
    'Time_Constraints_List' : P_Time_Constraints_List,
    'Space_Constraints_List' : P_Space_Constraints_List
}

Tree_Parse (root, root_tree)
print (r_dict)
