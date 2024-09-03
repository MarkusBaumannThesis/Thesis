import utils, sys, pickle, numpy
from keras.models import load_model
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# vulnerability Type should match the model

#default mode / type of vulnerability
vulType = "brute force-proof"

# default model, some arbitrary one
loadModel = "LSTM-model_vulType-bruteforce-proof_neurons-100_optimizer-adam_epochs-10_batchsize-128_time-2024-09-03-20-12"

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  vulType = sys.argv[1]
print('vulnerability type given as {}'.format(vulType))

#get the model from the command line argument
if (len(sys.argv) > 2):
  loadModel = sys.argv[2]
print('model type given as {}'.format(loadModel))

size = 200 #dimensions of the word2vec model
datasetName = 'dataset-' + str(vulType) + '.h5'

dropout = 0.2
neurons = 100
optimizer = "adam"
epochs = 100
batchsize = 128

try:
  model = load_model("model/{}.h5".format(loadModel), custom_objects={'f1Score_lossFunction': utils.f1Score_lossFunction, 'f1Score': utils.f1Score})
except ValueError:
   # older model versions
   model = load_model("model/{}.h5".format(loadModel), custom_objects={'f1_loss': utils.f1Score_lossFunction, 'f1': utils.f1Score})

TrainX, TrainY, TestX, TestY = utils.__loadDataFromH5PY__(datasetName)

utils.__printInfo__(TrainX, TrainY, TestX, TestY, size)

print("Now predicting on training set (" + str(dropout) + " dropout)")
y_train = model.predict(TrainX, verbose=1)
y_pred_train = numpy.where(y_train > 0.5, 1,0)
cm_train = confusion_matrix(TrainY, y_pred_train , normalize='pred')
print(y_train)

print("Now predicting on test set (" + str(dropout) + " dropout)")
y_test = model.predict(TestX, verbose=1)
y_pred_test = numpy.where(y_test > 0.5, 1,0)
cm_test = confusion_matrix(TestY, y_pred_test , normalize='pred')
print(y_test)

with open('/trainHistoryDict', "rb") as file_pi:
    history = pickle.load(file_pi)

disp1 = ConfusionMatrixDisplay(confusion_matrix=cm_train)
disp1.plot()
plt.show()

disp2 = ConfusionMatrixDisplay(confusion_matrix=cm_test)
disp2.plot()
plt.show()

train_acc = accuracy_score(TrainY, y_pred_train)
test_acc = accuracy_score(TestY, y_pred_test)

#validate data on train and test set
# list all data in history
print(history.keys())
# summarize history for accuracy
plt.plot(history['binary_accuracy'])
plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train'], loc='upper left')
plt.show()

# summarize history for accuracy
plt.plot(history['loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train'], loc='upper left')
plt.show()

# summarize history for accuracy
plt.plot(history['f1Score'])
plt.title('model F1 scope')
plt.ylabel('f1 Score')
plt.xlabel('epoch')
plt.legend(['train'], loc='upper left')
plt.show()