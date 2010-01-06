import curses;
import curses.ascii;
import pprint;
import random;

debug=True;
debid=0;
def setid(x):
    global debid;
    debid=x;

def deepcopylist(multidimarray, dim):
    if dim==1:
        return multidimarray[:];
    else:
        a=[];
        for x in multidimarray:
            y=None;
            y=deepcopylist(x,dim-1);
            a.append(y);
        return a;

#initialization
screen=curses.initscr()
curses.start_color();
curses.noecho()
screen.keypad(1)
if curses.has_colors():
    for color in range(8):
        curses.init_pair(color+1, color, curses.COLOR_BLACK);

def color_to_pair(color):
    return color+1;
def color_to_attr(col):
        return curses.color_pair(color_to_pair(col));
#color definitions
WHITE = color_to_attr(curses.COLOR_WHITE) + curses.A_BOLD;
GRAY = GREY = color_to_attr(curses.COLOR_WHITE);
BOLD_RED = color_to_attr(curses.COLOR_RED) + curses.A_BOLD;
RED = color_to_attr(curses.COLOR_RED);
BOLD_BLUE = color_to_attr(curses.COLOR_BLUE) + curses.A_BOLD;
BROWN = color_to_attr(curses.COLOR_RED) + curses.A_DIM;
TAN = color_to_attr(curses.COLOR_YELLOW);
YELLOW = color_to_attr(curses.COLOR_YELLOW) + curses.A_BOLD;
BOLD_GREEN = color_to_attr(curses.COLOR_GREEN) + curses.A_BOLD;
ALERT_COLOR = color_to_attr(curses.COLOR_MAGENTA) + curses.A_BOLD;

def closescreen():
    curses.nocbreak();
    screen.keypad(0);
    curses.echo();
    curses.endwin();

cursorxpos=cursorypos=1;
def updatecursor():
    screen.move(cursorypos, cursorxpos);

def anykey():
    screen.getch();
def update():
    updatecursor();
    screen.refresh();

COLUMNS = 80;
LINES = 24;

def clearline(line):
    screen.hline(line,0, ord(" "), COLUMNS)

messLines=2;
messline=0;
messpos=0;
morestr=" --more--";
morelen=len(morestr);
def message(str):
    global messline;
    global messpos;
            
    while (len(str) > 0):
        #print "ACCESS:", str, messline, messpos;
        if(messline == messLines-1):
            charsleft = COLUMNS-morelen-messpos;
        else:
            charsleft = COLUMNS-messpos; 
        printedchars = min(charsleft, len(str));
        if charsleft > 0:
            screen.addstr(messline, messpos, 
                          str[0:printedchars]);
            messpos += printedchars;
            str = str[printedchars+1:];
        else:
            if(messline == messLines-1): #more
                screen.addstr(messline, messpos, morestr);
                update();
                anykey();
                screen.addstr(messline, messpos, " "*morelen); #clear 'more'
                messpos=0;
                messline = 0;
                #clearmessage();
            else:
                messline += 1;
            messpos=0;
            clearline(messline);
    if (not (((messline==messLines) and (messpos>=COLUMNS-morelen-2))
            or ((messline==0) and (messpos==0)))): 
                #spacing if needed and there's room
        screen.addstr(messline, messpos, "  ");
        messpos += 2;

def clearmessage():
    global messpos;
    global messline;
    messpos=0;
    messline=0;
    for line in range(messLines):
        clearline(line);

statusLine=LINES-1;
def setstatusline(str):
    clearline(statusLine);
    screen.addstr(statusLine, 0, str[0:COLUMNS]);

def getkey():
    return screen.getch();
    
class symbol:
    ascii=0;
    color=color_to_attr(curses.COLOR_MAGENTA);
    def __init__(self, char, attr=(color_to_attr(curses.COLOR_WHITE) + curses.A_BOLD)):
        if curses.ascii.isascii(char):
            self.ascii=ord(char);
            self.color=attr;
        else:
            print "Error in symbol: invalid character or string";

def printsymb(x, y, symb):
    if curses.has_colors():
        screen.addch(LINES-y-2, x, symb.ascii, symb.color);
    else:
        screen.addch(LINES-y-2, x, symb.ascii);

mapWidth = COLUMNS;
mapHeight = LINES-messLines-1;    

#define tiles
EMPTY_SPACE = symbol(".", GRAY);
WALL = symbol("#", WHITE);
UP_STAIR = symbol("<", WHITE);
DOWN_STAIR = symbol(">", WHITE);
CHAR_SYMB=symbol("@", BOLD_BLUE);
ERROR_SYMB=symbol("?", ALERT_COLOR);

mapPositions=[(x, y) for x in range(mapWidth) for y in range(mapHeight)];

def score(actor, points):
    actor.addScore(points);

itemList = {
    "%":BROWN,
    "$":YELLOW,
    "*":ALERT_COLOR,
    "(":GRAY,
    "[":GRAY,
    "!":ALERT_COLOR
};

