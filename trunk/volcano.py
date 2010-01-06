import curses
import curses.ascii
import pprint
import random
import copy
import math

DEBUG=True              # Gives extra info on the status line
WIZARDKEYS=True         # ? toggles omniscience, . toggles timefreeze
OMNISCIENT=False        # See everything, hear every message
TIMEFREEZE=False        # Lava and monsters cannot move
GODLYMIGHT=True         # Start with 50 of everything
LAVAMUNITY=False        # Lava does not hurt you
AMNESIA=False           # Don't show previously seen areas
FULLVIEW=False          # LOS is complete, not within 8 squares

DEATHVIEW=False         # True the true state of anything you've seen
DEATHMAGMA=False        # Lava travels fast offscreen when you're dead

lavaspeed = 0.8

programName="Volcano"
programVersion="0.0.5 (beta)"

#initialization
screen=curses.initscr()
curses.start_color()
curses.noecho()
screen.keypad(1)
if curses.has_colors():
    for color in range(8):
        curses.init_pair(color+1, color, curses.COLOR_BLACK)

def color_to_pair(color):
    return color+1
def color_to_attr(col):
        return curses.color_pair(color_to_pair(col))
#color definitions
WHITE = color_to_attr(curses.COLOR_WHITE) + curses.A_BOLD
GRAY = GREY = color_to_attr(curses.COLOR_WHITE)
BOLD_RED = color_to_attr(curses.COLOR_RED) + curses.A_BOLD
RED = color_to_attr(curses.COLOR_RED)
BLUE = color_to_attr(curses.COLOR_BLUE)
BOLD_BLUE = color_to_attr(curses.COLOR_BLUE) + curses.A_BOLD
BROWN = color_to_attr(curses.COLOR_RED) + curses.A_DIM
TAN = color_to_attr(curses.COLOR_YELLOW)
YELLOW = color_to_attr(curses.COLOR_YELLOW) + curses.A_BOLD
GREEN = color_to_attr(curses.COLOR_GREEN)
BOLD_GREEN = color_to_attr(curses.COLOR_GREEN) + curses.A_BOLD
BLACK = color_to_attr(curses.COLOR_BLACK)
ALERT_COLOR = color_to_attr(curses.COLOR_MAGENTA) + curses.A_BOLD

def closescreen():
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()

cursorxpos=cursorypos=1
def updatecursor():
    screen.move(cursorypos, cursorxpos)

def anykey():
    screen.getch()
def update():
    updatecursor()
    screen.refresh()

COLUMNS = 80
LINES = 24

def clearline(line):
    screen.hline(line,0, ord(" "), COLUMNS)

messLines=2
messline=0
messpos=0
morestr=" --more--"
morelen=len(morestr)
def message(str):
    global messline
    global messpos
            
    while (len(str) > 0):
        if(messline == messLines-1):
            charsleft = COLUMNS-morelen-messpos
        else:
            charsleft = COLUMNS-messpos 
        printedchars = min(charsleft, len(str))
        if charsleft > 0:
            screen.addstr(messline, messpos, 
                          str[0:printedchars])
            messpos += printedchars
            str = str[printedchars:]
        else:
            if messline == messLines-1: #more
                screen.addstr(messline, messpos, morestr)
                update()
                anykey()
                screen.addstr(messline, messpos, " "*morelen) #clear 'more'
                messpos=0
                messline = 0
            else:
                messline += 1
            messpos=0
            clearline(messline)
    if (not (((messline==messLines) and (messpos>=COLUMNS-morelen-2))
            or ((messline==0) and (messpos==0)))): 
                #spacing if needed and there's room
        screen.addstr(messline, messpos, "  ")
        messpos += 2

def clearmessage():
    global messpos
    global messline
    messpos=0
    messline=0
    for line in range(messLines):
        clearline(line)

statusLine=LINES-1
def setstatusline(str):
    clearline(statusLine)
    screen.addstr(statusLine, 0, str[0:COLUMNS])

def getkey():
    return screen.getch()
    
class symbol:
    ascii=0
    color=color_to_attr(curses.COLOR_MAGENTA)
    def __init__(self, char, attr=(color_to_attr(curses.COLOR_WHITE) + curses.A_BOLD)):
        if curses.ascii.isascii(char):
            self.ascii=ord(char)
            self.color=attr
        else:
            print "Error in symbol: invalid character or string"

def printsymb(square, symb):
    x,y=square
    if curses.has_colors():
        screen.addch(LINES-y-2, x, symb.ascii, symb.color)
    else:
        screen.addch(LINES-y-2, x, symb.ascii)

mapWidth = COLUMNS
mapHeight = LINES-messLines-1

