#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sorting mp3s on a basic level regarding genres
    by subdiff, https://github.com/subdiff/mp3GenreSortierer
    For the id3 reader stuff thanks to Ned Batchelder (http://nedbatchelder.com/code/modules/id3reader.html)
"""

import os, sys, subprocess, getopt, string, littleid3reader
import shutil, time

configwelcome = """# This is the config file of the mp3GenreSortierter (it is german for \"mighty mp3 sorter of genres\", but you knew that).
# The config file needs to be in the following format:
#########
### My genres: "Hip - Hop" House Volksmusik
### 
### Subgenres per genre:
### Hip - Hop: Rap "Trap" R&B 'Hip - Hop'
### House: Techno "Acid Jazz" 'Club - House'
### Volksmusik: "Heavy Metal ;)" Marschmusik
#########
# Rules: - Separate with single or double quotation marks or with empty space (if word is without emtpy spaces).
#  - Subgenres are arbitrary genres, you can find in the id3 tags of your files.
#  - Custom genres in first line are arbitrary, but become foldernames (so better not choose any bad characters on your system).
#
#
#
#

My genres: 

Subgenres per genre:
"""

#List of all id3 (sub)genres
"""id3genres = [
    # 0-19
    'Blues', 'Classic Rock', 'Country', 'Dance', 'Disco', 'Funk', 'Grunge', 'Hip - Hop', 'Jazz', 'Metal',
    'New Age', 'Oldies', 'Other', 'Pop', 'R&B', 'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
    # 20-39
    'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack', 'Euro - Techno', 'Ambient', 'Trip - Hop', 'Vocal', 'Jazz + Funk',
    'Fusion', 'Trance', 'Classical', 'Instrumental', 'Acid', 'House', 'Game', 'Sound Clip', 'Gospel', 'Noise',
    # 40-59
    'Alt Rock', 'Bass', 'Soul', 'Punk', 'Space', 'Meditative', 'Instrumental Pop', 'Instrumental Rock', 'Ethnic', 'Gothic',
    'Darkwave', 'Techno - Industrial', 'Electronic', 'Pop - Folk', 'Eurodance', 'Dream', 'Southern Rock', 'Comedy', 'Cult', 'Gangsta Rap',
    # 60-79
    'Top 40', 'Christian Rap', 'Pop / Funk', 'Jungle', 'Native American', 'Cabaret', 'New Wave', 'Psychedelic', 'Rave', 'Showtunes',
    'Trailer', 'Lo - Fi', 'Tribal', 'Acid Punk', 'Acid Jazz', 'Polka', 'Retro', 'Musical', 'Rock & Roll', 'Hard Rock',
    # 80-99
    'Folk', 'Folk / Rock', 'National Folk', 'Swing', 'Fast - Fusion', 'Bebob', 'Latin', 'Revival', 'Celtic', 'Bluegrass',
    'Avantgarde', 'Gothic Rock', 'Progressive Rock', 'Psychedelic Rock', 'Symphonic Rock', 'Slow Rock', 'Big Band', 'Chorus', 'Easy Listening', 'Acoustic',
    # 100-119
    'Humour', 'Speech', 'Chanson', 'Opera', 'Chamber Music', 'Sonata', 'Symphony', 'Booty Bass', 'Primus', 'Porn Groove',
    'Satire', 'Slow Jam', 'Club', 'Tango', 'Samba', 'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
    # 120-139
    'Duet', 'Punk Rock', 'Drum Solo', 'A Cappella', 'Euro - House', 'Dance Hall', 'Goa', 'Drum & Bass', 'Club - House', 'Hardcore',
    'Terror', 'Indie', 'BritPop', 'Negerpunk', 'Polsk Punk', 'Beat', 'Christian Gangsta Rap', 'Heavy Metal', 'Black Metal', 'Crossover',
    # 140-147
    'Contemporary Christian', 'Christian Rock', 'Merengue', 'Salsa', 'Thrash Metal', 'Anime', 'JPop', 'Synthpop'
    ]  """ 

#TODO: Fehler beim Eintragen der Subgenres beseitigen -> DONE?
#TODO: Singlelisten und Folderlisten vor dem Bearbeiten alphabetisch anordnen! -> DONE?
#TODO: Wartezeit vor dem Bestätigen des Verschieben eines Ordners -> DONE?
#TODO: Try-Klammer um id3 reader -> DONE?
#TODO: Keine Unterscheidung von Groß-Klein-Schrift bei Genres -> DONE?
#TODO: Ordner manuell kopieren -> DONE?
#TODO: Target genres komplett im Programm editierbar machen
#TODO: Genreeingaben für alle Genres und entscheidbar machen ob immer verknüpfen (Standard: Nein) FEINTUNING


class Genre(object):
    'User genres, which represent single folders at the end where all the music moves.' 
    # List of all user genres
    genrelist=[]
#    genrenamelist=[]
    
    def __init__(self, genrename="Default"):
        for g in Genre.genrelist:
            if genrename == g.getgname():
                print "The genre %s was already specified. Please use another name." %(genrename)
                return
        self._subgenres=[] #Official id3 genres, which the user want to join
        self._gname=genrename
        self._initmygenre()
        self._readsubgenres()
      
    def _initmygenre(self):
        """ Additional initializing of the genrelist and the config file"""
        self.genrelist.append(self)
        self.genrelist.sort(key= lambda g: (g.getgname().lower(), g.getgname()[0].islower()) )
        data = self._readconfig()
        for line in data:
            if line.startswith("My genres:"):
                #words = getWords(line.lstrip("My genres: "))
                words = getWords(line[len("My genres:"):])
                if not any(self._gname in s for s in words):
                    words.append(self._gname)
                words.sort(key= lambda w: (w.lower(), w[0].islower()) )
                data[data.index(line)]= "My genres: " + writeLine(words)
                self._writeconfig(data)
        # Now update the subgenre section
        data = self._readconfig()
        substartindex, searchingbegin= 0, True
        for line in data:
            if line.startswith("Subgenres per genre:"):
                searchingbegin=False
            if searchingbegin:
                substartindex+=1
            else:
                sline=line
                if sline.lstrip("'\"").startswith(self._gname):
                    return
        mygenreindex=self.genrelist.index(self)
        data.insert(substartindex+1+mygenreindex, "'"+self._gname +"':\n")
        self._writeconfig(data)
    def _readsubgenres(self):
        data = self._readconfig()
        i=0
        searchingbegin=True
        for line in data:
            if line.startswith("Subgenres per genre:"):
                searchingbegin=False
            if not searchingbegin:
                sline = line
                if sline.lstrip("'\"").startswith(self._gname):
                    # getting the preconfigured subgenres from configfile
                    words = getWords(line[len(self._gname)+3:])
                    for word in words:
                        if not any(word in s for s in self._subgenres):
                            self._subgenres.append(word)
                    self._subgenres.sort(key=lambda w: (w.lower(), w[0].islower()))
                    # writing back the subgenres in alphabetic order
                    data[i]="'"+self._gname+"': " + writeLine(self._subgenres)
                    self._writeconfig(data)
            i+=1
        
    def addsubgenre(self, subgenre=""):
        """Adds new subgenre to Class list and config file or if subgenre="", only
        writes the Subgenre line in config file"""
        if not subgenre=="":
            self._subgenres.append(subgenre)
            self._subgenres.sort(key=lambda w: (w.lower(), w[0].islower()))
        data=self._readconfig()
        i=-1
        for line in data:
            i+=1
            if line.replace('"', "").replace("'", "").startswith(self._gname +":"):
                data[i]= "'" + self._gname + "': " + writeLine(self._subgenres)
        self._writeconfig(data)
        
    def compSubgenres(self, subgenre):
        """ Compares the associated id3 genres of self with the other subgenre"""
        for subg in self._subgenres:
            if subgenre.replace(' ','') == subg.replace(' ',''):
                return True
        return False
    def getgname(self):
        return self._gname
    def _readconfig(self):
        try:
            genrefile=open(configfilepath, "r")
        except:
            print "Could not read \"%s\". Aborting." % (configfilepath)
            sys.exit(-1)
        data = genrefile.readlines()
        genrefile.close
        return data
    def _writeconfig(self, data):
        try:
            genrefile=open(configfilepath, "w")
        except:
            print "Could not write to \"%s\". Aborting." % (configfilepath)
            sys.exit(-1) 
        genrefile.writelines(data)
        genrefile.close
 

def getWords(line):
    "Function for getting separate words of lines in config file"
    sline=line.strip()
    words=[]
    wordstart = True
    withsep = False
    i=-1
    if sline=="":
        return words
    for c in sline:
        if wordstart and isSep(c):
            i += 1
            words.append("") # This means: words[i]=""
            wordstart=False
            withsep=True
        elif wordstart:
            if not c==' ': # Ignoring Empty Spaces between with isSep separated words
                i +=1
                words.append(c) # This means: words[i]=c
                wordstart=False
                withsep=False
        elif withsep:
            if not isSep(c):
                words[i]+=c
            else:
                if words[i].replace(' ','')=="":
                    words.pop()
                    i=i-1
                wordstart=True
        elif not withsep:
            if not c==' ':
                words[i]+=c
            else:
                wordstart=True
    return words                
def writeLine(words):
    "From a list of words write the config lines behind genre or the subgenres"
    if words==[]:
        return '\n'
    line=""
    for word in words:
        line += "'" + word + "' "
    return line[:-1] + '\n'
                
    
# String Separator in config file
def isSep(sep):
    if sep=="'" or sep=="\"":
        return True
    else:
        return False
    
def UserInputHandler(transformfct=str, acceptlist=[], openingstr="", repeatstr="", cancellist=[], defaultstr=None):
    "Helper function for getting textual input from user"
    begin=True
    userinput=None
    while True:
        if begin:
            begin=False
            userinput=raw_input(openingstr)
        else:
            userinput= raw_input(repeatstr)
        if userinput==None:
            print "Critical error in UserInputHandler. Received 'None'! Aborting program."
            sys.exit(-1)
        if userinput in cancellist:
            return None
        if userinput==defaultstr:
            return defaultstr
        try:
            userinput=transformfct(userinput)
        except:
            userinput=None
            continue
        if userinput in acceptlist:
            return userinput
    
def WorkOnRootFolder():
    "Analyze and copy items in the folder on top of the hierarchy (workingpath)"
    folderlist, singlelist = [], []
    for file in os.listdir(workingpath):
        filepath=workingpath+os.sep+file
        if os.path.isdir(filepath):
            if filepath not in [workingpath, copyroot]: 
                folderlist.append(file)
        elif file.endswith(".mp3"):
            singlelist.append(file)
    singlelist.sort(key=lambda w: (w.lower(), w[0].islower()))   
    folderlist.sort(key=lambda w: (w.lower(), w[0].islower()))
    userinputallowed=True
    for single in singlelist:
        starget= SingleTarget(workingpath+os.sep+single,single, userinputallowed)
        if starget==1:
            userinputallowed=False
        else:
            CopySingleton(single, starget) # Search for target of single and copy it
    for folder in folderlist:
        time.sleep(0.5)
        print "######################################################"
        print "######################################################"
        mode=UserInputHandler(int, range(1,4),
                              "Please choose for folder '%s':\n(1) Select target now (2) Analyse content (3) Skip folder (b) Quit: " %folder, 
                              "Please select '1', '2' or '3': ",
                              ['b','B'])
        if not mode:
            print "### Exited on user behalf."
            sys.exit()        
        if mode==1:
            openingstr= "############\nCustom genres:\n"
            for i,g in enumerate(Genre.genrelist):
                openingstr += "("+str(i+1)+") " + g.getgname()+"\n"
            openingstr += "############\nSpecify target: "
#            print range(1, len(Genre.genrelist)+1)
            genre= UserInputHandler(int, range(1, len(Genre.genrelist)+1), 
                                    openingstr, 
                                    "Please type a number between '1' and '" + str(len(Genre.genrelist))+"': ", 
                                    )
            destpath=copyroot+os.sep+Genre.genrelist[genre-1].getgname()
            print "Now copying folder '" + folder + "' to '" + destpath + "'. This may take a while..."
            RecursiveCopyFolder(folder, workingpath, destpath , [workingpath])
        elif mode==2:
            InitiateAnalyzedFolderCopy(folder,FolderTarget(workingpath+os.sep+folder, folder))
        else:
            print "Warning: Skipping Folder '%s'." %folder
            continue
            
def SingleTarget(filepath, file, userinputallowed=True):
    "Tries to find custom genre target of file. If miss, call SubgenreUserInput"
    print "######################################################"
    print "# %s:" %file
    try:
        id3r = littleid3reader.Reader(filepath)
        filegenre = id3r.getValue('genre')
    except:
        print "### Could not read id3 genre from file. ###"
        filegenre=None
    subgenre=None
    #subgenrefound=False
    if filegenre:
        sfilegenre = filegenre.replace(' ','').replace('-','').lower()
        subgenre = filegenre
    else:
        print "### No genre value in File. ###" ,
        if userinputallowed:
            return SubgenreUserInput(subgenre, filepath)
        else:
            print "--> User input omitted!"
            return None
    if sfilegenre.startswith("("):# and filegenre.endswith(")"):
        #filegenre=filegenre.strip('()')
        sfilegenre= sfilegenre[1:]
        ssfilegenre=""
        for c in sfilegenre:
            if c==')':
                break
            ssfilegenre += c
        try:
            ssfilegenre=int(ssfilegenre)
            subgenre=littleid3reader._genres[ssfilegenre]
            print "### Genre in file: %s ###" % subgenre ,
        except:
            print "### Genre in file: %s ###" % filegenre ,
            subgenre=filegenre
    else:
        print "### Genre in file: %s ###" % filegenre ,
        for id3g in littleid3reader._genres:
            if id3g.replace(' ','').replace('-','').lower() == sfilegenre:
                subgenre=id3g
                #subgenrefound=True
                break
    #if subgenrefound==True:
    if subgenre:
        for genre in Genre.genrelist:
            if genre.compSubgenres(subgenre):
                print "--> Assigned to custom genre '%s'." %(genre.getgname())
                return genre
    if userinputallowed:
        return SubgenreUserInput(subgenre, filepath)
    else:
        print ""
        return None
           
def SubgenreUserInput(subgenre, song):
    "In case this will give user oportunity to specify genre manually"
    saveallowed=True
    #if isid3:
        #print "Target for file with id3 genre '%s'?" %(subgenre),
    #    print ("('#': Selection '#s': Save selection 'E': Skip this file 'B': Quit)")
    #else:
    if subgenre=="" or subgenre==None:
        #print "Target with no genre in file?" ,
        print ("('#': Select 'f': Play song 'e': Skip song 'r': Ignore next inputs 'b': Quit)")
        saveallowed=False
    else:
        print ("('#': Select '#s': Select + save 'f': Play song 'e': Skip song 'r': Ignore next inputs 'b': Quit)")
    genresel=""
    i=1
    for genre in Genre.genrelist:
        genresel+= "("+ str(i) + ") " + genre.getgname() + " "
        if i%2==0:
            genresel = genresel[:-1]
            genresel += '\n'
        i+=1
    genresel = genresel[:-1] + ": "
    settemp = True
    begin=True
    while settemp == True:
        if begin:
            sel=raw_input(genresel)
            sel=sel.strip()
            begin=False
        if sel.lower()=="f":
            PlaySong(song)
            sel=raw_input("Started external player. Please choose now again: ")
            continue
        if sel.lower()=="e":
            print "Warning: Skipped this file!"
            #settemp=False
            return None
        if sel.lower()=="r":
            print "Warning: No more user inputs have been allowed in this folder!"
            return 1
        if sel.lower()=="b":
            print "Exited on user behalf."
            sys.exit()
        savesel=False
        if len(sel)==2:
            savesel=True
            if saveallowed:
                if not sel[1].lower()=='s':
                    sel=['0',""]
        if len(sel)>2:
            sel=['0',""]
        if len(sel)==1:
            sel=[sel[0],""]
        try:
            sel=[int(sel[0]),sel[1]]
        except:
            sel=[0,""]
        if 1<= sel[0] <= len(Genre.genrelist):
            settemp=False
            if savesel:
                if saveallowed:
                    Genre.genrelist[sel[0]-1].addsubgenre(subgenre) # New subgenre to custom genre
                    print "Saved assignment: '"+subgenre+"' => '"+Genre.genrelist[sel[0]-1].getgname()+"'."
                else:
                    print "No genre in file to link to custom genre '%s', but selected this for copying the file." %Genre.genrelist[sel[0]-1].getgname()
                time.sleep(0.5)
            return Genre.genrelist[sel[0]-1]
        else:
            sel= raw_input("Please choose '1' till '%i' (with optional 's' afterwards), 'f' to listen to the song or 'e' to skip, 'b' to quit: "  % len(Genre.genrelist))

def CopySingleton(file, mygenre):
    "Copies single singeltons in workingdirectory"
    if mygenre:
        destpath = copyroot +os.sep+ mygenre.getgname() #+ '/'
        filepath = workingpath+os.sep+file
        if os.path.exists(destpath+os.sep+file):
            print "Warning: File exists already. Copying skipped."
            return
#            if not raw_input("File exists already. Overwrite? Answer (Y/N, standard: N): ") in ['y', 'Y']:
#                print "NOT overwriting %s. Skipping." %file
#                return
        try:
            shutil.copy2(filepath, destpath)  
        except shutil.Error as e:
            print('Copy-Error: %s' % e)
            return
        except IOError as e:
            print('Copy-Error2: %s' % e.strerror)
            return
        print "Copied file \"%s\" to \"%s\"." %(file, destpath)
        
def FolderTarget(folderpath, folder, inputsallowed=True):
    """Goes through all mp3 and recursively through all subfolders in folder
    and returns how many genres are here"""
    print "######################################################"
    print "Analyzing '..." + folderpath[len(workingpath):] + "'"
    filelist = os.listdir(folderpath)
    folderlist, singlelist = [], []
    glist = [[None, 0]]
    for usergenre in Genre.genrelist:
        glist.append([usergenre, 0])
    for file in filelist:
        if os.path.isdir(folderpath+os.sep+file):
            folderlist.append(file)
        elif file.endswith(".mp3"):
            singlelist.append(file)
    singlelist.sort(key=lambda w: (w.lower(), w[0].islower()))   
    folderlist.sort(key=lambda w: (w.lower(), w[0].islower()))
    #skiprest=False
    for s in singlelist:
        sgenre=SingleTarget(folderpath+os.sep+s,s, inputsallowed)
        if sgenre==1:
            inputsallowed=False # Skipping the user input for the rest of files and folders in this folder.
        for g in glist:
            if g[0]==sgenre:
                g[1]+=1
    rangeglist = range(len(glist))   # Losing some efficiency here!  
    #if not skiprest:       
    for f in folderlist:
        fglist = FolderTarget(folderpath+os.sep+f, f, inputsallowed)
        for i in rangeglist:
            glist[i][1]+=fglist[i][1]
    return glist

def InitiateAnalyzedFolderCopy(folder, glist):
    "If folder content gets analyzed, this is its first function (glist comes from FolderTarget!)"
    ignorelist=[workingpath, copyroot]
    glist.sort(key=lambda x: x[1], reverse=True)
    print "######################################################"
    print "######################################################"
    print "Found in folder '" + folder + "' mp3s with the following counts of mappings to your custom genres:"
    noneindex=0
    j=0
    #for g in glist:
    #    if g[0]==None:
    #        noneindex=glist.index(g)
    #        break
    for i in range(len(glist)):
        j+=1
    #    if i>=5 and glist[i][1]==0 and glist[0][1]>0:
    #        j=j-1
    #        break
        if glist[i][0]==None:
            noneindex=i
            j=j-1
        else:
            print "("+str(j)+") "+ glist[i][0].getgname() + ": " + str(glist[i][1])
    print "Songs with no mapping: " + str(glist[noneindex][1])
    time.sleep(1)
    string = "Where should this folder go? Recommending "
    if glist[0][1]== 0 or (glist[0][0]==None and glist[1][1]== 0):
        defstring=None
        string=string + "nothing. Choose number from above or skip folder with 'e'."
    else:
        defstring=""
        if glist[0][0]==None:
            string=string + "(1) '" + glist[1][0].getgname()+"'"
        else:
            string=string + "(1) '" + glist[0][0].getgname()+"'"
        string = string + " (for this press Enter, select other genre or skip folder with 'e')."
    print string
    #waitonuser=True
    #sel, isel = "", 0
    skip=False
    
    sel=UserInputHandler(int, acceptlist=range(1,j+1),
                         openingstr="My selection: ",
                         repeatstr="Please use a value between 1 and " + str(j) + " or skip with 'e'.",
                         cancellist=['e','E'],
                         defaultstr=defstring)
    if sel==None:
        skip=True
        #waitonuser=False
    elif sel=="":
        #waitonuser=False
        isel=1
    else:
        isel=sel
    if skip:
        print "Warning: Skipped this folder!"
        return
    else:
        if noneindex >= isel:
            isel=isel-1
        #if noneindex<=isel:
        #    isel += 1
        #for i in range(isel):
        #    if glist[i][0]== None:
        #        nonebevor=True
        destpath=copyroot+os.sep+ glist[isel][0].getgname()
        print ""
        print "+++ Copying folder '" + folder + "' to '" + destpath + "'. This may take a while..."
        print ""
        RecursiveCopyFolder(folder,workingpath, destpath,ignorelist)

def RecursiveCopyFolder(folder, srcpath, destpath, ignorelist):
    "Simple recursive copy of folders. Folders get intigrated and already existing files will NOT get replaced."
    srcpath=os.path.abspath(srcpath)
    destpath=os.path.abspath(destpath)
    if srcpath not in ignorelist:
        ignorelist.append(srcpath)
    #charcount=0
    destfolderpath=destpath+os.sep+folder
    srcfolderpath=srcpath+os.sep+folder
    print "+++ Now recursive copy is working in\n'%s' +++" %srcfolderpath
    try:
        os.mkdir(destfolderpath)
        string = "Folder '" + folder + "' created: "
        #charcount += len(string)
        print string
    except:
        if os.path.isdir(destfolderpath) and not os.path.islink(destfolderpath):
            print "+ Using the existing folder '" + destfolderpath + "'. +"
            #charcount += len(string)
            #print string
        else:
            print "+++ Warning: Target folder does not exists and there was an error while trying to create this folder:\n'"+ folder + "'.\nSkipping to next folder. +++"
            return
    sys.stdout.flush()
    filelist=[]
    dirlist=[]
    for file in os.listdir(srcfolderpath):
        if os.path.isdir(srcfolderpath+os.sep+file) and not os.path.islink(destfolderpath):
            dirlist.append(file)
        else:
            filelist.append(file)
    filelist.sort(key=lambda w: (w.lower(), w[0].islower()))
    dirlist.sort(key=lambda w: (w.lower(), w[0].islower()))
    for file in filelist:
        #if charcount > 50:
        #    print "..."
        #    charcount=0
        if os.path.exists(destfolderpath+os.sep+file):
            print "Warning: '%s' exists already. Copying skipped." %file
            continue
        try:
            shutil.copy2(srcfolderpath+os.sep+file,destfolderpath+os.sep+file)
            print "Copied: '" + file +"'. "
        except shutil.Error as e:
            print ""
            print("!!!!!! Copy-Error1: %s" % e)
            print ""
            #charcount=0
        except IOError as e:
            print ""
            print('!!!!!! Copy-Error2: %s' % e.strerror)
            print ""
            #charcount=0
    sys.stdout.flush()
    print ""
    for fold in dirlist:
        RecursiveCopyFolder(fold, srcfolderpath, destfolderpath, ignorelist)

def CreateFolders():
    "On startup, if necessary, makes folders for output"
    try:
        os.mkdir(copyroot)
        print "Created destination folder '" + copyroot + "'."
    except:
        if os.path.isdir(copyroot):
            print "### Found folder '"+ copyroot +"'.\nUsing this as destination folder."
        else:
            print "Error creating the destination folder \"%s\". Sufficient user rights? Aborting." % copyroot
            sys.exit(-1)
    time.sleep(1)
    for genre in Genre.genrelist:
        genrefolder = copyroot + os.sep + genre.getgname()
        try:
            os.mkdir(genrefolder)
            print "Created Custom Genre folder \'%s\'" %genrefolder
        except:
            if os.path.isdir(genrefolder):
                print "### Custom genre folder '"+ genre.getgname() + "' found. Using this folder."
                time.sleep(0.2)
            else:
                print "Genre \"%s\": Can not create folder \"%s\". Sufficient user rights? Aborting." % (genre.getgname(), genrefolder)
                sys.exit(-1)
        time.sleep(0.3)

def StartupConfig():
    "When starting the programm do some common checks and create if necessary the needed files and folders."
    print "### Working in \"%s\"." % (workingpath)
    #TODO: Change workingpath to selection of it
    time.sleep(1)
    if os.path.exists(configfilepath):
        try:
            print "Found '%s'. Using this file for configuration. Otherwise abort in next step!" % (configfilepath)
            configfile=open(configfilepath, "r")
        except:
            print "Error initial opening \"%s\" in Read Mode. Aborting." % (configfilepath)
            sys.exit(-1)
        configfile.close      
    else:
        try:
            print "Config file '%s' does not exist. Creating..." % (configfilepath)
            configfile=open(configfilepath, "w")
            configfile.write(configwelcome)
        except:
            print "Error creating config file \"%s\". Aborting." % (configfilepath)
            sys.exit(-1)
        configfile.close  
        print "Created config file. Please specify now your target genres in this file and restart the program."
        sys.exit()
    # Initial generating genres from file
    try:
        configfile=open(configfilepath, "r")
    except:
        print "Error opening \"%s\" in Read Mode. Aborting." % (configfilepath)
        sys.exit(-1)
    # Reading in genres from the correct line in configfile
    line=""
    for lines in configfile:
        if lines.startswith("My genres: "):
            line+=lines
            break
    if line=="":
        print "No line with 'My genres:' in '%s'.\nFile is  not in right format! Aborting." % (configfilepath)
        sys.exit(-1)
    # Cutting away "My genres: "
    genres=getWords(line[11:])
    if genres==[]: 
        print "No genres in config file '%s'.\nPlease specify these first in the config file." %(configfilepath)
        sys.exit(1)
        #CustomGenreStartupEditor()
    print "### Found following target genres in config file: " + writeLine(genres)[:-1]
    editgenres=UserInputHandler(acceptlist=['','y','Y','n','N'],
                                openingstr="Is this ok ('Y'/'n')?: ",
                                repeatstr="Please type 'y', 'n' or hit Enter.")
    #editgenres=raw_input("Is this ok ('Y'/'n')?: ")
    if editgenres.lower() == "n":
        print "In this case please edit your target genres in config file and restart the program."
        sys.exit(-1)
    for g in genres:
        Genre(g)
    configfile.close
    

def PlaySong(song):
    """Plays song in systems standard player"""
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', song))
    elif os.name == 'nt':
        os.startfile(song)
    elif os.name == 'posix':
        try:
            subprocess.call(('xdg-open', song))
        except:
            return


#def CustomGenreStartupEditor(genrelist=None):
    
def main(argv):
    """Reads command line options '-i <inputpath>' '-o <outputpath>' '-c <configpath>', else it uses standards:
       workingpath = <current working directory>,
       copyroot = <workingpath/../mp3GenreSortiererOutput>,
       configpath = <path of script>
    """
    global workingpath, copyroot, configfilepath
    
    infostring = """mp3GenreSortierer -i <inputpath> -o <copypath> -c configpath
    Standards are: inputpath = <current working directory>,
                   outputpath = <inputpath/mp3GenreSortiererOutput>,
                   configpath = <scriptpath>
    Option '--help' for more information (in later versions)."""
    
    try:
        opts, args = getopt.getopt(argv,"i:o:c:",["help","inputpath","outputpath","configpath"])
    except getopt.GetoptError:
        print infostring
        sys.exit(2)
    for opt, arg in opts:
        if opt == '--help':
            print infostring
            sys.exit()
        elif opt in ("-i", "--inputpath"):
            try:
                workingpath = os.path.abspath(arg)
            except:
                print "The provided inputpath is no valid path to a directory."
                sys.exit(-1)
        elif opt in ("-o", "--outputpath"):
            try:
                copyroot = os.path.abspath(arg)
            except:
                print "The provided outputpath is no valid path to a directory."
                sys.exit(-1)
        elif opt in ("-c", "--configpath"):
            try:
                configfilepath = os.path.abspath(arg)+os.sep+configfilename
            except:
                print "The provided configpath is no valid path to a directory."
                sys.exit(-1)


################################# main #################################
configfilename="mp3GenreSortiererConfig"
workingpath = os.path.abspath(os.getcwd())
#configfilepath=workingpath+os.sep+configfilename
configfilepath=sys.path[0]+os.sep+configfilename
copyroot = workingpath + os.sep + "mp3GenreSortiererOutput" # Set Output directory

#workingpath = os.path.abspath(os.getcwd()) # Get current working directory
#configfilepath=workingpath+os.sep+configfilename
#copyroot = os.path.abspath(workingpath +os.sep+ os.pardir + os.sep + "mp3GenreSortiererOutput") # Set Output directory

if __name__ == "__main__":
    main(sys.argv[1:])
    
#filelist = os.listdir(workingpath)

StartupConfig()

# Creating Copy path folders
CreateFolders()
# Start main work
WorkOnRootFolder()

print "### No more songs to sort for you. End of programm. Have a nice day. ###"
############################# end of main #############################


