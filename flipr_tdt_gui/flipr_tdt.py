#version 1.0
#script to handle tab-delimited data, put it in a python-friendly format, and perform FLIPR statistics and plotting
#by Phil Nova


########
#Import#
########

import csv
import math
import numpy as np
import matplotlib.pyplot as plt

####################
#Initialize Globals#
####################

#store the number of rows and columns on the plate
NROW = None
NCOL = None

#################
#Helper funtions#
#################

def checkEqual(iterator):
    #function to determine whether all items in list are identical. Useful in strip() function
  return len(set(iterator))<=1

def platesize(data, runtemp=37):
    #determine the size of the plate; called as a helper function by snapshot()
    #relies on the fact that the data is formatted as blocks of snapshots where each block begins with the temperature
    global NCOL
    
    blockStart = None
    blockEnd = None

    #create tolerance for temperature +/- 1 degree
    runrange = [str(runtemp-1),str(runtemp),str(runtemp+1)]
    
    for rowNum in range(len(data)):
        if data[rowNum][0][0:2] in runrange and len(data[rowNum])==len(data[rowNum+1])+1: #length check ensures that the temperature-containing row is longer than the one following it; this protects against the case in which a row of data happens to start with the running temperature
            if not bool(blockStart):
                blockStart = rowNum
            else:
                blockEnd = rowNum
                break

    NCOL = len(data[blockStart+1])
    #print "I think your plate has "+str(len(data[blockStart+1]))+" columns." #allows user to check assumptions of program re: plate size
    return (blockStart, blockEnd)

def suggestRunTemp(data):
        #alternative to platesize if calling platesize throws an error; gives a suggestion for the correct runtemp
        altruntemp = None
        for rownum in range(len(data)):
                if data[rownum][0][0:6]=='Temper':
                        altruntemp = data[rownum+1][0]
                        return altruntemp            

def detectPipetteIndex(pipetteTime, timeList):
        c = 0
        for t in timeList:
                if pipetteTime<=t:
                        return c
                else:
                        c+=1
        return c

def beforeAfterSeparator(snapDict, row, column, pipetteTime, excludeBefore = 2, excludeAfter = 5, ignoreBefore = 0):
    #used for Individual and Replicate classes to separate data into two dictionaries holding values before and after pipetting, respectively, and excluding some values within a specified window of the pipette time
    global PIPETTE_INDEX
    keys = snapDict.keys()
    keys.sort()

    PIPETTE_INDEX = detectPipetteIndex(pipetteTime, keys)
    
    beforeDict = dict()
    afterDict = dict()

    for key in keys:
        if key > ignoreBefore:
            if key<pipetteTime - excludeBefore:
                beforeDict[key] = snapDict[key][row][column]
            elif key>pipetteTime + excludeAfter:
                afterDict[key] = snapDict[key][row][column]

    return (beforeDict, afterDict)




##########################
#Data-formatting funtions#
##########################

def file_to_list(filename):
    #convert tab-delimited text file to Python list using csv module

    dataList = list()
    
    with open(filename,'rU') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                    dataList.append(row)

    return dataList


def strip(data):
    #remove empty spaces from list

    strippedData1 = list()
    strippedData2 = list()

    for row in data:
        #first pass through data - remove rows that consist only of ' ' over and over. Can cheat by excluding any list with all-identical entries
        if len(row)==1 or not checkEqual(row):
            #if not all items in list are the same, append the list. Len() check is b/c a one-item list has all-identical entries, but these should not be excluded
            strippedData1.append(row)

    
    unwanted = [' ','','.',',']
    for row in strippedData1:
        #second pass through data; go through each row and eliminate any item that is on the unwanted list
        newrow = list()
        for item in row:
            if not item in unwanted:
                newrow.append(item)
        strippedData2.append(newrow)

    return strippedData2


def snapshot(data, runtemp = 37, endchar = ['~End']):
    #create a list of lists where each of the latter is a 'snapshot' of the plate at roughly one time
    global NROW


    platerange = platesize(data, runtemp)
    
    numRows = platerange[1]-platerange[0]

    NROW = numRows/2

    #print "I think your plate has "+str(NROW)+" rows." #allows user to check assumptions of program re: plate size
    
    end = data[platerange[0]::].index(endchar)

    snapshotList = list()

    i = 0
    while i<end:
        snapshotList.append(data[platerange[0]::][i:i+numRows])
        i+=numRows

    return snapshotList
    