#define tiles
UNKNOWN = symbol(" ", WHITE)
EMPTY_SPACE = symbol(".", GRAY)
GRASS = symbol(".", GREEN)
WALL = symbol("#", GRAY)
OUTER_WALL = symbol("#", GRAY)
UP_STAIR = symbol("<", WHITE)
DOWN_STAIR = symbol(">", WHITE)
LAVA = symbol(",", RED)
MAGMA = symbol(",", BOLD_RED)
CHAR_SYMB=symbol("@", BOLD_BLUE)
DEAD_CHAR_SYMB=symbol("@", BLUE)
BURNT_CHAR_SYMB=symbol("@", RED)
ERROR_SYMB=symbol("?", ALERT_COLOR)

mapPositions=[(x, y) for x in range(mapWidth) for y in range(mapHeight)]

MAXHP,HP,POINT,TURN,MONEY,FOOD,GEM,WEAPON,ARMOR,POTION,SCROLL = range(11)
itemDict = {
    MAXHP:symbol("@", ALERT_COLOR),
    HP:symbol("#", ALERT_COLOR),
    POINT:symbol("P", ALERT_COLOR),
    TURN:symbol("T", ALERT_COLOR),
    MONEY:symbol("$", YELLOW),
    FOOD:symbol("%", BROWN),
    GEM:symbol("*", ALERT_COLOR),
    WEAPON:symbol("(", GRAY),
    ARMOR:symbol("[", GRAY),
    POTION:symbol("!", BOLD_BLUE),
    SCROLL:symbol("?", WHITE),
}
gemColors = (BOLD_GREEN, BOLD_BLUE, BOLD_RED, WHITE, YELLOW, GRAY)

def itemsymbol(itm):
    if itm=="*":
        return symbol("*", gemColors[(curlevel.depth % len(gemColors))])
    elif itm in itemDict:
        return itemDict[itm]
    else:
        print "Nonexistant item ", itm

def itemscore(item):
    if item==MAXHP:
        return 1
    elif item==HP:
        return 1
    elif item==MONEY:
        return 1
    elif item==FOOD:
        return 1
    elif item==GEM:
        return 2
    elif item==WEAPON:
        return 1
    elif item==ARMOR:
        return 1
    elif item==POTION:
        return 1
    elif item==SCROLL:
        return 3
    else:
        print "Illegal scoring item"
        return 0


monsterDict = {
    "ant": BROWN,
    "bat": BROWN,
    "cat": BROWN,
    "dog": BROWN,
    "emu": WHITE,
    "fay": WHITE,
    "gnu": WHITE,
    "hog": WHITE,
    "imp": WHITE,
    "jin": WHITE,
    "kite": WHITE,
    "lion": WHITE,
    "mara": WHITE,
    "naga": WHITE,
    "ogre": WHITE,
    "pard": WHITE,
    "quip": WHITE,
    "rukh": WHITE,
    "slime": WHITE,
    "troll": WHITE,
    "umbra": WHITE,
    "virus": WHITE,
    "wyvern": WHITE,
    "xenomy": WHITE,
    "ytitne": WHITE,
    "zombie": GRAY,
}

monsterSymbols = {}
monsterNames={}
ZOMBIE=26

monsterSymbols = {}
for name, col in monsterDict.iteritems():
    monsterSymbols[name[0]]=symbol(name[0],col)
monsterNames = {}
for name, col in monsterDict.iteritems():
    monsterNames[name[0]]=name

def monstersymbol(mon):
    if mon in monsterSymbols:
        return monsterSymbols[mon]
    else:
        return symbol(mon)
def monstername(mon):
    if mon in monsterNames:
        return monsterNames[mon]
    else:
        return "ErrorMonsterName"     
def inttomonster(int):
    return monster(chr(int + ord("a") - 1))

class monster:
    hp = 1
    power = 0
    asc=None
    def __init__(self, x):
        self.asc=x
        self.hp=ord(x)-ord("a")+1
        self.power = self.hp
    def name(self):
        return monstername(self.asc)
    def symb(self):
        return monstersymbol(self.asc)
    def alive(self):
        return (self.hp > 0)
    def getHit(self, actor, power):
        self.hp -= max(0,power)
        if actor==hero:
            message("It has " + pprint.pformat(self.hp) + " HP remaining.")
        if not self.alive:
            message("The " + self.name() + " dies.")
            score(actor, 1)
    def prefersX(self):
        return random.choice((True, False))
    def addScore(self, points):
        pass



