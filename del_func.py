__author__ = 'pablogsal'


#FUNCTIONS###############################################################

#This deletes the INTER-outliers if the night has been detectes as outlier in general


def remove_internight(clean_list):
    global deleteflag
    print(utilities.bcolors.WARNING+'I will remove inter-outlier for outlier nights'+utilities.bcolors.ENDC+'\n')


    outliers_list_pos=utilities.find_outlayers(utilities.night_stats(clean_list).median())
    for i in outliers_list_pos:
        temp=utilities.find_outlayers([a.average for a in clean_list[i]] )
        blacklist= [clean_list[i][j].direction for j in temp ]

        for blackitem in blacklist:
            os.remove(blackitem)
            print("Removed "+blackitem)



#This deletes the INTER-outliers for all nights

def remove_interall(clean_list):
    global deleteflag
    print(utilities.bcolors.FAIL+'I will remove inter-outlier for all nights'+utilities.bcolors.ENDC+'\n')

    for i in range(len(clean_list)):
        temp=utilities.find_outlayers([a.average for a in clean_list[i]] )
        blacklist= [clean_list[i][j].direction for j in temp  ]

        for blackitem in blacklist:
            os.remove(blackitem)
            print("Removed "+blackitem)



#This deletes the night if the night has been detectes as outlier in general

def remove_night(clean_list):
    global deleteflag
    print(utilities.bcolors.FAIL+'I will remove outlier nights'+utilities.bcolors.ENDC+'\n')

    outliers_list_pos=utilities.find_outlayers(utilities.night_stats(clean_list).median())
    for i in outliers_list_pos:
        blacklist= [j.direction for j in clean_list[i]]

        for blackitem in blacklist:
            os.remove(blackitem)
            print("Removed "+blackitem)

#This deletes the night if the night has been detectes as bad in general


def remove_badnight(clean_list):
    print(utilities.bcolors.FAIL+'I will remove bad nights'+utilities.bcolors.ENDC+'\n')

    bad=[i for i in clean_list if len(i)<3 ]
    for night in bad:
        for bad_file in night:
            os.remove(bad_file.direction)
            print("Removed "+bad_file.direction)

    print('Removed '+str(len(bad))+' bad nights.')
    file.write('Removed '+str(len(bad))+' bad nights.')
    print('\n')
    file.write('\n' )


def remove_cludy(clean_list):
    print(utilities.bcolors.FAIL+'I will remove cloudy images'+utilities.bcolors.ENDC+'\n')
    filelist=[]
    for night in clean_list:
        for test_file in night:
            filelist.append(test_file)

    clouds=[]
    blacklist=[a for a in filelist if a.average >= 600 ]

    for bad_file in blacklist:
            os.remove(bad_file.direction)
            print("Removed "+bad_file.direction)
            clouds.append(["/".join(bad_file.give_time()[0:3]),bad_file.average])

    print('Removed '+str(len(blacklist))+' cloudy images.')
    file.write('\n' )
    file.write('Removed '+str(len(blacklist))+' cloudy images.')
    print('\n')
    if len(clouds)>0:
        file.write('\n' )
        file.write(tabulate.tabulate(clouds, headers=['Date', 'Medians'], tablefmt='orgtbl'))

    file.write('\n' )

def remove_cludy_std(clean_list):
    print(utilities.bcolors.FAIL+'I will remove cloudy images'+utilities.bcolors.ENDC+'\n')
    filelist=[]
    for night in clean_list:
        for test_file in night:
            filelist.append(test_file)

    clouds=[]
    blacklist=[a for a in filelist if a.stdev <= 7 ]

    for bad_file in blacklist:
            os.remove(bad_file.direction)
            print("Removed "+bad_file.direction)
            clouds.append(["/".join(bad_file.give_time()[0:3]),bad_file.stdev])

    print('Removed '+str(len(blacklist))+' cloudy images.')
    file.write('\n' )
    file.write('Removed '+str(len(blacklist))+' cloudy images.')
    print('\n')
    if len(clouds)>0:
        file.write('\n' )
        file.write(tabulate.tabulate(clouds, headers=['Date', 'Stdev'], tablefmt='orgtbl'))

    file.write('\n' )




##################################################################