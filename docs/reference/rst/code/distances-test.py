import Orange

# Read some data
table = Orange.data.Table("iris.tab")

# Euclidean distance constructor
d2Constr = Orange.distance.instances.EuclideanConstructor()
d2 = d2Constr(table)

# Constructs 
dPears = Orange.distance.instances.PearsonRConstructor(table)

#reference instance
ref = table[0]

print "Euclidean distances from the first data instance: "

for ins in table[:5]:
    print "%5.4f" % d2(ins, ref),
print 

print "Pearson correlation distance from the first data instance: "

for ins in table[:5]:
    print "%5.4f" % dPears(ins, ref),
print 