def timeList(snap):
        rfuValueList = [[[float(i) for i in group] for group in snap[timepoint] if snap[timepoint].index(group)%2==1] for timepoint in range(len(snap))]
        return rfuValueList

#below involves looping over same data more times; re-did this code as above list comprehension. Left original code below b/c it is more readable
    #for sn in range(len(snap)):
        #rfuValueList = [snap[sn][val] for val in range(len(snap[sn])) if val%2==1] #value for dict will be RFU data (i.e. exclude time values)
        #rfuValueList = [[float(i) for i in n] for n in rfuValueList] #convert all items to float; is there a way to combine this w/ previous line?
        #timeD[float(snap[sn][0][1])]=rfuValueList #use first time value in snapshot as key

def timeDict(snap):
    #turn output of snapshot() into a dictionary, keyed by time, where each value is a snapshot at that approximate time
    timeD = dict()

    #rfuValueList = timeList(snap)
    rfuValueList = [[[float(i) for i in group] for group in snap[timepoint] if snap[timepoint].index(group)%2==1] for timepoint in range(len(snap))]

    

    for sn in range(len(snap)):
        timeD[float(snap[sn][0][1])]=rfuValueList[sn]
    
    return timeD

##################################
#Statistical funtions and classes#
##################################

class Individual(object):
    #represents the behavior of a single well
    def __init__(self, snap, row, column, pipetteTime = 18, ignore = 0):
        snapDict = timeDict(snap)
        self.before, self.after = beforeAfterSeparator(snapDict, row, column, pipetteTime, ignore)
        snapList = timeList(snap)
        self.allValues = [snapList[t][row][column] for t in range(len(snapList))]
        self.name = number_to_well((row,column))
        self.pipetteTime = pipetteTime
        self.pipette = PIPETTE_INDEX

    def meanBef(self):
        self.meanBefore = sum(self.before.values())/float(len(self.before.values()))
        return self.meanBefore
        

    def meanAft(self):
        self.meanAfter = sum(self.after.values())/float(len(self.after.values()))
        return self.meanAfter
        

    def meanDiff(self):
        before = self.meanBef()
        after = self.meanAft()
        self.meanDifference = after - before
        return self.meanDifference

    def normmeanDiff(self):
            self.normmeanMeanDiff = self.meanDiff() / self.meanBef()
            return self.normmeanMeanDiff

    def stdErr(self):
        STD1 = np.std(self.before.values())
        STD2 = np.std(self.after.values())
        n1 = float(len(self.before.values()))
        n2 = float(len(self.after.values()))
        self.stdError = math.sqrt((STD1**2 / n1) + (STD2**2 / n2))
        return self.stdError


    def stdev(self):
            self.stdev = np.std(self.allValues)
            return self.stdev
        
    def plotAllValues(self):
            plt.title(self.name)
            plt.xlabel('Time (s)')
            plt.ylabel('RFU')
            plt.plot(self.allValues)
            plt.axvline(x=self.pipette, color='k', ls='dashed')
            plt.show()
            
    def diffMaxBeforeMaxAfter(self):
            self.MaxBefore = max(self.before.values())
            self.MaxAfter = max(self.after.values())
            self.diffMaxBeforeMaxAfter = self.MaxAfter - self.MaxBefore
            return self.diffMaxBeforeMaxAfter

    def diffMaxNormalized(self):
            self.diffMaxNormalized = self.diffMaxBeforeMaxAfter/self.meanBef()
            return self.diffMaxNormalized
        
class Replicate(object):
    #represents multiple wells
    def __init__(self, name, *individuals):
        if not type(individuals[0])==type(tuple()):
                self.individuals = [indiv for indiv in individuals]
        else:
                #clause to help replicateMaker(), which stores groups of indivudals in a tuple
                self.individuals = [indiv for indiv in individuals[0]]
        self.name = name

    def __str__(self):
        print "Contains "+str(len(self.individuals))+" individuals."

    def meanMeanDiff(self):
        meanDifferences = list()
        for indiv in self.individuals:
            meanDifferences.append(indiv.meanDiff())
        self.meanMeanDifference = sum(meanDifferences)/float(len(meanDifferences))
        return self.meanMeanDifference

    def normmeanMeanDiff(self):
        normmeanDifferences = list()
        for indiv in self.individuals:
            normmeanDifferences.append(indiv.normmeanDiff())
        self.normmeanMeanDifference = sum(normmeanDifferences)/float(len(normmeanDifferences))
        return self.normmeanMeanDifference
    def combinedStdError(self):
        errs = list()
        for indiv in self.individuals:
            errs.append(indiv.stdErr()**2)
        self.stdError = math.sqrt(sum(errs))/len(errs)
        return self.stdError

