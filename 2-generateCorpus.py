from pydriller import Repository
import re

urls = ["https://github.com/iluwatar/java-design-patterns", "https://github.com/spring-projects/spring-framework", "https://github.com/openjdk/jdk", "https://github.com/JetBrains/JetBrainsRuntime"]

def __prepareMethod__(sourceCode):

    sourceClean = ""
    
    for line in sourceCode:

        line = line.strip()

        # normalize strings
        regex = re.compile(r'''"([^"\\\n]|\\(['"?\\abfnrtv]|[0-7]{1,3}|x[0-9a-fA-F]+))*"''')
        line = regex.sub('"string"', line)

        # ignore comment (//), javadoc (/* and *), import, and package lines
        regex = re.compile('^//|^/\*|^\*|^import|^package')
        if re.match(regex, line):
            continue

        # remove inline comments
        regex = re.compile('//.*$')
        line = regex.sub('', line)

        # remove inline javadoc comments
        regex = re.compile('/\*.*$')
        line = regex.sub('', line)

        # replace string escape character '"' with 'stringEscapceChar' (otherwise tokenizer in 3-tokenizeCorpus.py explodes)
        regex = re.compile(r'''\'(")\'''')
        line = regex.sub('\'stringEscapeChar\'', line)

        sourceClean = sourceClean + " " + line

    return sourceClean

#####################################################################

tokenizerCorpus = ""

for url in urls:
    
    files = []
    repo = Repository(url)
    repoName = repo._get_repo_name_from_url(url)

    for commit in repo.traverse_commits():

        for modified_file in commit.modified_files:

            filename = modified_file.filename
            
            # disregard deleted files
            if filename is None:
                continue
            
            # disregard non-Java files
            if (".java" not in filename):
                continue
            
            # disregard already present files
            if filename in files:
                continue
            
            sourceCode = modified_file.source_code

            # disregard empty files
            if sourceCode is None:
                continue

            # clean up source code
            sourceCode = sourceCode.splitlines();
            sourceCode = __prepareMethod__(sourceCode)
            print("fin " + repoName + " " + filename)

            tokenizerCorpus = tokenizerCorpus + "\n\n" + sourceCode
            files.append(filename)
        

    try:
        with open('tokenizerCorpus.txt', "w", encoding="utf-8") as corpusFile:
            corpusFile.write(tokenizerCorpus)
    except UnicodeEncodeError:
        print("failed to write due to UnicodeEncodeError. Sucks to be you.")