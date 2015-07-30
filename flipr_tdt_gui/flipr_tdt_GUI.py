########
#Import#
########

import string

try:
    from Tkinter import *
except ImportError: #Python 3
    from tkinter import *


import flipr_tdt as ft
import tkMessageBox
import PIL
from PIL import Image, ImageTk

####################
#Initialize Globals#
####################

PLATE_FORMAT = None
PLATE_ROWS = None
PLATE_COLS = None
SCREEN = None
ANALYSIS_NAME = None
FILE_NAME = None
lst = None #stores array of plate read data
counter = 0 #allows second screen to tick through list of colors
READ_TEMP = 37
COMPOUND_ADD_TIME = 18
IGNORE = 0 #do not use any values before this time

##############
#Start Window#
##############

def StartWindow():
    master = Tk()

    master.wm_title("FLIPPER!")
                    
    
    var = StringVar()
    var2 = StringVar()
    var3 = StringVar()
    
    title = Label(master, text="Enter the name of your file")
    title.grid(row=0)
    
    label1 = Label(master, text=".txt")
    label1.grid(row=01, column=1)
    #label1.pack(side='right')
    
    e = Entry(master)
    e.grid(row=01, column=0)
    #e.pack(side='left')
    
    e.focus_set()

    title2 = Label(master, text="Read Temperature")
    title2.grid(row=02)
    
    e2 = Entry(master, textvariable=var, width=3)
    e2.grid(row=03)
    e2.focus_set()
    var.set('37')

    title3 = Label(master, text="Compound Addition Time (s)")
    title3.grid(row=04)

    e3 = Entry(master, textvariable = var2, width=3)
    e3.grid(row=05)
    e3.focus_set()
    var2.set('18')

    title4 = Label(master, text="Ignore Reads Before Time (s)")
    title4.grid(row=6)

    e4 = Entry(master, textvariable = var3, width = 3)
    e4.grid(row = 7)
    e4.focus_set()
    var3.set("0")

    title5 = Label(master, text="(c) Phil Nova 2014")
    title5.grid(row=10)
    
    
##    logo = ImageTk.PhotoImage(Image.open('flipperlogo.png'))
##    Label(master, image=logo).grid(row=01, column=3)

    image = Image.open('flipperlogo.png')
    image = image.resize((125, 125), Image.ANTIALIAS) #The (250, 250) is (height, width)
    logo = ImageTk.PhotoImage(image)
    Label(master, image=logo).grid(row=10, column=0)
    
    def callback():
        global FILE_NAME
        global READ_TEMP
        global COMPOUND_ADD_TIME
        global IGNORE
        global message
        FILE_NAME = e.get()
        READ_TEMP = int(e2.get())
        proceed = True

        IGNORE = int(e4.get())

        try:
            COMPOUND_ADD_TIME = int(e3.get())
        except ValueError:
            COMPOUND_ADD_TIME = e3.get()
            if COMPOUND_ADD_TIME.lower()!='manual':
                proceed = False
                tkMessageBox.showerror('Processing Error','Invalid Pipette Time')
                
        
        

        global lst
        try:
            FILE_NAME+='.txt'
            lst = ft.file_to_list(FILE_NAME)

            try:
                snap = ft.snapshot(ft.strip(lst), runtemp=READ_TEMP)
            except TypeError:
                tkMessageBox.showerror('Processing Error','Run Temperature Not Recognized; Alternate Run Temperature Suggested')
                alttemp = ft.suggestRunTemp(ft.strip(lst))
                var.set(str(int(round(float(alttemp)))))
                proceed = False
            
        except IOError:
            tkMessageBox.showerror('File Error','No Such File in Current Directory')
            proceed = False

        
        
        if proceed == True:
            global SCREEN
            global indivs
            

            if type(COMPOUND_ADD_TIME)==type('hello'):
                master.destroy()
                indivs = ft.individualMaker_manualTime(snap)
                
            else:
                indivs = ft.individualMaker(snap, COMPOUND_ADD_TIME, IGNORE)
                master.destroy()
            SCREEN += 1
            
            
            

    b = Button(master, text="Enter", width=10, command=callback)
    b.grid(row=9)
    #b.pack(side='bottom')

    
    
    mainloop()



##############
#First Screen#
##############

#User chooses plate format - 48 or 96 wells

