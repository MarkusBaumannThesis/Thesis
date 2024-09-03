from source_code_tokenizer import JavaTokenizer

inputString = ""
with open('tokenizerCorpus.txt', 'r', encoding="utf-8") as inputFile:
    inputString = inputFile.read()

tokenized = JavaTokenizer().tokenize(inputString)

with open('tokenized.txt', 'w', encoding="utf-8") as outfile:
    for value, key in tokenized:
        outfile.write(f"{value}\n")
