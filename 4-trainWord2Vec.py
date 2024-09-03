import nltk
from gensim.models import Word2Vec
import os.path
import pickle
from alive_progress import alive_bar

allWords = []

# Loading the tokenized corpus 
with open('D:/dev/glos/tokenized.txt', 'r', encoding="utf-8") as inputFile:
    tokenized = inputFile.read().lower().replace('\n', ' ')

print("Length of the training file: " + str(len(tokenized)) + ".")
print("It contains " + str(tokenized.count(" ")) + " individual code tokens.")

# Preparing the dataset (or loading already processed dataset to not do everything again)
if (os.path.isfile('trainedModelOnlyWords')):
  with open ('trainedModelOnlyWords', 'rb') as buffer:
    allWords = pickle.load(buffer)
  print("loaded processed model.")
else:  
  print("now processing...")
  with alive_bar():
    allWords = nltk.word_tokenize(tokenized)
  print("saving")
  with open('trainedModelOnlyWords', 'wb') as buffer:
    pickle.dump(allWords, buffer)

print("processed.\n")

for mincount in [10,30,50,100,300,500,5000]:
  for iterations in [1,5,10,30,50,100]:
    for size in [5,10,15,30,50,75,100,200,300]:

      print("\n\n W2V model with min count " + str(mincount) + " and " + str(iterations) + " Iterationen and size " + str(size))
      fname = "word2vecs-onlyWords/word2vec_" + str(mincount) + "-" + str(iterations) +"-" + str(size)+ ".model"

      if (os.path.isfile(fname)):
        print("model already exists.")

      else:
        print("calculating model...")
        # training the model
        model = Word2Vec(allWords, vector_size=size, min_count=mincount, epochs=iterations, workers = 4)  

        #saving the model
        with open(fname, 'wb') as file:
          model.save(file)



