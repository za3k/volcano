import curses
import curses.ascii
import pprint
import random
import copy

WIZARDKEYS=True
OMNISCIENT=False
TIMEFREEZE=False
GODLYMIGHT=True
LAVAMUNITY=False
debug=True

programName="Volcano"
programVersion="0.0.4 (beta)"

debid=0
def setid(x):
    global debid
    debid=x

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

def printsymb(x, y, symb):
    if curses.has_colors():
        screen.addch(LINES-y-2, x, symb.ascii, symb.color)
    else:
        screen.addch(LINES-y-2, x, symb.ascii)

mapWidth = COLUMNS
mapHeight = LINES-messLines-1    

#define tiles
UNKNOWN = symbol("?", WHITE)
EMPTY_SPACE = symbol(".", GRAY)
GRASS = symbol(".", GREEN)
WALL = symbol("#", WHITE)
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

itemList = {
    "%":BROWN,
    "$":YELLOW,
    "*":ALERT_COLOR,
    "(":GRAY,
    "[":GRAY,
    "!":BOLD_BLUE,
}

for asc, col in itemList.items():
    itemList[asc] = symbol(asc, col)

gemColors = (BOLD_GREEN, BOLD_BLUE, BOLD_RED, WHITE, YELLOW, GRAY)
def itemsymbol(itm):
    if itm=="*":
        return symbol("*", gemColors[(curlevel.depth % len(gemColors))])
    elif itm in itemList:
        return itemList[itm]
    else:
        return symbol(itm)

