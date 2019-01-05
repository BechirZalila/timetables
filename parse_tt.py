#! /usr/bin/env python3
# $Id$

import sys
import os
from xml.etree import ElementTree as et

r_dict = {}
tex_dir  = 'tex_files'
tchr_dir = 'Emplois Enseignants'
sgrp_dir = 'Emplois Groupes'
room_dir = 'Emplois Salles'
fict_tch = 'ZZZ_JUM_'  # Ficticious teacher prefix
fict_rm  = 'Salle OPT' # Ficticious room prefix

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

## All the P_XXX functions allow to recursively parse the FET file
## using a visitor design pattern.

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
    pass
    #print ("Parsing Institution Name: <" + elt.text + ">")

def P_Comments (elt):
    pass
    #print ("Parsing Comments: <" + elt.text + ">")

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
    """Inserts an activity (a_id) into the activities of a teacher, a
       year, a group or a subgroup."""
    
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
        'subject'  : getProperty (elt, 'Subject').text,
        'teachers' : [x.text for x in getPropertyList (elt, 'Teacher')],
        'tags'     : [x.text for x in getPropertyList (elt, 'Activity_Tag')],
        'students' : [x.text for x in getPropertyList (elt, 'Students')],
        'duration' : int (getProperty (elt, 'Duration').text),
        'day'      : None,
        'hour'     : None,
        'room'     : None,
    }
    a_id = getPropertyText (elt, 'Id')
    r_dict['activities'][a_id] = a_dict

    # Update the activity list of the corresponding teacher and
    # student group.

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

    # Some rooms have no building. Update only those who have one
    if b_name:
        r_dict['buildings'][b_name]['rooms'].add (r_name)
    
def P_Rooms_List (elt):
    r_dict ['rooms'] = {}
    Tree_Parse (elt, {'Room' : P_Room})

def P_ConstraintActivityPreferredStartingTime (elt):
    """We parse only the time constraints that are automatically generated
       by FET when freezing the time table. This allows to deduce the
       whole time table.
    """
    if active (elt):
        a_id = getPropertyText (elt, 'Activity_Id')
        day = getPropertyText (elt, 'Preferred_Day')
        hour = getPropertyText (elt, 'Preferred_Hour')

        r_dict ['activities'][a_id]['day'] = day
        r_dict ['activities'][a_id]['hour'] = hour

        # Update the corresponding teacher(s) time table
        for t in r_dict ['activities'][a_id]['teachers']:
            r_dict['teachers'][t]['timetable'][day][hour].add(a_id)

        # Update the corresponding student group(s) time table
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
    """We parse only the space constraints that are automatically
       generated by FET when freezing the time table. This allows to
       deduce the whole time table.
    """
    
    if active (elt):
        a_id = getPropertyText (elt, 'Activity_Id')
        room = getPropertyText (elt, 'Room')
        day = r_dict ['activities'][a_id]['day']
        hour = r_dict ['activities'][a_id]['hour']

        # Update the activity room. This will update automaticlly the
        # corresponding teacher(s) and student group(s) time tables as
        # these store only the activity Id an not a copy of the
        # activity.
        r_dict ['activities'][a_id]['room'] = room

        # Update the corresponding room time table
        r_dict ['rooms'][room]['timetable'][day][hour].add(a_id)
    
def P_Space_Constraints_List (elt):
    Tree_Parse (elt, {'ConstraintActivityPreferredRoom' :
                      P_ConstraintActivityPreferredRoom})

# The Latex generation part.

# The below 2 dictionaries are used to translate the day and hour
# names into their corresponding counter parts in the Latex world.

tt_d_trans = {
    'Lundi'    : 'lundi',
    'Mardi'    : 'mardi',
    'Mercredi' : 'mercredi',
    'Jeudi'    : 'jeudi',
    'Vendredi' : 'vendredi',
    'Samedi'   : 'samedi'
}

tt_h_trans = {
    '08:15 - 10:15'   : 'one',
    '08:15 - 10:15 A' : 'one',
    '08:15 - 10:15 B' : 'one',
    '10:30 - 12:30'   : 'two',
    '10:30 - 12:30 A' : 'two',
    '10:30 - 12:30 B' : 'two',
    '14:00 - 16:00'   : 'three',
    '14:00 - 16:00 A' : 'three',
    '14:00 - 16:00 B' : 'three',
    '16:15 - 18:15'   : 'four',
    '16:15 - 18:15 A' : 'four',
    '16:15 - 18:15 B' : 'four'
}

