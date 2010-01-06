import curses;
import curses.ascii;
import pprint;

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
DIM_RED = color_to_attr(curses.COLOR_RED) + curses.A_DIM;
BOLD_BLUE = color_to_attr(curses.COLOR_BLUE) + curses.A_BOLD;

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

def getkey():
    return screen.getch();
    
class symbol:
    ascii=0;
    color=color_to_attr(curses.COLOR_MAGENTA);
    def __init__(self, char):
        if curses.ascii.isascii(char):
            self.ascii=ord(char);
            self.color=color_to_attr(curses.COLOR_WHITE) + curses.A_BOLD;
        else:
            print "Error in symbol: invalid character or string";
    def __init__(self, char, attr):
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
CHAR_SYMB=symbol("@", BOLD_BLUE);

mapPositions=[(x, y) for x in range(mapWidth) for y in range(mapHeight)];

class level:
    floormap = None;
    map = None;
    def __init__(self):
        middle = [WALL]+[EMPTY_SPACE]*(mapWidth-2)+[WALL];
        top=bottom=[WALL]*(mapWidth);
        self.map=self.floormap=[top]+[middle]*(mapHeight-2)+[bottom];
    def printmap(self):
        for x,y in mapPositions:
            symb=self.map[y][x];
            printsymb(x, y, symb);
    def isWall(self, x, y):
        return self.floormap[y][x]==WALL;

class character:
    xpos = 4;
    ypos = 4;
    state = {"@":0, "#":0, "$":0, "%":0, "*":0, "(":0, "[":0, "!":0, "?":0};
    alive=True;
    def __init__(self):
        self.add_item("@",3);
        self.add_item("%",1);
        self.add_item("(");
        self.add_item("[");
    def add_item(self, item, amount=1):
        if item in self.state:
            self.state[item] += amount;
            if item=="@":
                self.add_item("#", amount); #max health increases current health
            if item=="#":
                if self.state["#"] <= 0:
                    self.alive=False;
        else:
            print "Error, that is not a valid item";
    def remove_item(self,item,amount):
        self.add_item(item, -amount);
    def printself(self):
        printsymb(self.xpos, self.ypos, CHAR_SYMB);

def printhero():
    global cursorxpos;
    global cursorypos;
    
    hero.printself();
    cursorxpos=hero.xpos;
    cursorypos=LINES-hero.ypos-2;

def printmap():
    curlevel.printmap();

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
 
hero = character();
curlevel = level();

action = None;
while(hero.alive and action != QUIT):
    printmap();
    printhero();
    update();
    clearmessage(); #This is a soft clear
            
    action=getAction();
    if action==HELP:
        message("My, you seem to need a lot of help these days.  But you know what they say, good help is hard to find.  If you want something done right, you just have to do it yourself.");
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
            
                if curlevel.isWall(newxPos,newyPos):
                    message("Ouch!");
                    continue;
                else:
                    hero.xpos = newxPos;
                    hero.ypos = newyPos;
            else:
                message("You can't walk that way?");
        else:
            message("Zzz...");
    else:
        print "Error, illegal action.";
        break;
    
    if not hero.alive:
        message("You have died.");

message("Game Over.");
update();
anykey();

closescreen();