class PlateFormatWindow():
    def __init__(self, master):
        self.master=master
        self.startwindow()
        

    def startwindow(self):

        self.var1 = IntVar()
        self.textvar = StringVar()

        self.Label1=Label(self.master, text="Select Plate Format")
        self.Label1.grid(row=0, column=0)

        self.Label2=Label(self.master, textvariable=self.textvar)
        self.Label2.grid(row=2, column=0)

        self.rb0 = Radiobutton(self.master, text="384 Well", variable = self.var1, value=0, command=self.cb1select)
        self.rb1.grid(row=1, column = 0, sticky=W)
        
        self.rb1 = Radiobutton(self.master, text="96 Well", variable=self.var1,
                               value=1, command=self.cb1select)
        self.rb1.grid(row=1, column=1, sticky=W)

        self.rb2 = Radiobutton(self.master, text="48 Well", variable=self.var1,
                               value=2, command=self.cb1select)
        self.rb2.grid(row=1, column=2, sticky=W)

        self.Button1=Button(self.master, text="OK", command=self.ButtonClick)
        self.Button1.grid(row=1, column=2)

    def ButtonClick(self):
        global PLATE_FORMAT
        global SCREEN
        SCREEN+=1
        if (self.var1.get())==0:
            PLATE_FORMAT = 384
            self.master.destroy()
        elif (self.var1.get())==1:
            PLATE_FORMAT=96
            self.master.destroy()  
        elif (self.var1.get())==2:
            PLATE_FORMAT=48
            self.master.destroy()  
        else:
             SCREEN-=1

    def cb1select(self):
        return self.var1.get()


    

###############
#Second Screen#
###############

selected = list()
replicates = list()


def greyout():
    #grey out unused rows and columns
    return (PLATE_ROWS - ft.NROW, PLATE_COLS - ft.NCOL)
    