class level:
    floormap = []
    knownmap = []
    items = {}
    monsters = {}
    stairs = {}
    depth=0
    full=False
    cachedupstair=None
    def __init__(self, depth, stairsup, stairsdown, special):
        #level generation
        self.depth=depth
        #map generation
        self.floormap=[[ERROR_SYMB for x in range(mapWidth)] for y in range(mapHeight)]
        self.knownmap=[[UNKNOWN for x in range(mapWidth)] for y in range(mapHeight)]
        if OUTSIDE in special:
            for x,y in mapPositions:
                #print x,y
                self.floormap[y][x]=GRASS
                self.seen((x,y))
        else:
            #outside walls
            for y in range(mapHeight):
                self.floormap[y][0]=OUTER_WALL
                self.floormap[y][mapWidth-1]=OUTER_WALL
            for x in range(1,mapWidth-1):
                self.floormap[0][x]=OUTER_WALL
                self.floormap[mapHeight-1][x]=OUTER_WALL
                for y in range(1,mapHeight-1):
                    self.floormap[y][x]=WALL
            #Create rooms
            roomTiles = [(i,EMPTY_SPACE) for i in range(9)]
            def thirds(a,b):
                return int(round((b-a)/3+a)),int(round((b-a)*2/3+a))
            def randomValues(minimum, maximum, minDistance):
                if abs(minimum-maximum) <= minDistance:
                    print "Error in randomValues"
                    return 1,1
                while 1:
                    point1 = random.randrange(minimum,maximum)
                    point2 = random.randrange(minimum,maximum)
                    if abs(point1-point2) <= minDistance:
                        continue
                    else:
                        return min(point1,point2), max(point1,point2)
            vertLine1, vertLine2=thirds(1,mapWidth-1)
            horLine1, horLine2=thirds(1,mapHeight-1)
            # room is (vertleft vertright horbottom hortop roomindex)
            rooms=[]
            #tricks with range insures that the rooms don't touch dividers
            for topHor, bottomHor in [[1,horLine1], [horLine1,horLine2], [horLine2,mapHeight]]:
                for leftVert,rightVert in [[1,vertLine1], [vertLine1,vertLine2], [vertLine2,mapWidth]]:
                    vl,vr = randomValues(leftVert,rightVert,3)
                    hb,ht = randomValues(topHor,bottomHor,3)
                    #draw determined room
                    for x in range(vl,vr):
                        for y in range(hb,ht):
                            self.floormap[y][x]=EMPTY_SPACE
                    rooms.append((vl,vr,hb,ht))
            #determine corridors to draw
            connections=[]
            roomsconnected=range(9) #list of rooms used for calculation
            roompairs=[(0,1),(1,2), #horizontal
                       (3,4),(4,5),
                       (6,7),(7,8),
                       (0,3),(3,6), #vertical
                       (1,4),(4,7),
                       (2,5),(5,8),]
            while max(roomsconnected) > 0:
                index=random.randrange(len(roompairs))
                connection = roompairs[index]
                del roompairs[index]
                group1, group2 = sorted([roomsconnected[connection[0]], roomsconnected[connection[1]]])
                if group1==group2:
                    continue
                else:
                    for room in range(9):
                        if roomsconnected[room] == group2:
                            roomsconnected[room] = group1
                    connections.append(connection)
            #draw corridors
            for corridor in connections:
                room1,room2=rooms[corridor[0]],rooms[corridor[1]]
                #check about a vertical hallway
                def drawvert(room1,room2):
                    vertcommon=list(set(range(room1[0],room1[1])) & set(range(room2[0],room2[1])))
                    if len(vertcommon)==0:
                        return False
                    else:
                        x=random.choice(vertcommon)
                        #draw a vertical hallway
                        bottom,top=sorted((room1[2],room2[2]))
                        for y in range(bottom+1,top):
                            self.floormap[y][x]=EMPTY_SPACE
                        return True
                #check about a horizontal hallway
                def drawhoriz(room1,room2):
                    horizcommon=list(set(range(room1[2],room1[3])) & set(range(room2[2],room2[3])))
                    if len(horizcommon)==0:
                        return False
                    else:
                        y=random.choice(horizcommon)
                        #draw a horizontal hallway
                        left,right=sorted((room1[0],room2[0]))
                        for x in range(left+1,right):
                            self.floormap[y][x]=EMPTY_SPACE
                        return True
                def drawbroken(room1,room2):
                    #supposes no orthogonal lines are possible
                    #xmin,xmax are for the range BETWEEN rooms,
                    #not the rooms themselves
                    xmin,xmax,ymin,ymax,minx,miny=None,None,None,None,None,None
                    if room1[0] > room2[0]: #room1 is left ALWAYS
                        room1,room2=room2,room1
                    xmin = random.randrange(room1[0],room1[1])
                    xmax = random.randrange(room2[0],room2[1])
                    if room1[2] < room2[2]: #if room1 is bottom
                        ymin = random.randrange(room1[2],room1[3])
                        ymax = random.randrange(room2[2],room2[3])
                        midx,midy=random.choice([(xmin,ymax),(xmax,ymin)])
                    else:
                        ymin = random.randrange(room2[2],room2[3])
                        ymax = random.randrange(room1[2],room1[3])
                        midx,midy=random.choice([(xmin,ymin),(xmax,ymax)])
                    for x in range(xmin,xmax+1):
                        self.floormap[midy][x]=EMPTY_SPACE
                    for y in range(ymin,ymax+1):
                        self.floormap[y][midx]=EMPTY_SPACE
                    self.floormap[midy][midx]=EMPTY_SPACE
                    return True
                #put the hallway on the map
                if random.choice((True,False)):
                    if not drawvert(room1,room2):
                        if not drawhoriz(room1,room2):
                            drawbroken(room1,room2)
                else:
                    if not drawhoriz(room1,room2):
                        if not drawvert(room1,room2):
                            drawbroken(room1,room2)
            
        #item generation
        self.items={}
        if NOITEMS not in special:
            for i in range(5):
                randomItem = random.choice((FOOD,POTION,MONEY,WEAPON,ARMOR,GEM))
                self.additem(randomItem)
        #monster generation
        self.monsters={}
        if NOMONSTERS not in special:
            for i in range(2):
                randomMonster = inttomonster(3)
                self.addmonster(randomMonster)
        #stair placement
        self.stairs={}
        for pair in [(x, UP_STAIR) for x in stairsup] + \
                      [(x, DOWN_STAIR) for x in stairsdown]:
            space = self.randomFeaturelessSpace()
            self.stairs[space] = pair[0]
            self.floormap[space[1]][space[0]] = pair[1]
            if pair[1] == UP_STAIR:
                self.cachedupstair=space
        #special feature placement
        if LAVASOURCE in special:
            space = self.randomFeaturelessSpace()
            self.floormap[space[1]][space[0]] = MAGMA
    def additem(self, item):
        space = self.randomUnfilledSpace()
        self.items[space]=item
    def addmonster(self, monster):
        space = self.randomUnoccupiedSpace()
        self.monsters[space]=monster
    def randomSpace(self):
        while 1:
            randSquare=random.randrange(mapWidth),random.randrange(mapHeight)
            if self.solid(randSquare):
                continue
            else:
                return randSquare
    def randomSpecialSpace(self, function):
        def spaceFunc(self2):
            while 1:
                space = self2.randomSpace()
                if function(space):
                    return space
        return spaceFunc
    def randomUnoccupiedSpace(self):
        return self.randomSpecialSpace(lambda s: not self.isOccupied(s))(self)
    def randomUnfilledSpace(self): 
        return self.randomSpecialSpace(lambda s: s not in self.items)(self)
    def randomFeaturelessSpace(self): 
        return self.randomSpecialSpace(lambda s: s not in self.stairs)(self)
    def tile(self, square):
        return self.floormap[square[1]][square[0]]
    def setTile(self, square, s):
        self.floormap[square[1]][square[0]]=s
    def symb(self,square):
        if self.monsterPresent(square):
            return self.monsters[square].symb()
        elif self.itemPresent(square):
            return itemsymbol(self.item(square))
        else:
            return self.tile(square)
    def limitedsymb(self,square):
        if DEATHVIEW and self.wasSeen(square):
            return self.symb(square)
        return self.knownmap[square[1]][square[0]]
    def solid(self, square):
        return self.tile(square) in (WALL, OUTER_WALL)
    def monsterPresent(self, square):
        return square in self.monsters
    def hitMonster(self, square, actor, power):
        if self.monsterPresent(square):
            self.monsters[square].getHit(actor, power)
            if not self.monsters[square].alive():
                del self.monsters[square]
        else:
            print "Error, no monster present on that square."
    def itemPresent(self, square):
        return square in self.items
    def isOccupied(self,square):
        return self.monsterPresent(square) or heroPresent(square)
    def item(self, square):
        if self.itemPresent(square):
            return self.items[square]
        else:
            print "Illegal item access: item not present."
            return "@"
    def takeItem(self, square, actor):
        tempItem = self.items[square]
        del self.items[square]
        actor.addItem(tempItem)
    def empty(self, square):
        if self.floormap != EMPTY_SPACE:
            return False
        elif self.monsterPresent(square):
            return False
        elif self.itemPresent(square):
            return False
        elif heroPresent(square):
            return False
        else:
            return True
    def seen(self,square):
        if not AMNESIA:
            x,y=square
            if square in self.items:
                self.knownmap[y][x]=itemsymbol(self.item(square))
            else:
                self.knownmap[y][x]=copy.copy(self.floormap[y][x])
    def wasSeen(self, square):
        return self.knownmap[square[1]][square[0]]!=UNKNOWN
    def stairup(self):
        #assumes there were stairs up
        return self.cachedupstair
    def stairdownExists(self, name):
        return name in self.stairs.itervalues()
    def getstairdown(self, name):
        #assumes it's actually down
        stairset=[key for key,item in self.stairs.iteritems() if item==name]
        if len(stairset)==0:
            print "No stairs down"
        elif len(stairset)==1:
            return stairset[0]
        else:
            print "Too many stairs down"
            return stairset[0]

