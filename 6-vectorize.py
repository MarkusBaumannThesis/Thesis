import os, sys, pickle, numpy, random
from gensim.models import Word2Vec
from source_code_tokenizer import JavaTokenizer
import h5py
from tqdm import tqdm

#default mode / type of vulnerability
vulType = "brute force-proof"

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
  vulType = sys.argv[1]
print('vulnerability type given as {}'.format(vulType))

# word2vec model parameters to be loaded
mincount = 10 # minimum times a word has to appear in the corpus to be in the model
iterations = 100 # training iterations for the word2vec model (epochs)
size = 200 # size (dimensions) of the word2vec model

# get word2vec path
w2vPath = "word2vecs-full/word2vec_" + str(mincount) + "-" + str(iterations) + "-" + str(size) + ".model"

# exit if model not present
if not (os.path.isfile(w2vPath)):
  print("word2vec model is still being created...")
  sys.exit()
  
# load word2vec model
w2vModel = Word2Vec.load(w2vPath)
word_vectors = w2vModel.wv

with open ('trainingSet', 'rb') as fp:
    trainingSet = pickle.load(fp)

with open ('testingSet', 'rb') as fp:
    testingSet = pickle.load(fp)

TrainX = []
TrainY = []
TestX = []
TestY = []

def __tokenizeMethod__(column):
    try:
        values = JavaTokenizer().tokenize(column)
    except Exception:
        print("error")
        return None
    vectorlist = []
    for token, _ in values:
        if token in word_vectors.index_to_key and token != " ":
            vector = w2vModel.wv.get_vector(token)
            vectorlist.append(vector.tolist())
    return vectorlist

datasetName = 'dataset-' + str(vulType) + '.h5'
# Open an HDF5 file for writing
def __vectorizeToFile__():
    with h5py.File(datasetName, 'w') as h5_file:

        vectorSize = word_vectors.vector_size

        # Create datasets with placeholders for Train and Test data
        # We don't know the second dimension (number of tokens) ahead of time, so we use None in maxshape.
        h5_file.create_dataset('TrainX', shape=(0, 0, vectorSize), maxshape=(None, None, vectorSize), dtype='float32')
        h5_file.create_dataset('TrainY', shape=(0,), maxshape=(None,), dtype='int32')
        h5_file.create_dataset('TestX', shape=(0, 0, vectorSize), maxshape=(None, None, vectorSize), dtype='float32')
        h5_file.create_dataset('TestY', shape=(0,), maxshape=(None,), dtype='int32')

        # Process the training data in batches
        train_idx = 0
        currentLenTrain = 0
        zeroToken = numpy.zeros((200,), dtype='float32')
        for entry in tqdm(trainingSet):
            # Process vulnerable and safe samples
            vlVul = __tokenizeMethod__(entry[1])
            if vlVul is not None:
                # Resize datasets to accommodate new data
                if len(vlVul) > currentLenTrain:
                    currentLenTrain = len(vlVul)
                else:
                    while len(vlVul) < currentLenTrain:
                        vlVul.append(zeroToken)
                h5_file['TrainX'].resize((train_idx+1, currentLenTrain, vectorSize))
                h5_file['TrainX'][train_idx] = vlVul
                h5_file['TrainY'].resize((train_idx+1,))
                h5_file['TrainY'][train_idx] = 1  # Vulnerable
                train_idx += 1
            
            vlSafe = __tokenizeMethod__(entry[2])
            if vlSafe is not None:
                if len(vlSafe) > currentLenTrain:
                    currentLenTrain = len(vlSafe)
                else:
                    while len(vlSafe) < currentLenTrain:
                        vlSafe.append(zeroToken)
                h5_file['TrainX'].resize((train_idx+1, currentLenTrain, vectorSize))
                h5_file['TrainX'][train_idx] = vlSafe
                h5_file['TrainY'].resize((train_idx+1,))
                h5_file['TrainY'][train_idx] = random.randint(0, 1)  # Not Vulnerable
                train_idx += 1

        # Process the testing data in batches
        test_idx = 0
        currentLenTest = 0
        for entry in tqdm(testingSet):
            # Process vulnerable and safe samples
            vlVul = __tokenizeMethod__(entry[1])
            if vlVul is not None:
                if len(vlVul) > currentLenTest:
                    currentLenTest = len(vlVul)
                else:
                    while len(vlVul) < currentLenTest:
                        vlVul.append(zeroToken)
                h5_file['TestX'].resize((test_idx+1, currentLenTest, vectorSize))
                h5_file['TestX'][test_idx] = vlVul
                h5_file['TestY'].resize((test_idx+1,))
                h5_file['TestY'][test_idx] = 1  # Vulnerable
                test_idx += 1

            vlSafe = __tokenizeMethod__(entry[2])
            if vlSafe is not None:
                if len(vlSafe) > currentLenTest:
                    currentLenTest = len(vlSafe)
                else:
                    while len(vlSafe) < currentLenTest:
                        vlSafe.append(zeroToken)
                h5_file['TestX'].resize((test_idx+1, currentLenTest, vectorSize))
                h5_file['TestX'][test_idx] = vlSafe
                h5_file['TestY'].resize((test_idx+1,))
                h5_file['TestY'][test_idx] = random.randint(0, 1)  # Not Vulnerable
                test_idx += 1

if (not os.path.isfile(datasetName)):
    print("vectorizing datasets ...")
    __vectorizeToFile__()
    print("datasets vectorized.")
else:
    print("vectorized dataset already exists. make sure to backup it before running this script again. Exiting ...")