#User selects replicates and desired analyses
def SecondWindow():
    master = Tk()
    oncanvas = False

    #GLOBALS FOR COLOR-CODING
    colors = ["black","red","green","blue","cyan","yellow","magenta"]
    object_codes = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')+list('abcdefghijklmnopqrstuvwxyz')+list('1234567890!@#$%^&*()-_+={}[]|\/?><.,`~:;')
    
    v = StringVar()
    hover = StringVar()
    #store current replicates
    
    topLeftFrame = Frame(master)
    topLeftFrame.pack(side = LEFT)

    topRightFrame = Frame(master)
    topRightFrame.pack(side = RIGHT)

    bottomFrame = Frame(master)
    bottomFrame.pack(side = BOTTOM)

    platewidth = (PLATE_COLS+2)*20
    plateheight = (PLATE_ROWS+2)*20

    
    
    c = Canvas(topLeftFrame, width= platewidth, height= plateheight, bg='white')

    
    
    alph = list(string.printable)
    rowlabels = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    for i in range(1,PLATE_ROWS+2):
        c.create_line([20, i*20, platewidth-20, i*20])
    for i in range(1,PLATE_ROWS+1):
        c.create_text(12.5, 10+i*20, text=str(rowlabels[i-1]))

    for i in range(1, PLATE_COLS+2):
        c.create_line([i*20, 20, i*20, plateheight-20])
    for i in range(1, PLATE_COLS+1):
        c.create_text(10+i*20, 12.5, text=str(i))

    unused = greyout()

    
    for rownum in range(unused[0]):
        for colnum in range(PLATE_COLS):
            c.create_rectangle([colnum*20+20, plateheight-(rownum*20+20), colnum*20+40, plateheight-(rownum*20+40)], width=1, fill='grey')
            
    for colnum in range(unused[1]):
        for rownum in range(PLATE_ROWS): 
            c.create_rectangle([platewidth-(colnum*20+40), rownum*20+20, platewidth-(colnum*20+20), rownum*20+40], width=1, fill='grey')
            

    #COLOR CODE REPLICATE TEXT


    c.pack()
    
    def on_select(event):
        x = (event.x/20)-1
        y = (event.y/20)-1

        if x > -1 and y > -1 and x < ft.NCOL and y < ft.NROW:
        
            if (y,x) not in selected:
            
                selected.append((y,x))
            

                h = c.create_oval([(x+1)*20, (y+1)*20, (x+1)*20+20, (y+1)*20+20], fill=colors[counter%len(colors)], tags='blah')
                print c.gettags(h)
                

            else:
                selected.remove((y,x))
                c.delete(CURRENT)
    
    c.bind("<Button-1>", on_select)



    def replicate():
        global counter
        if selected not in replicates and len(selected)!=0:
            replicates.append(selected[:])

        replicatetext = 'Replicates:\n'
        for i in replicates:
            wells=''

            if len(i)>1:
                
                for w in i:
                    wells+=(ft.number_to_well(w)+' ')
                    
            else:
                
                    wells = ft.number_to_well(i[0])
                
                
            replicatetext+=(wells+'\n')

        
        v.set(replicatetext)
        selected[:]=[]
        counter+=1
        
        #c.delete('oval')

    replicate_button = Button(topRightFrame, text="Make Replicate", fg="blue", command = replicate)
    replicate_button.pack()

    def auto_replicate(height, width, end):
        numreps = (ft.NROW / height) * (ft.NCOL / width) - end
        topcorner = [0,0]

        while numreps > 0:

            for x in range(topcorner[0],topcorner[0]+width):
                for y in range(topcorner[1],topcorner[1]+height):
                    if topcorner[0]+width<=ft.NCOL and topcorner[1]+height<=ft.NROW:
                        selected.append((y,x))
                        c.create_oval([(x+1)*20, (y+1)*20, (x+1)*20+20, (y+1)*20+20], fill=colors[counter%len(colors)], tags=str(counter))
                    else:
                        pass
                    
            replicate()
            
            numreps -= 1
            
            if topcorner[0]+width < PLATE_COLS:
                topcorner[0]=topcorner[0]+width
            else:
                topcorner[0]=0
                topcorner[1]=topcorner[1]+height
            
    def auto_replicate_window():
        top = Toplevel()
        top.title("Set Replicate Size")

        var_height = StringVar()
        var_width = StringVar()
        var_end = StringVar()

        heightEntry = Entry(top, textvariable=var_height, width=3)
        heightEntry.grid(row=1)
        heightEntry.focus_set()
        var_height.set('2')
        
        widthEntry = Entry(top, textvariable=var_width, width=3)
        widthEntry.grid(row=3)
        widthEntry.focus_set()
        var_width.set('1')

        endEntry = Entry(top, textvariable=var_end, width=3)
        endEntry.grid(row=5)
        endEntry.focus_set()
        var_end.set('0')

        titleHeight = Label(top, text="Height")
        titleHeight.grid(row=0)

        titleWidth = Label(top, text="Width")
        titleWidth.grid(row=2)

        titleEnd = Label(top, text="Blank Replicates at the End")
        titleEnd.grid(row=4)

        def cancel():
            top.destroy()
        
        def close():
            try:
                height = int(heightEntry.get())
                width = int(widthEntry.get())
                end_dist = int(endEntry.get())
                top.destroy()
                auto_replicate(height, width, end_dist)
            
                
                
            except ValueError:
                tkMessageBox.showerror('Value Error','All Entries Must Be Integers')
                

            
        
        proceed = Button(top, text="OK", command=close)
        proceed.grid(row = 6, column=1)

        cancelButton = Button(top, text="Cancel", command=cancel)
        cancelButton.grid(row=6, column=0)

    auto_replicate_button = Button(topRightFrame, text="Auto Replicate", fg="blue", command = auto_replicate_window)
    auto_replicate_button.pack()
    
    def undo():
        global counter
        counter-=1
        c.delete('blah')
        
        try:
            replicates.pop()
            print 'popped'
            print len(replicates)
            replicatetext = 'Replicates:\n'
            for i in replicates:
                well=''

                if len(i)>1:
                
                    for w in i:
                        well+=(ft.number_to_well(w)+' ')
                    
                else:
                
                    well = ft.number_to_well(i[0])
                
                
                replicatetext+=(well+'\n')
            

                v.set(replicatetext)            
            
        except IndexError:
            pass

        
       

    
    
    undo_button = Button(topRightFrame, text = "Undo", fg="red", command = undo)
    undo_button.pack()

    #w = Message(topRightFrame, textvariable=len(v))
    #w.pack()
    
    var_indivrep = IntVar() 
    indiv_rep_button = Checkbutton(topRightFrame, text="Treat Unused Individuals as Replicates", variable=var_indivrep)
    indiv_rep_button.pack()

    var_barplot = IntVar() 
    indiv_barplot = Checkbutton(topRightFrame, text="Make Barplots", variable=var_barplot)
    indiv_barplot.pack()

    var_plateplot = IntVar()
    indiv_plateplot = Checkbutton(topRightFrame, text="Make Plateplot", variable = var_plateplot)
    indiv_plateplot.pack()

    var_replicateplot = IntVar()
    rep_rawplot = Checkbutton(topRightFrame, text="Plot Raw Data by Replicate", variable = var_replicateplot)
    rep_rawplot.pack()

    image = Image.open('flipperlogo.png')
    image = image.resize((50, 50), Image.ANTIALIAS) #The tuple of integers is (height, width)
    logo = ImageTk.PhotoImage(image)
    Label(master, image=logo).pack(side=TOP)
    
    def advance():
        global SCREEN
        global indiv_as_rep
        global barplot
        global plateplot
        global repplot
        SCREEN+=1

        #set states of checkbox variables
        indiv_as_rep = var_indivrep.get()
        barplot = var_barplot.get()
        plateplot = var_plateplot.get()
        repplot = var_replicateplot.get()
        
        master.destroy()
    
    next_button = Button(bottomFrame, text="OK", fg = "green", command = advance)
    next_button.pack()

    
    
    def showxy(event):
        alph = list('ABCDEFGHIJKLMNOPQRSTUV')
        xm, ym = event.x//20-1, event.y//20-1
        if xm > -1 and ym > -1 and xm < ft.NCOL and ym < ft.NROW:
            c = alph[ym]
            r = xm+1
            str1 = "Mouse at %s %d" % (c, r)
        else:
            str1 = "Select Replicates"
        # show cordinates in title
        master.title(str1)

        
        
        


    def leave(event):
        str1 = "Select Replicates"
        master.title(str1)
        
    #hover display
    c.bind("<Motion>", showxy)
    c.bind("<Leave>", leave)
    
    

    
    mainloop()
    



