import utils, sys, pickle
from datetime import datetime
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras import metrics

#default mode / type of vulnerability
vulType = "brute force-proof"

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  vulType = sys.argv[1]
print('vulnerability type given as {}'.format(vulType))

size = 200 #dimensions of the word2vec model
datasetName = 'dataset-' + str(vulType) + '.h5'

# Load data
TrainX, TrainY, TestX, TestY = utils.__loadDataFromH5PY__(datasetName)

utils.__printInfo__(TrainX, TrainY, TestX, TestY, size)

csum = 0
for a in TrainY:
  csum = csum+a
print("percentage of vulnerable samples: "  + str(int((csum / len(TrainX)) * 10000)/100) + "%")
  
testvul = 0
for y in TestY:
  if y == 1:
    testvul = testvul+1
print("absolute amount of vulnerable samples in test set: " + str(testvul))

#hyperparameters for the LSTM model

dropout = 0.2
neurons = 100
optimizer = "adam"
epochs = 10
batchsize = 128

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("Starting LSTM: ", nowformat)


print("Dropout: " + str(dropout))
print("Neurons: " + str(neurons))
print("Optimizer: " + optimizer)
print("Epochs: " + str(epochs))
print("Batch Size: " + str(batchsize))
print("max length: " + str(size))

#creating the model  
model = Sequential()
model.add(LSTM(neurons, dropout = dropout, recurrent_dropout = dropout)) #around 50 seems good
model.add(Dense(1, activation='sigmoid'))
model.compile(loss=utils.f1Score_lossFunction, optimizer='adam', metrics=[utils.f1Score, metrics.binary_accuracy])

now = datetime.now() # current date and time
nowformat = now.strftime("%H:%M")
print("Compiled LSTM: ", nowformat)

#training the model
history = model.fit(TrainX, TrainY, epochs=epochs, batch_size=batchsize)

# saving history for later use
with open('/trainHistoryDict', 'wb') as file_pi:
    pickle.dump(history.history, file_pi)

now = datetime.now()
nowtime = now.strftime("%H-%M")
nowdate = now.date()
print("saving LSTM model. ", nowtime)
model.save('model/LSTM-model_vulType-{}_neurons-{}_optimizer-{}_epochs-{}_batchsize-{}_time-{}-{}.h5'.format(vulType, neurons, optimizer, epochs, batchsize, str(nowdate), str(nowtime)))
print("\n\n")