##    def combinedStdev(self):
##            stdevs = list()
##            samplesize = list()
##            samplemeans = list()
##            
##            for indiv in self.individuals:
##                    stdevs.append(indiv.stdev())
##                    samplesize.append(len(indiv.allValues))
##                    samplemeans.append(sum(indiv.allValues)/samplesize[-1])
##
##            newmean = sum(samplemeans)/len(samplemeans)
##            running = 0
##            for i in range(len(stdevs)):
##                    running+= (samplesize[i]*stdevs[i]**2)+(samplesize[i]*(newmean - samplemeans[i])**2)
##
##            stdev = math.sqrt(running / sum(samplesize))
##
##            self.combinedStdev = stdevb
##            return self.combinedStdev

    def combinedStdevSimple(self):
            meanDiffs = list()

            for indiv in self.individuals:
                    meanDiffs.append(indiv.meanDiff())

            self.combinedStdev = np.std(meanDiffs)
            return self.combinedStdev

    def diffofMaxima(self):
            diffofMaximaList = list()
            for indiv in self.individuals:
                    diffofMaximaList.append(indiv.diffMaxBeforeMaxAfter())
            self.diffofMaxima = sum(diffofMaximaList)/len(diffofMaximaList)
            return self.diffofMaxima

    def meanBef(self):
        before_list = []
        for indiv in self.individuals:
            before_list.append(indiv.meanBef())
        self.meanBef = sum(before_list)/float(len(before_list))
        return self.meanBef

    def meanAft(self):
        after_list = []
        for indiv in self.individuals:
            after_list.append(indiv.meanAft())
        self.meanAft = sum(after_list)/float(len(after_list))
        return self.meanAft



    def combineddiffMaxNormalized(self):
            diffMaxNormalizedList = list()
            for indiv in self.individuals:
                    diffMaxNormalizedList.append(indiv.diffMaxNormalized()*100)
            self.diffMaxNormalized = sum(diffMaxNormalizedList)/len(diffMaxNormalizedList)
            return self.diffMaxNormalized
    
            
###################
#Plotting funtions#
###################

def plotAllIndivs(replicate, filename):
        plt.title(replicate.name)
        plt.xlabel('Time (s)')
        plt.ylabel('RFU')
        for indiv in replicate.individuals:
                plt.plot(indiv.allValues, label = indiv.name)
        plt.axvline(x=replicate.individuals[0].pipette, color='k', ls='dashed')
        plt.legend()
        plt.savefig(filename+'_'+replicate.name+'.png')
        plt.close()

def tilePlot(indivArray, name):
        names = list()
        num_rows = len(indivArray)
        num_cols = len(indivArray[0])
        for r in range(num_rows):
                for c in range(num_cols):
                        names.append(str(r)+str(c))
        
        f, names = plt.subplots(num_rows, num_cols, sharex='col', sharey='row')

        for r in range(num_rows):
            for c in range(num_cols):
                
                        names[r][c].plot(indivArray[r][c].allValues)
                #if r*c<=48: #only show names if plot is relatively small
                        #names[r][c].set_title(indivArray[r][c].name)
                #else: #if plot is large, remove x and y ticks on all axes
                        names[r][c].tick_params(axis='x', which='both', bottom='off', top='off', labelbottom='off') # labels along the bottom edge are off
                        names[r][c].tick_params(axis='y', which='both', left='off', right='off', labelbottom='off') # labels along the bottom edge are off
                
        f.subplots_adjust(hspace=.05)
        
        plt.setp([a.get_xticklabels() for a in f.axes[:]], visible=False)
        plt.setp([a.get_yticklabels() for a in f.axes[:]], visible=False)
        

        #plt.show()
        
        name+='.png'
        plt.savefig(name)
        plt.close()