def testPoint(square):
    return not curlevel.solid(square)
#the following code taken from en.literateprograms.org
#(Brensenham's algorithm for drawing lines using integer arithmetic)
def testLine(x1,y1,x2,y2):
    steep = abs(y2 - y1) > abs(x2 - x1)
    if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
    if y1 < y2: 
        ystep = 1
    else:
        ystep = -1
    deltax = x2-x1
    deltay = abs(y2-y1)
    error = -deltax / 2
    y=y1
    for x in range(x1, x2+1):
        if steep:
            if not testPoint((y,x)):
                return False
        else:
            if not testPoint((x,y)):
                return False
        error += deltay
        if error >= 0:
            y+=ystep
            error-=deltax
    return True
def LOS(square1,square2):
    x1,y1=square1
    x2,y2=square2
    if (abs(x1-x2)+abs(y1-y2)>8) and not FULLVIEW:
        return False

    #check to see if, ignoring the endpoints, there's a clear path
    if x1==x2:
        pass
    elif x1 < x2:
        x2-=1
        if x1!=x2:
            x1+=1
    else:
        x2+=1
        if x1!=x2:
            x1-=1
    if y1==y2:
        pass
    elif y1 < y2:
        y2-=1
        if y1!=y2:
            y1+=1
    else:
        y2+=1
        if y1!=y2:
            y1-=1
    return testLine(x1,y1,x2,y2)

