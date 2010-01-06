from __future__ import division

def interesting(x,y):
    return hash(x) <= hash(y)

memos={}

def interestingtwotrees(size):
    if size in memos:
        return memos[size]
    if size == 1:
        return ((),)
    elif size==2:
        return ()
    else:
        collection = set()
        for i in range(1,size-1):
            for x in interestingtwotrees(i):
                for y in interestingtwotrees(size-1-i):
                    if interesting(x,y):
                        collection.add((x,y))
        memos[size]=tuple(collection)
        return interestingtwotrees(size)


def interestingdangleabletrees(size):
    all=list(interestingtwotrees(size-1))
    return tuple([(x,) for x in all])        

def leftOrder(tree):
    if len(tree) == 0:
        return tree
    elif len(tree) == 1:
        return (leftOrder(tree[0]),)
    else:
        leftSubtree=tree[0]
        rightSubtree=tree[1]
        if hash(leftSubtree) < hash(rightSubtree):
            return (leftOrder(leftSubtree),leftOrder(rightSubtree))
        else:
            return (leftOrder(rightSubtree),leftOrder(leftSubtree))

def sizeof(tree):
    if tree==():
        return 1
    elif len(tree)==0:
        return sizeof(tree[0])+1
    else:
        return sizeof(tree[0])+sizeof(tree[1])+1

def depth(tree):
    if len(tree)==0:
        return 1
    else:
        return 1+max([depth(a) for a in tree])

def dangleable(tree):
    if len(tree)==1:
        if twotree(tree[0]):
            return True
        else:
            return False
    else:
        return False

def twotree(tree):
    if len(tree)==0:
        return True
    elif len(tree)==1:
        return False
    else:
        return twotree(tree[0]) and twotree(tree[1])

def dangle(treeC, node):
    if node==0:
        return treeC
    else:
        return danglehelp(treeC[0], node-1, ())
def danglehelp(treeC, node, extraTree):
    if node==0:
        #treeC==()
        return (extraTree,)
    else:
        #len(treeC)==2
        #go down left of right branch
        left=treeC[0]
        right=treeC[1]
        leftSize=sizeof(left)
        if node <= leftSize:
            return danglehelp(left, node-1, (right, extraTree,) )
        else:
            return danglehelp(right, node-leftSize-1, (extraTree, left,) )

def dangleableNodes(treeC):
    return (0,) + dangleableHelper(treeC[0],1)  
def dangleableHelper(treeC, offset):
    if treeC==():
        return (offset,)
    else:
        left=treeC[0]
        right=treeC[1]
        return  dangleableHelper(left,offset+1) \
            +   dangleableHelper(right,offset+sizeof(left)+1)

def equivtree(treeA, treeB):
    for node in dangleableNodes(treeB):
        treeC = dangle(treeB,node)
        if leftOrder(treeA)==leftOrder(treeC):
            return True
    return False #Probably

def uniquedangleabletrees(size):
    all = list(interestingdangleabletrees(size))
    unique=[]
    for a in all:
        for b in unique:
            if equivtree(a, b):
                break
        else:
            unique.append(a)
    return tuple(unique)

size=8
all=interestingdangleabletrees(size)
#for x in all:
#    print x
unique = uniquedangleabletrees(size)
print
for x in unique:
    print x
print len(all), " total", len(unique), " unique"
print all
print unique

def depths(x):
    return map(lambda node: depth(dangle(x,node)), dangleableNodes(x))
def median(x):
    x.sort()
    halfway=len(x)//2
    if len(x)%2==0:
        return (x[halfway]+x[halfway+1])/2
    else:
        return x[halfway]
def mean(x):
    return sum(x) / len(x)
def better(x,y):
    def value(x):
        return (lambda y: y.count(8))(depths(x))
    if value(x)>value(y):
        return x
    else:
        print y, value(y)
        return y
best=reduce(better, unique)
print "Best found:"
print best

dungeon=(((), ((), ((((), ()), ()), ((((), ()), ((), ())), (((), ()), ((), ())))))),)
print dungeon
print depths(dungeon)
print "Max", max(depths(dungeon))
print "Min", min(depths(dungeon))
print "Range", max(depths(dungeon))-min(depths(dungeon))
print "Mean", mean(depths(dungeon))
print "Median", median(depths(dungeon))
print len(dangleableNodes(dungeon))
print dangleableNodes(dungeon)

dangledTrees = list(set([leftOrder(dangle(dungeon, node)) for node in dangleableNodes(dungeon)]))
print len(dangledTrees)
print dangledTrees

def atDepth(tree, depth):
    if depth==0:
        return 1
    else:
        total=0
        for subtree in tree:
            total += atDepth(subtree, depth-1)
        return total

for dun in [ 
    (((), ((), ((((), ()), ()), ((((), ()), ((), ())), (((), ()), ((), ())))))),),  #depth
    ((((), ()), ((((), ()), ()), ((((), ()), ((), ())), (((), ()), ((), ()))))),),  #depth
    (((((), ()), (((((), ()), ()), (((), ()), ())), (((), ()), ((), ())))), ()),)   #depth
    ]:
        print dun
        maxdepth = depth(dun)
        for d in range(maxdepth):
            print "Depth ", d, "\t Levels ", atDepth(dun, d)