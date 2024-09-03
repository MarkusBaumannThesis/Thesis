import os, sys, csv, pickle

#default mode / type of vulnerability
vulType = "brute force"

# default max character count for methods to be considered
maxMethodLen = 10000

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  vulType = sys.argv[1]
print('vulnerability type given as {}'.format(vulType))

path = '/dev/glos/repos'

# split the Data
trainingSet = []
testingSet = []
idxEmptyTotal = 0
idxTooLargeTotal = 0
idxMatchesKeyword = 0
idxSuccess = 0
idxTotal = 0
for filename in os.listdir(path):

    # input assurance
    if not filename.startswith('repo-') or not filename.endswith('.csv'):
        continue

    # just for testing
    #if filename != 'repo-test.csv':
    #    continue

    # split training and testing sets
    with open(os.path.join(path, filename), 'r') as csvinput:

        reader = csv.reader(csvinput, delimiter=";")
        idxEmpty = 0
        idxTooLarge = 0
        for row in list(reader):
            idxTotal = idxTotal + 1

            # skip rows where pre or post method is empty for some reason
            if not row[3] or not row[4]:
                idxEmpty = idxEmpty + 1
                continue

            # skip rows where pre or post method exceeds a given maximum length (to prevent a few bad methods to blow up vectorization. Should also be removed during code-window-version)
            if len(row[3]) > maxMethodLen or len(row[4]) > maxMethodLen:
                idxTooLarge = idxTooLarge + 1
                continue

            if vulType in row[2]:
                idxMatchesKeyword = idxMatchesKeyword + 1
                if row[5] == "True":
                    tup = tuple(row)
                    entry = [tup[2], tup[3], tup[4]]
                    trainingSet.append(entry)
                    idxSuccess = idxSuccess + 1
                elif row[5] == "False":
                    tup = tuple(row)
                    entry = [tup[2], tup[3], tup[4]]
                    testingSet.append(entry)
                    idxSuccess = idxSuccess + 1
        
        if idxEmpty != 0:
            idxEmptyTotal = idxEmptyTotal + idxEmpty
            print("skipped " + str(idxEmpty) + " empty methods.")
        if idxTooLarge != 0:
            idxTooLargeTotal = idxTooLargeTotal + idxTooLarge
            print("skipped " + str(idxTooLarge) + " methods that exceed max character count " + str(maxMethodLen) + ".")
print("Total amount of skipped empty methods: " + str(idxEmptyTotal))
print("Total amount of skipped too large methods: " + str(idxTooLargeTotal))
print("Total amount of methods that hit a keyword: " + str(idxMatchesKeyword))
print("Total amount of non-skipped methods: " + str(idxSuccess))
print("Total amount of methods: " + str(idxTotal))

with open('trainingSet', 'wb') as fp:
    pickle.dump(trainingSet, fp)

with open('testingSet', 'wb') as fp:
    pickle.dump(testingSet, fp)