class character:
    pos = (4,4)
    level = 1 #dungeon level
    #max hp, min hp, money, food, gems, weapon, armor, points, turns
    state = {MAXHP:0, HP:0, POINT:0, TURN:0, MONEY:0, FOOD:0, GEM:0, WEAPON:0, ARMOR:0, POTION:0, SCROLL:0}
    alive=True
    killer = None
    def __init__(self):
        self.addItem(MAXHP,3)
        self.addItem(FOOD)
        self.addItem(WEAPON)
        self.addItem(ARMOR)
        if GODLYMIGHT:
            self.addItem(MAXHP,50)
            self.addItem(WEAPON,50)
            self.addItem(ARMOR,50)
        self.addScore(1) #for living
    def addItem(self, item, amount=1):
        if item in self.state:
            if item==HP:
                amount = max(0, min(self.state[HP]+amount, self.state[MAXHP]))-self.state[HP]
            self.state[item] += amount
            if item!= POINT and item != TURN:
                self.addScore(amount*itemscore(item))
            if item==MAXHP:
                self.addItem(HP, amount) #max health increases current health
            if item==HP and self.state[HP] <= 0:
                self.alive=False
                self.addScore(-1)
                message("You die.")
        else:
            print "Error, that is not a valid item"
    def removeItem(self,item,amount):
        self.addItem(item, -amount)
    def power(self):
        return max(1, self.state[WEAPON])
    def getHit(self,pow,actor):
        if self.alive:
            damage = max(0, pow-self.state[ARMOR])
            self.removeItem(HP, damage)
            actor.addScore(damage)
            if not self.alive:
                actor.addScore(1)
                #add cause of death here
    def addScore(self,points):
        self.addItem(POINT, points)
    def setKiller(self, killerSymb):
        if self.alive:
            self.killer=killerSymb

hero = character()
def heroPresent(square):
    return square==hero.pos

def printhero():
    global cursorxpos
    global cursorypos
    
    if hero.alive:
        printsymb(hero.pos, CHAR_SYMB)
    else:
        if curlevel.tile(hero.pos) in (MAGMA, LAVA):
            printsymb(hero.pos, BURNT_CHAR_SYMB)
        else:
            printsymb(hero.pos, DEAD_CHAR_SYMB)
    cursorxpos=hero.pos[0]
    cursorypos=LINES-hero.pos[1]-2

idealTokenLength = COLUMNS // len(hero.state)
if DEBUG:
    idealTokenLength=0
def printstatus():
    pieces=[]
    spacer = " "
    for elt, val in hero.state.items():
        token="_ " + pprint.pformat(val)
        token += " " * max(0, idealTokenLength-len(token))
        pieces.append(token)
    if pieces==[]:
        print "error, no status line"
    else:
        line = ''.join(pieces)
        if DEBUG:
            line = line + " L" + pprint.pformat(hero.level)
            line = line + " X" + pprint.pformat(hero.pos[0])
            line = line + " Y" + pprint.pformat(hero.pos[1])
        setstatusline(line)