def commonFormat (s, ):
    # In Latex all '_' must be escaped in standard mode
    return s.replace ('_', '\_')

def formatRoom (room):
    return '\\formatroom{' + commonFormat (room) + '}'

def formatSubject (subject):
    return '\\formatsubject{' + commonFormat (subject) + '}'

def formatTeacher (teacher):
    return '\\formatteacher{' + commonFormat (teacher) + '}'

def formatTag (tag):
    return '(\\formattag{' + commonFormat (tag).replace('(', '').replace (')', '') + '})'

def formatStudents (students):
    return '\\formatstudents{' + commonFormat (students) + '}'

def filterTags (tags):
    # We do not include the (1/15) and (1/7) tags
    return [formatTag(t) for t in tags if t[1] != '1']

def trimTeacher (t):
    # All teacher names ending with ' N' when N is a number are
    # stripped.
    
    if t [-1] in "0123456789":
        space = t.rfind (' ')
        return t [:space]
    return t

def filterTeachers (teachers, rev = False):
    # Do not include ficticious teachers who are here only for the
    # sake of FET.
    
    l = [formatTeacher (trimTeacher (t))
            for t in teachers if t.find (fict_tch) == -1]
    l.sort (key = lambda s: len (s), reverse = rev)
    return l

def filterStudents (students, rev = False):
    l = [formatStudents (s) for s in students]
    l.sort (key = lambda s: len (s), reverse = rev)
    return l

# FIXME: The below 3 functions (Gen_xxx_H_Data) need to be factorized
# as they are very similar.