monsterList = {
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

for name, col in monsterList.items():
    monsterSymbols[name[0]] = symbol(name[0], col)

for name in monsterList:
    monsterNames[name[0]] = name #.lower()

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
                self.seen(x,y)
        else:
            #outside walls
            for y in range(mapHeight):
                self.floormap[y][0]=OUTER_WALL
                self.floormap[y][mapWidth-1]=OUTER_WALL
            for x in range(1,mapWidth-1):
                self.floormap[0][x]=OUTER_WALL
                self.floormap[mapHeight-1][x]=OUTER_WALL
                for y in range(1,mapHeight-1):
                    self.floormap[y][x]=EMPTY_SPACE
            #wall in the middle
            for y in range(5, 10):
                self.floormap[y][10] = WALL
        #item generation
        self.items={}
        if NOITEMS not in special:
            for i in range(5):
                randomItem = random.choice(("%","!","$","(","[","*"))
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
            x=random.randrange(mapWidth)
            y=random.randrange(mapHeight)
            if self.solid(x,y):
                continue
            else:
                return (x,y)
    def randomSpecialSpace(self, function):
        def spaceFunc(self2):
            while 1:
                space = self2.randomSpace()
                if function(space):
                    return space
        return spaceFunc
    def randomUnoccupiedSpace(self):
        return self.randomSpecialSpace(lambda s: not self.isOccupied(s[0],s[1]))(self)
    def randomUnfilledSpace(self): 
        return self.randomSpecialSpace(lambda s: s not in self.items)(self)
    def randomFeaturelessSpace(self): 
        return self.randomSpecialSpace(lambda s: s not in self.stairs)(self)
    def symb(self,x,y):
        if self.monsterPresent(x,y):
            return self.monsters[(x,y)].symb()
        elif self.itemPresent(x,y):
            return itemsymbol(self.item(x,y))
        else:
            return self.floormap[y][x]
    def limitedsymb(self,x,y):
        return self.knownmap[y][x]
    def solid(self, x, y):
        tile = self.floormap[y][x]
        if tile==WALL:
            return True
        if tile==OUTER_WALL:
            return True
        return False
    def monsterPresent(self, x, y):
        return (x, y) in self.monsters
    def hitMonster(self, x, y, actor, power):
        if self.monsterPresent(x,y):
            self.monsters[(x,y)].getHit(actor, power)
            if not self.monsters[(x,y)].alive():
                del self.monsters[(x,y)]
        else:
            print "Error, no monster present on that square (", x, ", ", y, ") "
    def itemPresent(self, x, y):
        return (x, y) in self.items
    def isOccupied(self,x,y):
        if self.monsterPresent(x,y):
            return True
        elif heroPresent(x,y):
            return True
        else:
            return False
    def item(self, x, y):
        if self.itemPresent(x,y):
            return self.items[(x, y)]
        else:
            print "Illegal item access: item not present at ",x,y
            return "@"
    def takeItem(self, x, y, actor):
        tempItem = self.items[(x,y)]
        del self.items[(x,y)]
        actor.addItem(tempItem)
    def empty(self, x, y):
        if self.floormap != EMPTY_SPACE:
            return False
        elif self.monsterPresent(x,y):
            return False
        elif self.itemPresent(x,y):
            return False
        elif heroPresent(x,y):
            return False
        else:
            return True
    def seen(self,x,y):
        if (x,y) in self.items:
            self.knownmap[y][x]=itemsymbol(self.item(x,y))
        else:
            self.knownmap[y][x]=copy.copy(self.floormap[y][x])
    def wasSeen(self, x, y):
        return (not (self.knownmap[y][x]==UNKNOWN))
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

def LOS(square1,square2):
    x1,y1=square1
    x2,y2=square2
    if abs(x1-x2) + abs(y1-y2) <= 10:
        return True
    else:
        return False

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
        x=monstersymbol(asc)
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

MAXHP = "@"
HP = "#"
POINT = "P"
TURN = "T"
MONEY = "$"
FOOD = "%"
GEM = "*"
WEAPON = "("
ARMOR = "["
POTION = "!"
SCROLL = "?"

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

class character:
    xpos = 4
    ypos = 4
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
        return max(1, self.state["("])
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
def heroPresent(x, y):
    if x==hero.xpos:
        if y==hero.ypos:
            return True
    return False

def printhero():
    global cursorxpos
    global cursorypos
    
    if hero.alive:
        printsymb(hero.xpos, hero.ypos, CHAR_SYMB)
    else:
        if curlevel.floormap[hero.ypos][hero.xpos] in (MAGMA, LAVA):
            printsymb(hero.xpos, hero.ypos, BURNT_CHAR_SYMB)
        else:
            printsymb(hero.xpos, hero.ypos, DEAD_CHAR_SYMB)
    cursorxpos=hero.xpos
    cursorypos=LINES-hero.ypos-2

idealTokenLength = COLUMNS // len(hero.state)
if debug:
    idealTokenLength=0
def printstatus():
    pieces=[]
    spacer = " "
    for elt, val in hero.state.items():
        token=elt + ": " + pprint.pformat(val)
        token += " " * max(0, idealTokenLength-len(token))
        pieces.append(token)
    if pieces==[]:
        print "error, no status line"
    else:
        line = ''.join(pieces)
        if debug:
            line = line + " L" + pprint.pformat(hero.level)
            line = line + " X" + pprint.pformat(hero.xpos)
            line = line + " Y" + pprint.pformat(hero.ypos)
            line = line + " I" + pprint.pformat(debid)
        setstatusline(line)

herocansee=set()
herocannotsee=set()
heromaybesees=set()
def printmap():
    for x,y in mapPositions:
        printsymb(x,y, ERROR_SYMB)
    for x,y in mapPositions:
        if OMNISCIENT:
            printsymb(x,y, curlevel.symb(x,y))
        else:
            printsymb(x,y, curlevel.limitedsymb(x,y))
    for x,y in getsight(hero.xpos,hero.ypos):
        printsymb(x,y, curlevel.symb(x,y))
        curlevel.seen(x,y)
def getsight(px,py):
    minx=max(0,px-10)
    maxx=min(mapWidth-1,px+10)
    miny=max(0,py-10)
    maxy=min(mapHeight-1,py+10)
    possarea = [(x,y) for x in range(minx,maxx+1) for y in range(miny,maxy+1)]
    actualarea = [square for square in possarea if LOS(square, (px,py))]
    return set(actualarea)
def printheroarea():
    global herocansee
    global herocannotsee
    global heromaybesees
    for square in heromaybesees:
        if LOS((hero.xpos, hero.ypos), square):
            herocansee.add(square)
        else:
            herocannotsee.add(square)
    heromaybesees.clear()
    for x,y in herocansee:
        curlevel.seen(x,y)
        printsymb(x,y, curlevel.symb(x,y))
    for x,y in herocannotsee:
        printsymb(x,y, curlevel.limitedsymb(x,y))
    if OMNISCIENT:
        for x,y in mapPositions:
            printsymb(x,y, curlevel.symb(x,y))
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
    old = getsight(a[0],a[1])
    new = getsight(b[0],b[1])
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

curindex = "middle"

OUTSIDE="outside"
NOITEMS="noitems"
NOMONSTERS="nomonsters"
LAVASOURCE="lavasource"
dungeon = {
    OUTSIDE:level(depth=0, stairsup=[], stairsdown=["top"], special=[NOITEMS,NOMONSTERS,OUTSIDE]),
    "top":level(depth=1, stairsup=[OUTSIDE], stairsdown=["middle"], special=[]),
    "middle":level(depth=3, stairsup=["top"], stairsdown=["bottom"], special=[LAVASOURCE]),
    "bottom":level(depth=9, stairsup=["middle"], stairsdown=[], special=[]),
}
curlevel = dungeon[curindex]
lava.level="middle"

def sight(level,space,mess):
    if hero.level == level:
        if LOS((hero.xpos,hero.ypos), space) or OMNISCIENT:
            message(mess)
def adjacent(a,b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) == 1
def spreadzombies():
    pass
def updatelava():
    lavalevel=dungeon[lava.level]
    magmasquares = [(x,y) for x,y in mapPositions if lavalevel.floormap[y][x] == MAGMA]
    bordersquares = [square for magmaSquare in magmasquares for square in mapPositions if adjacent(square,magmaSquare)]
    bordersquares = list(set(bordersquares))
    bordersquares = [(x,y) for x,y in bordersquares if not lavalevel.solid(x,y)]
    bordersquares = [(x,y) for x,y in bordersquares if not lavalevel.floormap[y][x] in (LAVA, MAGMA)]

    if len(bordersquares) == 0:
        for x,y in magmasquares:
            flagsquare((x,y))
            lavalevel.floormap[y][x] = LAVA
        oldlev=lava.level
        upstair = lavalevel.stairup()
        lava.level = lavalevel.stairs[upstair]
        del lavalevel.stairs[upstair]
        lavalevel=dungeon[lava.level]
        if lava.level != OUTSIDE:
            if lavalevel.stairdownExists(oldlev):
                sight(oldlev,dungeon[oldlev].stairup(),"Lava fills the level.")
                stairdown = lavalevel.getstairdown(oldlev)
                del lavalevel.stairs[stairdown]
                magmify(lava.level,stairdown)
                sight(lava.level,stairdown,"Lava bubbles up the stairs!")
                if hero.alive:
                    message("It gets warmer.")
            else:
                print "No stairs back down!"
        else:
            pass #lava's done
    else:
        stairspresent=[square for square in bordersquares if square in lavalevel.stairs]
        for x,y in stairspresent:
            if lavalevel.floormap[y][x] == DOWN_STAIR:
                magmify(lava.level,(x,y))
                sight(lava.level, (x,y), "Lava starts pouring down the stairs.")
                lava.level = lavalevel.stairs[(x,y)]
                lavalevel=dungeon[lava.level]
                upstairssquare=lavalevel.stairup()
                magmify(lava.level,upstairssquare)
                sight(lava.level, upstairssquare, "Lava pours down the stairs!")
                return
        for square in bordersquares:
            magmify(lava.level,square)
        for x,y in magmasquares:
            if lava.level==hero.level:
                flagsquare((x,y))
            lavalevel.floormap[y][x] = LAVA
def magmify(levelname,square):
    #assuption: not a down staircase, not solid
    level=dungeon[levelname]
    x,y=square
    level.floormap[y][x] = MAGMA
    if hero.alive and levelname==hero.level and (x,y) == (hero.xpos, hero.ypos):
        if not LAVAMUNITY:
            message("You are cremated.")
            hero.getHit(255,lava)
    if level.itemPresent(x,y):
        sight(levelname, square, "The object is incinerated.")
        level.takeItem(x,y,lava)
    if level.monsterPresent(x,y):
        mname=level.monsters[(x,y)].name()
        sight(levelname, square, "The " + mname + " is roasted.")
        level.hitMonster(x,y,lava,255)
    if levelname==hero.level:
        flagsquare(square)


hero.level=curindex
hero.xpos, hero.ypos = curlevel.stairup()

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
            flagsquare((hero.xpos,hero.ypos))
            if vector[2] == 0:
                newxPos = hero.xpos + vector[0]
                newyPos = hero.ypos + vector[1]
                if curlevel.solid(newxPos,newyPos):
                    message("Ouch!")
                    continue
                else:
                    flagsquare((newxPos,newyPos))
                    if curlevel.monsterPresent(newxPos, newyPos):
                        #hit the monster
                        mname=curlevel.monsters[(newxPos,newyPos)].name()
                        message("You hit the " + mname + " for "+pprint.pformat(hero.power())+" damage.")
                        curlevel.hitMonster(newxPos, newyPos, hero, hero.power())
                        if (newxPos,newyPos) not in curlevel.monsters:
                            message("It dies.")
                    else:
                        flagheromove((hero.xpos,hero.ypos),(newxPos,newyPos))
                        hero.xpos = newxPos
                        hero.ypos = newyPos
                        if curlevel.floormap[newyPos][newxPos] == MAGMA:
                            magmify(hero.level, (newxPos,newyPos))
                        if curlevel.itemPresent(newxPos, newyPos):
                            curlevel.takeItem(newxPos, newyPos, hero)
                            message("You pick it up.")
                            if (hero.xpos, hero.ypos) in curlevel.stairs:
                                type=curlevel.floormap[newyPos][newxPos]
                                if type==UP_STAIR:
                                    type="up"
                                else:
                                    type="down"
                                    message("You discover stairs leading " + type + " underneath.")
            else:
                herosquare = (hero.xpos, hero.ypos)
                if herosquare in curlevel.stairs:
                    stairtype=curlevel.floormap[herosquare[1]][herosquare[0]] 
                    if (vector[2]==1 and stairtype != UP_STAIR) \
                        or (vector[2]==-1 and stairtype != DOWN_STAIR):
                        message("You can't walk that way.")
                        continue

                    #attempt to traverse stairs
                    targetindex = curlevel.stairs[herosquare]
                    if targetindex not in dungeon:
                        print "Target level ", targetindex, "does not exist."
                        continue
                    targetlevel = dungeon[targetindex]
                    if targetlevel.stairdownExists(curindex):
                        #actually use stairs
                        stairsquare=targetlevel.getstairdown(curindex)
                        curindex,curlevel=targetindex,targetlevel
                        hero.level=curindex
                        hero.xpos,hero.ypos=stairsquare
                        printstatus() #Displays the level number
                        printmap()
                        if hero.level == OUTSIDE:
                            message("You exit the dungeon.")
                    else:
                        print "Bad stairs from level ", targetindex, " to level ", currentindex
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
            (x,y)=square
            if hero.alive:
                targetx,targety = hero.xpos,hero.ypos
                (xshift,yshift)=(0,0)
                
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
                    newx,newy=x+vector[0], y+vector[1]
                    if curlevel.solid(newx, newy):
                        continue
                    if vector==(0,0):
                        break
                    if newx==hero.xpos and newy==hero.ypos:
                        #attack the hero
                        message("The " + curlevel.monsters[square].name() + " attacks you.")
                        herooldhp=hero.state["#"]
                        hero.setKiller(curlevel.monsters[square].symb())
                        hero.getHit(curlevel.monsters[square].power, curlevel.monsters[square])
                        herohpchange=herooldhp - hero.state["#"]
                        if herohpchange > 0:
                            message("It did " + str(herohpchange) + " damage.")
                        elif herohpchange == 0:
                            message("It did not hurt you.")
                        else:
                            message("It healed you.")
                        break
                    if curlevel.isOccupied(newx, newy):
                        continue
                    flagsquare(square)
                    flagsquare((newx,newy))
                    curlevel.monsters[(newx,newy)]=curlevel.monsters[square]
                    del curlevel.monsters[square]
                    if curlevel.floormap[newy][newx]==MAGMA:
                        magmify(hero.level, (newx,newy)) #A refresh so as not to duplicate code
                    break
                else:
                    message("The monster disintigrates.")
                    del curlevel.monsters[square]
        spreadzombies()
        updatelava()
    printheroarea()

printstatus()
printheroarea()
printhero()
update()
anykey()

if (not action==QUIT) and (not TIMEFREEZE):
    while lava.level != OUTSIDE:
        oldlev=lava.level
        updatelava()
        if hero.level in (lava.level, oldlev):
            printmap()
            printhero()
            update()
    
            
message("Game over.")

printstatus()
update()
anykey()

closescreen()