herocansee=set()
herocannotsee=set()
heromaybesees=set()
def printmap():
    for square in mapPositions:
        printsymb(square, ERROR_SYMB)
    for square in mapPositions:
        if OMNISCIENT:
            printsymb(square, curlevel.symb(square))
        else:
            printsymb(square, curlevel.limitedsymb(square))
    for square in getsight(hero.pos):
        printsymb(square, curlevel.symb(square))
        curlevel.seen(square)
def getsight(psquare):
    if FULLVIEW:
        return mapPositions
    else:
        px,py=psquare
        minx=max(0,px-10)
        maxx=min(mapWidth-1,px+10)
        miny=max(0,py-10)
        maxy=min(mapHeight-1,py+10)
        possarea = [(x,y) for x in range(minx,maxx+1) for y in range(miny,maxy+1)]
        actualarea = [square for square in possarea if LOS(psquare,square)]
        return set(actualarea)
def printheroarea():
    global herocansee
    global herocannotsee
    global heromaybesees
    for square in heromaybesees:
        if LOS(hero.pos, square):
            herocansee.add(square)
        else:
            herocannotsee.add(square)
    heromaybesees.clear()
    for square in herocansee:
        curlevel.seen(square)
        printsymb(square, curlevel.symb(square))
    for square in herocannotsee:
        printsymb(square, curlevel.limitedsymb(square))
    if OMNISCIENT:
        for square in mapPositions:
            printsymb(square, curlevel.symb(square))
    herocannotsee.clear()
    herocansee.clear()
    printhero()
#don't allocate the square now because the hero could shift levels
def flagsquare(square): 
    global heromaybesees
    heromaybesees.add(square)
def flagheromove(a,b):
    global herocansee
    global herocannotsee
    old = getsight(a)
    new = getsight(b)
    herocansee |= (new - old)
    herocannotsee |= (old - new)

class fluidicEntity:
    score=0
    def addScore(self, points):
        self.score += points
    def addItem(self, item):
        self.addScore(itemscore(item))
lava = fluidicEntity()

#define the moves
LEFT, RIGHT, DOWN, UP, DEPTH_DOWN, DEPTH_UP, WAIT, HELP, QUIT = range(9)

standardKeys = {
 curses.KEY_LEFT:LEFT,
 ord("h"):LEFT,
 ord("H"):LEFT,
 ord("a"):LEFT,
 ord("A"):LEFT,
 curses.KEY_RIGHT:RIGHT,
 ord("l"):RIGHT,
 ord("L"):RIGHT,
 ord("d"):RIGHT,
 ord("D"):RIGHT,
 curses.KEY_DOWN:DOWN,
 ord("k"):DOWN,
 ord("K"):DOWN,
 ord("s"):DOWN,
 ord("S"):DOWN,
 curses.KEY_UP:UP,
 ord("j"):UP,
 ord("J"):UP,
 ord("w"):UP,
 ord("W"):UP,
 ord(">"):DEPTH_DOWN,
 ord("<"):DEPTH_UP,
 curses.KEY_B2:WAIT,
 curses.ascii.SP:WAIT,
 ord("."):WAIT,
 curses.KEY_F1:HELP,
 ord("?"):HELP,
 curses.ascii.ESC:QUIT,
 ord("Q"):QUIT,
 ord("X"):QUIT, 
 }

def getAction():
    key=getkey()
    while (key not in standardKeys):
        key = getkey()
    return standardKeys[key]

moveVectors = {
 LEFT:(-1,0,0),
 RIGHT:(1,0,0),
 DOWN:(0,-1,0),
 UP:(0,1,0),
 DEPTH_DOWN:(0,0,-1),
 DEPTH_UP:(0,0,1),
 WAIT:(0,0,0)
 }

OUTSIDE,NOITEMS,NOMONSTERS,LAVASOURCE=range(4)
dungeon = {
    OUTSIDE:level(depth=0, stairsup=[], stairsdown=["top"], special=[NOITEMS,NOMONSTERS,OUTSIDE]),
    "top":level(depth=1, stairsup=[OUTSIDE], stairsdown=["middle"], special=[]),
    "middle":level(depth=1, stairsup=["top"], stairsdown=["bottom"], special=[LAVASOURCE]),
    "bottom":level(depth=1, stairsup=["middle"], stairsdown=[], special=[]),
}
curindex = "middle"
curlevel = dungeon[curindex]
lava.level="middle"

def sight(level,space,mess):
    if hero.level == level:
        if LOS(hero.pos, space) or OMNISCIENT:
            message(mess)