for asc, col in itemList.items():
    itemList[asc] = symbol(asc, col);

def itemsymbol(itm):
    if itm=="*":
        return symbol("*", random.choice((BOLD_GREEN, BOLD_BLUE, BOLD_RED, WHITE, YELLOW, GRAY)));
    elif itm in itemList:
        return itemList[itm];
    else:
        return symbol(itm);

monsterList = {
    "ant": BROWN,
    "bat": BROWN,
    "cat": BOLD_GREEN,
    "dog": BROWN,
    };
monsterSymbols = {};
monsterNames={};

for name, col in monsterList.items():
    monsterSymbols[name[0]] = symbol(name[0], col);

for name in monsterList:
    monsterNames[name[0]] = name;

def monstersymbol(mon):
    if mon in monsterSymbols:
        return monsterSymbols[mon];
    else:
        return symbol(mon);

def monstername(mon):
    if mon in monsterNames:
        return monsterNames[mon];
    else:
        return "ErrorMonsterName";      

class level:
    floormap = None;
    items = {};
    monsters = {};
    upstair = [];
    downstair = [];
    def __init__(self):
        middle = [WALL]+[EMPTY_SPACE]*(mapWidth-2)+[WALL];
        bottom=[WALL]*(mapWidth);
        top=bottom[:];
        self.floormap=[top]+[middle]*(mapHeight-2)+[bottom];
        self.floormap=deepcopylist(self.floormap,2);
        self.additem("%");
        self.additem("$");
        self.additem("(");
        self.additem("[");
        self.additem("*");
        self.monsters[(1,1)]=monster("a");
        self.upstair = [(3, 3, 0)];
        self.downstair = [(10, 10, 2)];
        for up_stair in self.upstair:
            self.floormap[up_stair[1]][up_stair[0]] = UP_STAIR;
        for down_stair in self.downstair:
            self.floormap[down_stair[1]][down_stair[0]]=DOWN_STAIR;
    def additem(self, item):
        space = self.randomUnfilledSpace();
        self.items[space]=item;
    def addmonster(self, monster):
        space = self.randomUnoccupiedSpace();
        self.monsters[space]=monster;
    def randomSpace(self):
        while 1:
            x=random.randrange(mapWidth);
            y=random.randrange(mapHeight);
            if self.solid(x,y):
                continue;
            else:
                return (x,y);
    def randomUnoccupiedSpace(self):
        while 1:
            space=self.randomSpace();
            x,y=space;
            if self.isOccupied(x,y):
                continue;
            else:
                return space;
    def randomUnfilledSpace(self):
        while 1:
            space=self.randomSpace();
            x,y=space;
            if self.itemPresent(x,y):
                continue;
            else:
                return space;
    def printsquare(self,x,y):
        symb = ERROR_SYMB;
        if self.monsterPresent(x,y):
            symb=self.monsters[(x,y)].symb();
        elif self.itemPresent(x,y):
            symb=itemsymbol(self.item(x,y));
        else:
            symb=self.floormap[y][x];
        printsymb(x, y, symb);
    def printmap(self):
        for x,y in mapPositions:
            self.printsquare(x,y);
    def solid(self, x, y):
        return self.floormap[y][x]==WALL;
    def monsterPresent(self, x, y):
        return (x, y) in self.monsters;
    def hitMonster(self, x, y, actor, power):
        if self.monsterPresent(x,y):
            self.monsters[(x,y)].getHit(actor, power);
            if not self.monsters[(x,y)].alive():
                del self.monsters[(x,y)];
        else:
            print "Error, no monster present on that square (", x, ", ", y, ") ";
    def itemPresent(self, x, y):
        return (x, y) in self.items;
    def isOccupied(self,x,y):
        if self.monsterPresent(x,y):
            return True;
        elif heroPresent(x,y):
            return True;
        else:
            return False;
    def item(self, x, y):
        if self.itemPresent(x,y):
            return self.items[(x, y)];
        else:
            print "Illegal item access: item not present at ",x,y;
            return "!";
    def takeItem(self, x, y):
        tempItem = self.items[(x,y)];
        del self.items[(x,y)];
        return tempItem;
    def empty(self, x, y):
        if self.floormap != EMPTY_SPACE:
            return False;
        elif self.monsterPresent(x,y):
            return False;
        elif self.itemPresent(x,y):
            return False;
        elif heroPresent(x,y):
            return False;
        else:
            return True;

