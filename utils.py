from keras import backend as K
import tensorflow as tf
import h5py

def getTokens(change):
    tokens = []  

    change = change.replace(" .",".")
    change = change.replace(" ,",",")
    change = change.replace(" )",")")
    change = change.replace(" (","(")
    change = change.replace(" ]","]")
    change = change.replace(" [","[")
    change = change.replace(" {","{")
    change = change.replace(" }","}")
    change = change.replace(" :",":")
    change = change.replace("- ","-")
    change = change.replace("+ ","+")
    change = change.replace(" =","=")
    change = change.replace("= ","=")
    splitchars = [" ","\t","\n", ".", ":", "(", ")", "[", "]", "<", ">", "+", "-", "=","\"", "\'","*", "/","\\","~","{","}","!","?","*",";",",","%","&"]
    start = 0
    end = 0
    for i in range(0, len(change)):
        if change[i] in splitchars:
            if i > start:
                start = start+1
                end = i
                if start == 1:
                    token = change[:end]
                else:
                    token = change[start:end]
                if len(token) > 0:
                    tokens.append(token)
                tokens.append(change[i])
                start = i
    return(tokens)

#Define F1 loss and measurement

def f1Score_lossFunction(y_true, y_pred):
    
    truePositives = K.sum(K.cast(float(y_true)*y_pred, 'float'), axis=0)
    #trueNegatives = K.sum(K.cast((1-float(y_true))*(1-y_pred), 'float'), axis=0)
    falsePositives = K.sum(K.cast((1-float(y_true))*y_pred, 'float'), axis=0)
    falseNegatives = K.sum(K.cast(float(y_true)*(1-y_pred), 'float'), axis=0)

    precision = truePositives / (truePositives + falsePositives + K.epsilon())
    recall = truePositives / (truePositives + falseNegatives + K.epsilon())

    f1 = 2*precision*recall / (precision+recall+K.epsilon())
    f1 = tf.where(tf.math.is_nan(f1), tf.zeros_like(f1), f1)
    return 1 - K.mean(f1)

def __recall__(y_true, y_pred):
        truePositives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        allPositives = K.sum(K.round(K.clip(y_true, 0, 1)))
        recall = truePositives / (allPositives + K.epsilon())
        return recall

def __precision__(y_true, y_pred):
        truePositives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
        allPositives = K.sum(K.round(K.clip(y_pred, 0, 1)))
        precision = truePositives / (allPositives + K.epsilon())
        return precision

def f1Score(y_true, y_pred):
    precision = __precision__(y_true, y_pred)
    recall = __recall__(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

def __loadDataFromH5PY__(datasetName):
    with h5py.File(datasetName, 'r') as h5_file:
        # Load the datasets into numpy arrays
        X1 = h5_file['TrainX'][:]
        Y1 = h5_file['TrainY'][:]
        X2 = h5_file['TestX'][:]
        Y2 = h5_file['TestY'][:]

    print("datasets loaded.")

    return X1, Y1, X2, Y2

def __printInfo__(TrainX, TrainY, TestX, TestY, size):

    lenEntryTrain = 0
    for entry in TrainX:
        if len(entry) > lenEntryTrain:
            lenEntryTrain = len(entry)

    lenEntryTest = 0
    for entry in TestX:
        if len(entry) > lenEntryTest:
            lenEntryTest = len(entry)

    print("Training Set:")
    print(str(len(TrainX)) + " samples in the TrainX, each sample padded to " + str(lenEntryTrain) + " tokens, each of which is " + str(size) + "-dimensional.")
    print(str(len(TrainY)) + " samples in the TrainY.\n")
    print("Test Set:")
    print(str(len(TestX)) + " samples in the TestX, each sample padded to " + str(lenEntryTest) + " tokens, each of which is " + str(size) + "-dimensional.")
    print(str(len(TestY)) + " samples in the TestY.")