def adjacent(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1
def spreadzombies():
    pass

lavaCounter=-1
def updatelava():
    global lavaCounter
    lavaCounter+=lavaspeed
    while lavaCounter > 0:
        lavaCounter-=1
        lavamove()
def lavamove():
    lavalevel=dungeon[lava.level]
    magmasquares = [square for square in mapPositions if lavalevel.tile(square) == MAGMA]
    if DEATHMAGMA:
        #finish the levels very fast
        bordersquares = lavalevel.stairs.keys() + lavalevel.items.keys() + lavalevel.monsters.keys()
    else:
        bordersquares = [square for magmaSquare in magmasquares for square in mapPositions if adjacent(square,magmaSquare)]
        bordersquares = list(set(bordersquares))
        bordersquares = [square for square in bordersquares if not lavalevel.solid(square)]
    bordersquares = [square for square in bordersquares if not lavalevel.tile(square) in (LAVA, MAGMA)]
    if len(bordersquares) == 0:
        for square in magmasquares:
            flagsquare(square)
            x,y=square
            lavalevel.floormap[y][x] = LAVA
        oldlev=lava.level
        upstair = lavalevel.stairup()
        lava.level = lavalevel.stairs[upstair]
        del lavalevel.stairs[upstair]
        lavalevel=dungeon[lava.level]
        if hero.alive: #when a level is destroyed by lava
            if hero.level == OUTSIDE:
                message("The ground rumbles.")
            else:
                message("It gets warmer.")
        if lava.level != OUTSIDE:
            if lavalevel.stairdownExists(oldlev):
                sight(oldlev,dungeon[oldlev].stairup(),"Lava fills the level.")
                stairdown = lavalevel.getstairdown(oldlev)
                del lavalevel.stairs[stairdown]
                magmify(lava.level,stairdown)
                sight(lava.level,stairdown,"Lava bubbles up the stairs!")
            else:
                print "No stairs back down!"
        else:
            message("The volcano erupts!")
            pass #lava's done
    else:
        stairspresent=[square for square in bordersquares if square in lavalevel.stairs]
        for square in stairspresent:
            if lavalevel.tile(square) == DOWN_STAIR:
                magmify(lava.level,square)
                sight(lava.level, square, "Lava starts pouring down the stairs.")
                lava.level = lavalevel.stairs[square]
                lavalevel=dungeon[lava.level]
                upstairssquare=lavalevel.stairup()
                magmify(lava.level,upstairssquare)
                sight(lava.level, upstairssquare, "Lava pours down the stairs!")
                return
        for square in bordersquares:
            magmify(lava.level,square)
        for square in magmasquares:
            if lava.level==hero.level:
                flagsquare(square)
            x,y=square
            lavalevel.floormap[y][x] = LAVA
def magmify(levelname,square):
    #assuption: not a down staircase, not solid
    level=dungeon[levelname]
    x,y=square
    level.floormap[y][x] = MAGMA
    if hero.alive and levelname==hero.level and square == hero.pos:
        if not LAVAMUNITY:
            message("You are cremated.")
            hero.getHit(255,lava)
    if level.itemPresent(square):
        sight(levelname, square, "The object is incinerated.")
        level.takeItem(square,lava)
    if level.monsterPresent(square):
        mname=level.monsters[square].name()
        sight(levelname, square, "The " + mname + " is roasted.")
        level.hitMonster(square,lava,255)
    if levelname==hero.level:
        flagsquare(square)

hero.level = curindex
hero.pos = curlevel.stairup()
message("You enter the volcano.")
printmap()
printheroarea()
action = None
while(hero.alive and action != QUIT and hero.level != OUTSIDE):
    printstatus()
    update()
    clearmessage() #This is a soft clear
    
    #Hero action
    action=getAction()
    if action==HELP:
        message(programName + " version " + programVersion)
        if WIZARDKEYS:
            OMNISCIENT = not OMNISCIENT
        continue
    elif action == QUIT:
        message("You quit.")
        break
    elif action in moveVectors:
        vector = moveVectors[action]
        if action != WAIT:
            flagsquare(hero.pos)
            if vector[2] == 0:
                newPos=(hero.pos[0] + vector[0],hero.pos[1] + vector[1])
                if curlevel.solid(newPos):
                    message("Ouch!")
                    continue
                else:
                    flagsquare(newPos)
                    if curlevel.monsterPresent(newPos):
                        #hit the monster
                        mname=curlevel.monsters[newPos].name()
                        message("You hit the " + mname + " for "+pprint.pformat(hero.power())+" damage.")
                        curlevel.hitMonster(newPos, hero, hero.power())
                        if newPos not in curlevel.monsters:
                            message("It dies.")
                    else:
                        flagheromove(hero.pos,newPos)
                        hero.pos = newPos
                        if curlevel.tile(newPos) == MAGMA:
                            magmify(hero.level, newPos)
                        if curlevel.itemPresent(newPos):
                            curlevel.takeItem(newPos, hero)
                            message("You pick it up.")
                            if hero.pos in curlevel.stairs:
                                type=curlevel.tile(newPos)
                                if type==UP_STAIR:
                                    type="up"
                                else:
                                    type="down"
                                message("You discover stairs leading " + type + " underneath.")
            else:
                if hero.pos in curlevel.stairs:
                    stairtype=curlevel.tile(hero.pos)
                    if (vector[2]==1 and stairtype != UP_STAIR) \
                        or (vector[2]==-1 and stairtype != DOWN_STAIR):
                        message("You can't walk that way.")
                        continue

                    #attempt to traverse stairs
                    targetindex = curlevel.stairs[hero.pos]
                    if targetindex not in dungeon:
                        print "Target level ", targetindex, "does not exist."
                        continue
                    targetlevel = dungeon[targetindex]
                    if targetlevel.stairdownExists(curindex):
                        #actually use stairs
                        hero.pos=targetlevel.getstairdown(curindex)
                        curindex,curlevel=targetindex,targetlevel
                        hero.level=curindex
                        printstatus() #Displays the level number
                        printmap()
                        if hero.level == OUTSIDE:
                            message("You exit the dungeon.")
                    else:
                        print "Bad stairs from level ", targetindex, " to level ", curindex
                        continue
                else:
                    message("You can't walk that way.")
                    continue
            printheroarea()
        else:
            message("Zzz...")
            if WIZARDKEYS:
                TIMEFREEZE = not TIMEFREEZE
    else:
        print "Error, illegal action."
        break
    hero.addItem(TURN) #Add a turn
    #Level actions
    if not TIMEFREEZE:
        spreadzombies()
        for square in curlevel.monsters.keys():
            x,y=square
            if hero.alive:
                targetx,targety = hero.pos
                xshift,yshift=0,0
                if targetx > x:
                    xshift=1
                elif targetx < x:
                    xshift=-1
                else:
                    xshift=0
                if targety > y:
                    yshift=1
                elif targety < y:
                    yshift=-1
                else:
                    yshift=0
                positionRanking = []
                if xshift != 0 and yshift != 0: #Diagonal
                    if curlevel.monsters[(x,y)].prefersX():
                        positionRanking = [(xshift, 0), (0, yshift), (0,0)]
                    else:
                        positionRanking = [(0, yshift), (xshift, 0), (0,0)]
                elif xshift == 0 and yshift == 0:
                    positionRanking = [(0,0)]
                else: #Orthogonal
                    if xshift == 0:
                        positionRanking = [(0, yshift), (0,0)]
                    elif yshift == 0:
                        positionRanking = [(xshift, 0), (0,0)]
                    else:
                        print "Error in levelAction/moveMonsters/positionRanking"
                if TIMEFREEZE: positionRanking=[(0,0)]
                for vector in positionRanking:
                    newPos=(x+vector[0], y+vector[1])
                    if curlevel.solid(newPos):
                        continue
                    if vector==(0,0):
                        break
                    if newPos==hero.pos:
                        #attack the hero
                        message("The " + curlevel.monsters[square].name() + " attacks you.")
                        herooldhp=hero.state[HP]
                        hero.setKiller(curlevel.monsters[square].symb())
                        #not very OO
                        hero.getHit(curlevel.monsters[square].power, curlevel.monsters[square])
                        herohpchange=herooldhp - hero.state[HP]
                        if herohpchange > 0:
                            message("It did " + str(herohpchange) + " damage.")
                        elif herohpchange == 0:
                            message("It did not hurt you.")
                        else:
                            message("It healed you.")
                        break
                    if curlevel.isOccupied(newPos):
                        continue
                    flagsquare(square)
                    flagsquare(newPos)
                    curlevel.monsters[newPos]=curlevel.monsters[square]
                    del curlevel.monsters[square]
                    if curlevel.tile(newPos)==MAGMA:
                        magmify(hero.level, newPos) #A refresh so as not to duplicate code
                    break
                else:
                    message("The monster disintigrates.")
                    del curlevel.monsters[square]
        spreadzombies()
        updatelava()
    printheroarea()

message("Press any key to continue.")
printstatus()
printheroarea()
printhero()
update()
anykey()

if (not action==QUIT) and (not TIMEFREEZE):
    DEATHVIEW=True
    while lava.level != OUTSIDE:
        if lava.level==hero.level:
            DEATHMAGMA=False
        else:
            DEATHMAGMA=True
        oldlev=lava.level
        lavamove()
        if hero.level in (lava.level, oldlev):
            printmap()
            printhero()
            update()
    
            
message("Game over.")

printstatus()
update()
anykey()

closescreen()