##############
#Third Screen#
##############



#User chooses a filename -- should be an unused string
def ThirdWindow():
    master = Tk()
    master.wm_title("FLIPPER!")
    
    v = StringVar()
    
    title = Label(master, text="Choose a Valid Filename \n For Your Analysis")
    title.grid(row=0)
    
    label1 = Label(master, text=".txt")
    label1.grid(row=01, column=1)
    
    e = Entry(master)
    e.grid(row=01, column=0)
    
    e.focus_set()

    image = Image.open('flipperlogo.png')
    image = image.resize((50, 50), Image.ANTIALIAS) #The (250, 250) is (height, width)
    logo = ImageTk.PhotoImage(image)
    Label(master, image=logo).grid(row=2, column=2)
    
    def callback():
        global ANALYSIS_NAME
        global message
        ANALYSIS_NAME = e.get()
        not_allowed = (None, '', ' ')
        allowed_char = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')+list('abcdefghijklmnopqrstuvwxyz')+list('1234567890-_,.')

        proceed = True

        if ANALYSIS_NAME in not_allowed:
            proceed = False
            v.set("Error: Must contain a string!")
        else:
            
            for char in ANALYSIS_NAME:
                
                if char not in allowed_char:
                    proceed = False
                    v.set("Error: Name must consist of letters, numbers, and -_,. only!")
                    break
                
        #ensure that filename is not already in use
        try:
            with open(ANALYSIS_NAME+'.txt', 'r'):
                proceed = False
                v.set("Error: File Name Already in Use!")
                
        except IOError:
            pass
        
        if proceed == True:

            if barplot:
                ft.replicatePlot(reps, ANALYSIS_NAME+'_barplot')
                
            if plateplot:
                ft.tilePlot(indivs, ANALYSIS_NAME+'_plateplot')
            if repplot:
                for r in reps:
                    ft.plotAllIndivs(r, ANALYSIS_NAME+'_repplot')

                
            #write to file
            ANALYSIS_NAME+='.txt'
            master.destroy()
            fo = open(ANALYSIS_NAME, 'w')
            fo.write('Wells'+'\t'+'MeanDiff'+'\t'+'StdErr'+'\t'+'Normalized MeanDiff'+'\t'+'Difference of Maxima'+'\t'+'Normalized Difference of Maxima'+'\t'+'StandardDev'+'\t'+'Mean Before'+'\t'+'Mean After'+'\n')
            for r in reps:
                    fo.write('\n')
                    fo.write(r.name+'\t')
                    fo.write(str(r.meanMeanDiff())+'\t')
                    fo.write(str(r.combinedStdError())+'\t')
                    fo.write(str(r.normmeanMeanDiff())+'\t')
                    fo.write(str(r.diffofMaxima())+'\t')
                    fo.write(str(r.combineddiffMaxNormalized())+'\t')
                    fo.write(str(r.combinedStdevSimple())+'\t')
                    fo.write(str(r.meanBef())+'\t')
                    fo.write(str(r.meanAft())+'\t')
                    
            fo.close()

            
            
    b = Button(master, text="Enter", width=10, command=callback)
    b.grid(row=2)

    error = Label(master, textvariable = v)
    error.grid(row=3)


    
    mainloop()



############
#Main Loops#
############

SCREEN = 0

if SCREEN==0:
    StartWindow()

while SCREEN == 1:
    if ft.NCOL>12 or ft.NROW > 8:
        PLATE_FORMAT = 384
        SCREEN+=1
    elif ft.NCOL>8 or ft.NROW > 6:
        PLATE_FORMAT = 96
        SCREEN+=1
    elif ft.NCOL == 8 and ft.NROW == 4:
        PLATE_FORMAT = 96
        SCREEN+=1
    else:
        root=Tk()
        window=PlateFormatWindow(root)
        root.mainloop()

if PLATE_FORMAT == 48:
    PLATE_ROWS = 6
    PLATE_COLS = 8
elif PLATE_FORMAT == 96:
    PLATE_ROWS = 8
    PLATE_COLS = 12
else:
    PLATE_ROWS = 16
    PLATE_COLS = 24

if SCREEN == 2:
    SecondWindow()


reps = ft.replicateMaker2(indivs, replicates, indiv_as_rep)



if SCREEN==3:
    ThirdWindow()