class monster:
    hp = 1;
    power = 0;
    asc=None;
    def __init__(self, x):
        self.asc=x;
        self.hp=ord(x)-ord("a")+1;
        self.power = max((self.hp+2) // 4, 1);
    def name(self):
        return monstername(self.asc);
    def symb(self):
        x=monstersymbol(asc);
        return monstersymbol(self.asc);
    def alive(self):
        return (self.hp > 0);
    def getHit(self, actor, power):
        self.hp -= max(0,power);
        message("You hit the "+self.name()+" for " + pprint.pformat(power) + " damage.");
        message("It has " + pprint.pformat(self.hp) + " HP remaining.");
        if not self.alive():
            message("The " + self.name() + " dies.");
            score(actor, 1);

def itemscore(item):
    if item=="@":
        return 1;
    elif item=="#":
        return 1;
    elif item=="$":
        return 1;
    elif item=="%":
        return 1;
    elif item=="*":
        return 2;
    elif item=="(":
        return 1;
    elif item=="[":
        return 1;
    else:
        print "Illegal scoring item";
        return 0;

class character:
    xpos = 4;
    ypos = 4;
    level = 1;
    state = {"@":0, "#":0, "$":0, "%":0, "*":0, "(":0, "[":0, "!":0, "?":0};
    alive=True;
    def __init__(self):
        self.addItem("@",3);
        self.addItem("%",1);
        self.addItem("(");
        self.addItem("[");
        self.addScore(1); #for living
    def addItem(self, item, amount=1):
        if item in self.state:
            self.state[item] += amount;
            if item!= "!" and item != "?":
                self.addScore(amount*itemscore(item))
            if item=="@":
                self.addItem("#", amount); #max health increases current health
            if item=="#":
                if self.state["#"] <= 0:
                    self.alive=False;
                    self.addScore(-1);
                    message("You die.");
        else:
            print "Error, that is not a valid item";
    def removeItem(self,item,amount):
        self.addItem(item, -amount);
    def printself(self):
        printsymb(self.xpos, self.ypos, CHAR_SYMB);
    def power(self):
        return max(1, self.state["("]);
    def getHit(self,pow):
        damage = max(0, pow-self.state["["]);
        self.removeItem("#", damage);
    def addScore(self,points):
        self.addItem("!", points);

hero = character();
def heroPresent(x, y):
    if x==hero.xpos:
        if y==hero.ypos:
            return True;
    return False;

def printhero():
    global cursorxpos;
    global cursorypos;
    
    hero.printself();
    cursorxpos=hero.xpos;
    cursorypos=LINES-hero.ypos-2;

idealTokenLength = COLUMNS // len(hero.state);
if debug:
    idealTokenLength=0;
def printstatus():
    pieces=[];
    spacer = " ";
    for elt, val in hero.state.items():
        token=elt + ": " + pprint.pformat(val);
        token += " " * max(0, idealTokenLength-len(token));
        pieces.append(token);
    if pieces==[]:
        print "error, no status line";
    else:
        line = ''.join(pieces);
        if debug:
            line = line + " L" + pprint.pformat(hero.level);
            line = line + " X" + pprint.pformat(hero.xpos);
            line = line + " Y" + pprint.pformat(hero.ypos);
            line = line + " I" + pprint.pformat(debid);
        setstatusline(line);

def printmap():
    curlevel.printmap();
def printmappart(x,y):
    for a in (x-1,x,x+1):
        for b in (y-1, y, y+1):
            curlevel.printsquare(a,b);
    
    

#define the moves
LEFT, RIGHT, DOWN, UP, DEPTH_DOWN, DEPTH_UP, WAIT, HELP, QUIT = range(9);

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
 };

def getAction():
    key=getkey();
    while (key not in standardKeys):
        key = getkey();
    return standardKeys[key];

moveVectors = {
 LEFT:(-1,0,0),
 RIGHT:(1,0,0),
 DOWN:(0,-1,0),
 UP:(0,1,0),
 DEPTH_DOWN:(0,0,-1),
 DEPTH_UP:(0,0,1),
 WAIT:(0,0,0)
 };
 
curlevel = level();

printmap();
action = None;
while(hero.alive and action != QUIT):
    printstatus();
    printmappart(hero.xpos,hero.ypos);
    printhero();
    update();
    clearmessage(); #This is a soft clear
            
    action=getAction();
    if action==HELP:
        message("Volcano version 0.0.1");
        continue;
    elif action == QUIT:
        message("You quit.");
        break;
    elif action in moveVectors:
        vector = moveVectors[action];
        if action != WAIT:
            if vector[2] == 0:
                newxPos = hero.xpos + vector[0];
                newyPos = hero.ypos + vector[1];
                if curlevel.solid(newxPos,newyPos):
                    message("Ouch!");
                    continue;
                else:
                    if curlevel.monsterPresent(newxPos, newyPos):
                        #hit the monster
                        curlevel.hitMonster(newxPos, newyPos, hero, hero.power());
                    else:
                        hero.xpos = newxPos;
                        hero.ypos = newyPos;
                        if curlevel.itemPresent(newxPos, newyPos):
                            gotten=curlevel.takeItem(newxPos, newyPos);
                            hero.addItem(gotten);
                            message("You pick it up.");
            else:
                message("You can't walk that way?");
        else:
            message("Zzz...");
    else:
        print "Error, illegal action.";
        break;
    hero.addItem("?"); #Add a turn

message("Game Over.");
update();
anykey();

closescreen();