def tilePlot2(indivArray, name):
        num_rows = len(indivArray)
        num_cols = len(indivArray[0])

        names = list()
        codes = list()
        counterlist = list()

        counter = 0

        for r in range(num_rows):
            
            names.append(list())
            codes.append(list())
            counterlist.append(list())
            
            for c in range(num_cols):
                counter+=1
                names[r].append(str(r)+str(c))
                codes[r].append(c)
                counterlist[r].append(counter)

                 

        fig = plt.figure()
        ax = fig.add_subplot(111)    # The big subplot


        for r in range(num_rows):
            for c in range(num_cols):

                names[r][c]=fig.add_subplot(num_rows, num_cols, counterlist[r][c])

        # Turn off axis lines and ticks of the big subplot
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')

        for r in range(num_rows):
            for c in range(num_cols):
                
                names[r][c].plot(indivArray[r][c].allValues)
                names[r][c].set_title(indivArray[r][c].name)

        # Set common labels
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('RFU')

        fig.subplots_adjust(hspace=.25)

        plt.setp([a.get_xticklabels() for a in fig.axes[-1:]], visible=False)        
        plt.show()
        
def replicatePlot(reps, name):
        names = [i.name for i in reps]
        y_pos = np.arange(len(names))
        means = [i.meanMeanDiff() for i in reps]
        stderrs = [i.combinedStdError() for i in reps]
        plt.barh(y_pos, means, xerr=stderrs, align='center', alpha=0.4)
        plt.yticks(y_pos, names)
        plt.xlabel('Mean Difference')
        plt.title('Replicates')
        #plt.show()
        name+='.png'
        plt.savefig(name)
        plt.close()

def replicateText(reps, name):
        names = [i.name for i in reps]
        means = [i.meanMeanDiff() for i in reps]
        stderrs = [i.combinedStdError() for i in reps]

        fo = open(name+'.txt', 'w')
        fo.write('Replicate Data')
        fo.write('/n','/n')

        for i in range(len(names)):
                fo.write('NAME '+names[i])
                fo.write('/n')
                fo.write('MEAN DIFF '+means[i])
                fo.write('/n')
                fo.write('STDERR '+stderrs[i])
                fo.write('/n')
                fo.write('/n')
        fo.close()

######################
#Interactive funtions#
######################

def well_to_number(well):

    alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    alph=list(alph)

    assert type(well)==type('a'), 'Well must be a string'
    assert well[0].upper() in alph, 'First character in well ID must be a letter'

    row = alph.index(well[0].upper())

    if len(well)==2:
        col = int(well[1])-1
    else:
        col = int(well[1::])-1

    return row, col

def number_to_well(tup):
        alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        alph = list(alph)

        row = alph[tup[0]]
        col = tup[1::]
        col = int(col[0])+1
        
        well = str(row)+str(col)+' '

        return well

def individualMaker(snapDict, pipettetime = 18, ignore = 0):
    #take in time dictionary of snapshots and return row x col array of Individuals
    indivArray = list()
    

    for r in range(NROW):
            indivArray.append(list())
            for c in range(NCOL):
                    indivArray[r].append(Individual(snapDict, r, c, pipettetime, ignore))

    return indivArray

def individualMaker_manualTime(snap):
        indivArray = list()
        pipettetime = list()
        

        snapDict = timeDict(snap)
        snapList = timeList(snap)

        keys = snapDict.keys()
        keys.sort()
        k_range = keys[-1]-keys[0]
        k_factor = k_range/(len(keys))
        
        
        for r in range(NROW):
                pipettetime.append(list())
                for c in range(NCOL):
                        fig = plt.figure()
                        ax = fig.add_subplot(111)
                        
                        allValues = [snapList[t][r][c] for t in range(len(snapList))]
                        ax.plot(allValues)

                        def onclick(event):
                                global pip
                                pip = event.xdata * k_factor
                                #print pip
                                plt.close()
                                return
                                
                        cid = fig.canvas.mpl_connect('button_press_event', onclick)
                        plt.show()
                        pipettetime[r].append(pip)
        

        
        for r in range(NROW):
                indivArray.append(list())
                for c in range(NCOL):
                        indivArray[r].append(Individual(snap, r, c, pipettetime[r][c]))

        return indivArray