def Gen_Teacher_H_Data (d, d_dict, h):
    hA = h + ' A'
    hB = h + ' B'

    # 5 cas:

    # 1 - Les deux créneaux sont vides, on gènère une cellule grise

    # 2 - Le créneau A est vide et le créneau B est plein, on gènère
    #     une demi cellule B (1/15)

    # 3 - Les deux créneaux sont pleins, on génère deux demi cellules
    #     A et B

    # 4 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 2, on génère une cellule entière (1/7)

    # 5 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 1, on génère une demi cellule A (1/15)
    
    if len (d_dict[hA]) == 0 and len (d_dict[hB]) == 0:
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\cellcolor{lightgray}}')
    elif len (d_dict[hA]) == 0 and len (d_dict[hB]) >= 1:
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        studentsB = ', '.join(filterStudents(actB['students']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags(actB['tags']))
        roomB = formatRoom (actB ['room'])
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{}{' + roomB + ' ' + studentsB + '\\\\' +
               subjectB + '\\textsubscript{' + tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) >= 1:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        studentsA = ', '.join(filterStudents(actA['students']))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = formatRoom (actA ['room'])
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        studentsB = ', '.join(filterStudents (actB['students']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags (actB['tags']))
        roomB = formatRoom (actB ['room'])
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
               '}' + '\\\\' + studentsA + ' ' + roomA +  '}{' + roomB +
               ' ' + studentsB + '\\\\' + subjectB + '\\textsubscript{' +
               tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) == 0:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        studentsA = ', '.join(filterStudents(actA['students']))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = formatRoom (actA ['room'])
        durationA = actA ['duration']
        if durationA == 2:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdh{' + subjectA + '\\textsubscript{' + tagsA +
                   '}' + '\\\\' + studentsA + ' ' + roomA + '}}')
        else:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
                   '}' + '\\\\' + studentsA + ' ' + roomA + '}{}}')
    else:
        raise Exception ('Gen_Teacher_H_Data', actA)

def Gen_Subgroup_H_Data (d, d_dict, h):
    hA = h + ' A'
    hB = h + ' B'

    # 5 cas:

    # 1 - Les deux créneaux sont vides, on gènère une cellule grise

    # 2 - Le créneau A est vide et le créneau B est plein, on gènère
    #     une demi cellule B (1/15)

    # 3 - Les deux créneaux sont pleins, on génère deux demi cellules
    #     A et B

    # 4 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 2, on génère une cellule entière (1/7)

    # 5 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 1, on génère une demi cellule A (1/15)
    
    if len (d_dict[hA]) == 0 and len (d_dict[hB]) == 0:
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\cellcolor{lightgray}}')
    elif len (d_dict[hA]) == 0 and len (d_dict[hB]) >= 1:
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        teachersB = '\\\\'.join(filterTeachers(actB['teachers']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags(actB['tags']))
        roomB = formatRoom (actB ['room'])
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{}{' + roomB + '\\\\' + teachersB +
               ('\\\\' if len(teachersB) > 0 else '') +
               subjectB + '\\textsubscript{' + tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) >= 1:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        teachersA = '\\\\'.join(filterTeachers(actA['teachers'], True))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = formatRoom (actA ['room'])
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        teachersB = '\\\\'.join (filterTeachers(actB['teachers']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags (actB['tags']))
        roomB = formatRoom (actB ['room'])
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
               '}' + '\\\\' + teachersA +
               ('\\\\' if len(teachersA) > 0 else '') + roomA + '}{' +
               roomB + '\\\\' + teachersB +
               ('\\\\' if len(teachersB) > 0 else '') +
               subjectB + '\\textsubscript{' + tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) == 0:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        teachersA = '\\\\'.join(filterTeachers(actA['teachers'], True))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = formatRoom (actA ['room'])
        durationA = actA ['duration']
        if durationA == 2:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdh{' + subjectA + '\\textsubscript{' +
                   tagsA + '}' + '\\\\' + teachersA +
                   ('\\\\' if len(teachersA) > 0 else '') + roomA + '}}')
        else:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
                   '}' + '\\\\' + teachersA +
                   ('\\\\' if len(teachersA) > 0 else '') + roomA + '}{}}')
    else:
        raise Exception ('Gen_Subgroup_H_Data',
                         str (len (d_dict[hA])) + ' ' + str (len (d_dict[hB])))

def Gen_Room_H_Data (d, d_dict, h):
    hA = h + ' A'
    hB = h + ' B'

    # 5 cas:

    # 1 - Les deux créneaux sont vides, on gènère une cellule grise

    # 2 - Le créneau A est vide et le créneau B est plein, on gènère
    #     une demi cellule B (1/15)

    # 3 - Les deux créneaux sont pleins, on génère deux demi cellules
    #     A et B

    # 4 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 2, on génère une cellule entière (1/7)

    # 5 - Le créneau A est plein, le créneau B est vide et la durée de
    #     l'activité A est 1, on génère une demi cellule A (1/15)
    
    if len (d_dict[hA]) == 0 and len (d_dict[hB]) == 0:
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\cellcolor{lightgray}}')
    elif len (d_dict[hA]) == 0 and len (d_dict[hB]) >= 1:
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        teachersB = '\\\\'.join(filterTeachers(actB['teachers']))
        studentsB = ', '.join(filterStudents(actB['students']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags(actB['tags']))
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{}{' + studentsB + '\\\\' + teachersB +
               ('\\\\' if len(teachersB) > 0 else '') +
               subjectB + '\\textsubscript{' + tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) >= 1:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        teachersA = '\\\\'.join(filterTeachers(actA['teachers'], True))
        studentsA = ', '.join(filterStudents(actA['students']))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = actA ['room']
        actB = r_dict['activities'][list(d_dict[hB])[0]]
        teachersB = '\\\\'.join(filterTeachers(actB['teachers']))
        studentsB = ', '.join(filterStudents(actB['students']))
        subjectB = formatSubject (actB['subject'])
        tagsB = ', '.join(filterTags (actB['tags']))
        roomB = actB ['room']
        print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
               '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
               '}' + '\\\\' + teachersA +
               ('\\\\' if len(teachersA) > 0 else '') + studentsA + '}{' +
               studentsB + '\\\\' + teachersB +
               ('\\\\' if len(teachersB) > 0 else '') + subjectB +
               '\\textsubscript{' + tagsB + '}' + '}}')
    elif len (d_dict[hA]) >= 1 and len (d_dict[hB]) == 0:
        actA = r_dict['activities'][list(d_dict[hA])[0]]
        teachersA = '\\\\'.join(filterTeachers(actA['teachers'], True))
        studentsA = ', '.join(filterStudents(actA['students']))
        subjectA = formatSubject (actA['subject'])
        tagsA = ', '.join(filterTags (actA['tags']))
        roomA = actA ['room']
        durationA = actA ['duration']
        if durationA == 2:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdh{' + subjectA + '\\textsubscript{' + tagsA +
                   '}' + '\\\\' + teachersA +
                   ('\\\\' if len(teachersA) > 0 else '') + studentsA + '}}')
        else:
            print ('\\newcommand{\\' + tt_d_trans[d] + tt_h_trans[h] +
                   '}{\\formatdhh{' + subjectA + '\\textsubscript{' + tagsA +
                   '}' + '\\\\' + teachersA +
                   ('\\\\' if len(teachersA) > 0 else '') + studentsA + '}{}}')
    else:
        raise Exception ('Gen_Room_H_Data', actA)

def Gen_Teacher_D_Data (d, d_dict):
    Gen_Teacher_H_Data (d, d_dict, '08:15 - 10:15')
    Gen_Teacher_H_Data (d, d_dict, '10:30 - 12:30')
    Gen_Teacher_H_Data (d, d_dict, '14:00 - 16:00')
    Gen_Teacher_H_Data (d, d_dict, '16:15 - 18:15')

def Gen_Subgroup_D_Data (d, d_dict):
    Gen_Subgroup_H_Data (d, d_dict, '08:15 - 10:15')
    Gen_Subgroup_H_Data (d, d_dict, '10:30 - 12:30')
    Gen_Subgroup_H_Data (d, d_dict, '14:00 - 16:00')
    Gen_Subgroup_H_Data (d, d_dict, '16:15 - 18:15')

def Gen_Room_D_Data (d, d_dict):
    Gen_Room_H_Data (d, d_dict, '08:15 - 10:15')
    Gen_Room_H_Data (d, d_dict, '10:30 - 12:30')
    Gen_Room_H_Data (d, d_dict, '14:00 - 16:00')
    Gen_Room_H_Data (d, d_dict, '16:15 - 18:15')

def genPDF (f, out_dir):
    """Generate a PDF file from the fiven .tex file. The generation occurs
       inside the given out_dir directory. All temporary files
       produced during the generation are deleted.
    """
    print ('PDFLATEX  ' + (f + '.tex').ljust(27) +
           ' => ' + (f + '.pdf').rjust (27))
    os.system ('pdflatex --interaction=batchmode --output-directory="' +
               out_dir + '" "' + tex_dir + '/' + f + '.tex" > /dev/null')
    # Cleanup
    os.system ('rm "' + out_dir + '/' + f + '.aux"')
    os.system ('rm "' + out_dir + '/' + f + '.log"')

def Gen_Teacher_TT_Data (t):
    """Produce a .tex file representing the time table of the given
       teacher. Then compile it into a PDF file.
    """
    
    if t.find (fict_tch) != -1:
        # No time table for ficticious teacher
        return
    
    tt_dict = r_dict ['teachers'][t]['timetable']

    if tt_dict == emptyWeek ():
        # No empty time tables
        return

    t_name = t
    suffix = ''

    if t_name [-1] in "0123456789":
        space = t_name.rfind (' ')
        t_name = t [:space]
        suffix = t [space:]

    # Instead of passing the file as argument. We temporarily redirect
    # stdout to the .tex file and using print to generate its content.
    
    orig_stdout = sys.stdout
    f = open (tex_dir + '/' + t + '.tex', 'w')
    sys.stdout = f
    
    print ('\\input{common_header.tex}')
    print ('\\newcommand{\\teacher}{' + t_name + '}')
    print ('\\newcommand{\\semestrepartie}{' + suffix + '}')
    print ('\\newcommand{\\fulltitle}{\\teacher{}\\semestrepartie{}}')
    print ('\\newcommand{\\teachersign}{{\\bf Signature de l\'enseignant}' +
           '\\\\{\\bf \\teacher{}}}')
    print ('\\newcommand{\\dirdptsign}{{\\bf Signature du directeur de ' +
           'département \\dpt{}}\\\\{\\bf \\dirdpt{}}}')
    for d in tt_dict:
        Gen_Teacher_D_Data (d, tt_dict [d])
    print ('\\input{common_footer.tex}')

    # Restore stdout
    sys.stdout = orig_stdout

    f.close()
    genPDF (t, tchr_dir)

def Gen_Subgroup_TT_Data (sg):
    """Produce a .tex file representing the time table of the given
       subgroup. Then compile it into a PDF file.
    """
    
    tt_dict = r_dict ['sgroups'][sg]['timetable']

    if tt_dict == emptyWeek ():
        # No empty time tables
        return
    
    s_name = sg[:-3] # Section
    g_name = sg[-1]  # Groupe

    # Instead of passing the file as argument. We temporarily redirect
    # stdout to the .tex file and using print to generate its content.

    orig_stdout = sys.stdout
    f = open (tex_dir + '/' + sg + '.tex', 'w')
    sys.stdout = f

    print ('\\input{common_header.tex}')
    print ('\\newcommand{\\fulltitle}{Section ' + s_name + ' Groupe '
           + g_name + '}')
    print ('\\newcommand{\\teachersign}{}')
    print ('\\newcommand{\\dirdptsign}{{\\bf Signature du directeur '
           'de département \\dpt{}}\\\\{\\bf \\dirdpt{}}}')
    for d in tt_dict:
        Gen_Subgroup_D_Data (d, tt_dict [d])
    print ('\\input{common_footer.tex}')

    # Restore stdout
    sys.stdout = orig_stdout
    
    f.close()
    genPDF (sg, sgrp_dir)

def Gen_Room_TT_Data (r):
    """Produce a .tex file representing the time table of the given
       room. Then compile it into a PDF file.
    """
    
    if r.find (fict_rm) != -1:
        # No time table for ficticious room
        return
    
    tt_dict = r_dict ['rooms'][r]['timetable']

    if tt_dict == emptyWeek ():
        # No empty time tables
        return

    # Instead of passing the file as argument. We temporarily redirect
    # stdout to the .tex file and using print to generate its content.
    
    orig_stdout = sys.stdout
    f = open (tex_dir + '/' + r + '.tex', 'w')
    sys.stdout = f

    print ('\\input{common_header.tex}')
    print ('\\newcommand{\\fulltitle}{Salle ' + r + '}')
    print ('\\newcommand{\\teachersign}{}')
    print ('\\newcommand{\\dirdptsign}{}')
    for d in tt_dict:
        Gen_Room_D_Data (d, tt_dict [d])
    print ('\\input{common_footer.tex}')

    # Restore stdout
    sys.stdout = orig_stdout
    
    f.close()
    genPDF (r, room_dir)

# Main program

if __name__ == '__main__':
    if (len (sys.argv) == 1):
        input_file = '2018-2019_Sem-2_ENIS_DGIMA_data_and_timetable.fet'

    if (len (sys.argv) >= 2):
        # Assume the first command line argument to be the FET file
        input_file = sys.argv [1]

    if (len (sys.argv) >= 3):
        # Assume the second command line argument to be the TeX files dir
        tex_dir = sys.argv [2]
    
    if (len (sys.argv) >= 4):
        # Assume the third command line argument to be the teachers PDF dir
        tchr_dir = sys.argv [3]
    
    if (len (sys.argv) >= 5):
        # Assume the fourth command line argument to be the students PDF dir
        sgrp_dir = sys.argv [4]

    if (len (sys.argv) >= 6):
        # Assume the fifth command line argument to be the teachers PDF dir
        room_dir = sys.argv [5]
    
    # Parse the FET file and store it into a sort of an AST
    
    xml  = et.parse(input_file)
    root = xml.getroot()

    visitor_tree = {
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

    Tree_Parse (root, visitor_tree)

    # Prepare the Latex generation phase

    os.makedirs (tex_dir,  exist_ok = True)
    os.makedirs (tchr_dir, exist_ok = True)
    os.makedirs (sgrp_dir, exist_ok = True)
    os.makedirs (room_dir, exist_ok = True)

    # Generate the time tables

    stopAfterOne = False # For testing purpose only to generate only
                        # one timetable from each kind.
    
    for t in r_dict['teachers']:
        Gen_Teacher_TT_Data (t)
        if stopAfterOne:
            break

    for sg in r_dict['sgroups']:
        Gen_Subgroup_TT_Data (sg)
        if stopAfterOne:
            break

    for r in r_dict['rooms']:
        Gen_Room_TT_Data (r)
        if stopAfterOne:
            break