def allPossibleTuple():
        allPossible = list()
        for r in range(NROW):
                for c in range(NCOL):
                        allPossible.append((r,c))
        return allPossible

def replicateMaker(indivArray, replicateTuple):
    #take in a tuple of tuples containing the replicates, or enter None if there are no replicates
    #sample input: (indivArray, (('A1','A2','A3'),('B1','B2','B3')))
    if replicateTuple == None:
            return indivArray
    else:
            remaining = allPossibleTuple()
            repList = list()
            i = len(repList)
            while i < len(replicateTuple):
                    repList.append(list())
                    for well in replicateTuple[i]:
                            repList[i].append(well_to_number(well))
                            remaining.remove(well_to_number(well))
                    i+=1
        #if an individual well was not mentioned by the user, turn it into a single-individual replicate
                    
            for single in remaining:
                    repList.append([single])
                    
            replicateArray = list()
            for rep in repList:

                    name = str()
                    individuals = list()
                    for tup in rep:
                            name+=number_to_well(tup)
                            individuals.append(indivArray[tup[0]][tup[1]])
                            
                    individuals = tuple(individuals)
                    replicateArray.append(Replicate(name, individuals))
                    
    

        
            return replicateArray
                    
                    
def replicateMaker2(indivArray, replicateTuple, indiv_as_rep):
    #reworked version of replicateMaker function designed to work with flipr_tdt_GUI
    if replicateTuple == None:
            return indivArray
    else:
            remaining = allPossibleTuple()
            repList = list()
            i = len(repList)
            while i < len(replicateTuple):
                    repList.append(list())
                    for well in replicateTuple[i]:
                            repList[i].append(well)
                            try:
                                    remaining.remove(well)
                            except ValueError:
                                    pass
                    i+=1
        #if an individual well was not mentioned by the user, turn it into a single-individual replicate
                    #but only if user chose to do so
            if indiv_as_rep:        
                    for single in remaining:
                            repList.append([single])
                    
            replicateArray = list()
            for rep in repList:

                    name = str()
                    individuals = list()
                    for tup in rep:
                            name+=number_to_well(tup)
                            individuals.append(indivArray[tup[0]][tup[1]])
                            
                    individuals = tuple(individuals)
                    replicateArray.append(Replicate(name, individuals))
                    
    

        
            return replicateArray                    
    
    
    
    

###########
#Main Loop#
###########
        
##notfound = True
##while notfound:
##    inputfile = input("Input filename: ")
##    try:
##        lst = file_to_list(inputfile)
##        errors = None #change this to a check for errors using list comprehension
##        if errors:
##            print "Incorrect record format in records: \n"
##            for i in errors: print i
##            raise ValueError
##        
##        notfound = False
##
##    except NameError:
##        print "Invalid file. Please enter a correct file."
##        notfound = True


###########
#Test Code#
###########

##inputfile = input("Input filename: ")

##reps = replicateMaker(indivs, (('A1', 'B1'), ('A2','B2'),('A3','B3')))

##i1 = Individual(td, 1,1)
##i2 = Individual(td, 1, 2)
##print i1.meanDiff()
##print i2.meanDiff()
##print i1.meanDiff()
##r = Replicate(i1, i2)
##print r.individuals
##print r.combinedStdError()
##print r.meanMeanDiff()

#########
#~~Log~~#
#########
#
#1/6/14:
#Created main loop, file_to_list(), and strip()
#Need to break data into a list where each entry is the readings from the plate at one point in time; or perhaps a dictionary indexed by approximate time
#Created the list portion of the latter using a function called snapshot()
#fix try-except block b/c it does not actually catch incorrect filenames
#
#1/7/14:
#Created timeDict(), building off of snapshot()
#Had idea to treat replicates of wells as a class with built-in-methods to determine means, error, etc.
#Created Individual and Replicate classes and implemented basic methods
#
#1/8/14:
#Created function that automatically turns each well into an Individual
#
#1/10/14:
#Created function that allows the user to enter a tuple of tuples of wells, and turn each of the latter into a Replicate
#Function also turns any remaining individuals into one-individual Replicates
#
#1/13/14:
#Started work on Tkinter GUI in separate file (flipr_tdt_GUI)
#
#1/14/14:
#Tested code against data analysis performed in Excel. Results are the same!