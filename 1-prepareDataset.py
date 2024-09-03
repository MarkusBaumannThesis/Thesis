from pydriller import Repository
from alive_progress import alive_bar
import csv, re, random, sys
from git.exc import GitCommandError
from typing import List, Dict, Tuple

# default mode for code context creation. valid inputs are "method" or "frame"
contextType = 'method'

# default frame scope in case of contextType "frame"
frameScope = 5

# default max character count for methods to be considered
maxMethodLen = 2000

#get the vulnerability from the command line argument
if (len(sys.argv) > 1):
    contextType = sys.argv[1]
    if contextType != 'method' and contextType != 'frame' and contextType != 'diff':
        print('invalid context type given. Only "method", "frame" or "diff" are valid context types. Ending process ...')
        sys.exit()
print('code context type given as "{}"'.format(contextType))

if contextType == 'diff':
    contextType = 'frame'
    frameScope = 0

if (len(sys.argv) > 2):
    frameScope = int(sys.argv[2])
    print("frame scope set to {}".format(frameScope))

# insert path where repos have been generated to
path = '/dev/glos'
# insert split for training and testing data
trainingPercentage = 0.75

securityKeywordsFullsearch = ["aes", "cbc", "crc", "csrf", "cve", "dmz", "dsa", "dos", "hack", "hash", "hmac", "ldap", "md5", "nss", "nvd", "pgp", "pki", "rbac", "rc4", "rce", "rsa", "salt", "saml", "sha", "snif", "spam", "ssl", "sso", "x509", "xss", "xxe"]

securityKeywords = ["access policy", "access role", "access-policy", "access-role", "accesspolicy", "accessrole", "authentic", "authority", "authoriz", "unauthorized", "unauthorised", "biometric", "black list", "black-list", "blacklist", "blacklist", "buffer overflow", "certificate", "checksum", "cipher", "clearance", "confidentiality", "credential", "crypt", "decode", "defensive programming", "defensive-programming", "denial of service", "denial-of-service", "diffie-hellman", "dotfuscator", "ecdsa", "encode", "escrow", "cross site", "exploit", "firewall", "forge", "forgery", "gss api", "gss-api", "gssapi", "honey pot", "honeypot", "honeypot", "inject", "integrity", "malware", "obfuscat", "openid", "owasp", "password", "pbkdf2", "phishing", "repudiation", "rfc 2898", "rfc-2898", "rfc2898", "rijndael", "rootkit", "sanitiz", "secur", "shell code", "shell-code", "shellcode", "smart assembly", "smart-assembly", "smartassembly", "spnego", "spoofing", "spyware", "steganography", "tampering", "trojan", "unsigned", "violat", "virus", "vulnerability", "vulnerable", "white list", "white-list", "whitelist", "malicious", "directory traversal", "remote code execution", "cross site request forgery","click jack","clickjack","session fixation","cross origin","infinite loop","brute force","buffer overflow","cache overflow","command injection","cross frame scripting","csv injection","eval injection","execution after redirect","format string","path disclosure","function injection","replay attack","session hijacking","smurf","sql injection","flooding","tampering","sanitize","sanitise", "unauthorized", "unauthorised"]

fixingKeywords = ["prevent", "fix", "attack", "protect", "issue", "correct", "update", "improve", "change", "check", "malicious", "insecure", "vulnerable", "vulnerability", "fixed", "bugfix", "bug fix", "bug-fix", "fixing"]

urls = [
    "https://github.com/google/gson",
    "https://github.com/apache/gravitino", 
    "https://github.com/ReactiveX/RxJava", 
    "https://github.com/netty/netty", 
    "https://github.com/jenkinsci/jenkins", 
    "https://github.com/dbeaver/dbeaver", 
    "https://github.com/google/guava", 
    "https://github.com/apache/fury", 
    "https://github.com/apache/rocketmq", 
    "https://github.com/dianping/cat",
    "https://github.com/yuliskov/SmartTube",
    "https://github.com/LMAX-Exchange/disruptor",
    "https://github.com/facebook/fresco",
    "https://github.com/JetBrains/JetBrainsMono",
    "https://github.com/JetBrains/intellij-plugins",
    "https://github.com/JetBrains/xodus",
    "https://github.com/FabricMC/fabric"]

################################################################

class Context:
    def __init__(self, name, startLinePrev, endLinePrev, startLinePost, endLinePost):
        self.name = name
        self.startLinePrev = startLinePrev
        self.endLinePrev = endLinePrev
        self.startLinePost = startLinePost
        self.endLinePost = endLinePost

def __getUnsafeDiffBlocks__(lines):

    diffBlocks: List[Tuple[int, int]] = []
    firstLine = -1
    previousLine = 0
    for line in lines:

        # if this is the first iteration, initialize count variables
        if firstLine == -1:
            firstLine = line[0]
            previousLine = line[0]
            continue
            
        # if the current iteration belongs to the current diffBlock, just note new previousLine and walk forward
        if line[0] == previousLine + 1:
            previousLine = line[0]
            continue

        # consider current diffBlock finished. EXTEND WITH BUFFER (frame scope) IN BOTH DIRECTIONS!!
        diffBlocks.append((max(1, firstLine - frameScope), previousLine + frameScope))
        # then reset count variables
        firstLine = line[0]
        previousLine = line[0]
    
    # append this last block of changes, as it is disregarded during the loop because we only ever look for a previous line
    diffBlocks.append((max(1, firstLine - frameScope), previousLine + frameScope))

    return diffBlocks

def __getDiffBlocks__(diff: Dict[str, List[Tuple[int, str]]], value):
    
    diffBlocks: List[Tuple[int, int]] = []
    lines = diff.get(value)

    # auxiliary solution to diffs where things don't get changed, but only added or deleted: create the complementary list ("added" in case of "deleted" and "deleted" in case of "added", then fill diffBlocks with tuples that start and end at the complementary tuple's beginning, adjusted for the frame scope). Shouldn't run into loop-problems because "added" and "deleted" can't both be empty. Using an extracted unchecked version of getDiffBlocks anyway, just to be sure.
    if not lines:
        if value == "added":
            compValue = "deleted"
        else:
            compValue = "added"

        compLines = diff.get(compValue)
        compDiffBlocks = __getUnsafeDiffBlocks__(compLines)

        for block in compDiffBlocks:
            diffBlocks.append((max(1, block[0] - frameScope), block[0] + frameScope))
        return diffBlocks
    
    diffBlocks = __getUnsafeDiffBlocks__(lines)
    return diffBlocks

def __getCombinedContexts__(prevContexts, postContexts):
    contexts = []
    for postContext in postContexts:
        for prevContext in prevContexts:
            if postContext.name == prevContext.name:
                context = Context(postContext.name,
                                prevContext.start_line,
                                prevContext.end_line,
                                postContext.start_line,
                                postContext.end_line)
                contexts.append(context)
    return contexts

def __getChangedMethodsPrev__():
    
    namesOfChangedMethods = []
    for changedMethod in modified_file.changed_methods:
        namesOfChangedMethods.append(changedMethod.name)

    changedMethods = []
    for method in modified_file.methods_before:
        if method.name in namesOfChangedMethods:
            changedMethods.append(method)
    
    return changedMethods

def __prepareLine__(line, prevFrame):
    
    line = line.strip()

    # normalize strings
    regex = re.compile(r'''"([^"\\\n]|\\(['"?\\abfnrtv]|[0-7]{1,3}|x[0-9a-fA-F]+))*"''')
    line = regex.sub('"string"', line)

    # ignore comment (//), javadoc (/* and *), import, and package lines
    regex = re.compile('^//|^/\*|^\*|^import|^package')
    if re.match(regex, line):
        return prevFrame

    # remove inline comments
    regex = re.compile('//.*$')
    line = regex.sub('', line)

    # remove inline javadoc comments
    regex = re.compile('/\*.*$')
    line = regex.sub('', line)

    # replace string escape character '"' with 'stringEscapceChar' (otherwise tokenizer in 6-trainModel.py explodes)
    regex = re.compile(r'''\'(")\'''')
    line = regex.sub('\'stringEscapeChar\'', line)

    prevFrame.append(line)
    return prevFrame

def __prepareFrame__(source, startLine, endLine, frames):

    prevFrame = []
    
    for idx, line in enumerate(source, start = 1):

        if startLine <= idx and idx <= endLine:

            if any(frame[0] <= idx and idx <= frame[1] for frame in frames):

                prevFrame = __prepareLine__(line, prevFrame)

    return prevFrame

def __prepareMethod__(source, startLine, endLine):

    prevFrame = []
    
    for idx, line in enumerate(source, start = 1):

        if startLine <= idx and idx <= endLine:

            prevFrame = __prepareLine__(line, prevFrame)

    return prevFrame
            
################################################################

for url in urls:

    #repo = Repository(url, single='180403fc32cd7f525374e82cc6786d15cc7642cc')
    repo = Repository(url)
    repoName = repo._get_repo_name_from_url(url)

    try:
        print("begin repo " + repoName)
        with open("repos/repo-" + repoName + '.csv', 'w', newline='') as file:

            writer = csv.writer(file, delimiter=';')
            headers = ["file", "commit", "msg", "prevFrame", "postFrame", "training?"]
            writer.writerow(headers)

            with alive_bar():
                for commit in repo.traverse_commits():

                    # Verify that commit triggers keywords
                    if all(not re.search(rf'\b{re.escape(word)}\b', commit.msg, re.IGNORECASE) for word in securityKeywordsFullsearch) and all(word not in commit.msg.lower() for word in securityKeywords):
                        continue

                    if all(word not in commit.msg.lower() for word in fixingKeywords):
                        continue
                    

                    # Verify that at least one Java file is in this commit
                    containsJava = 0
                    for modified_file in commit.modified_files:
                        if (".java" in modified_file.filename):
                            containsJava = 1
                            break
                    if containsJava == 0:
                        continue

                    for modified_file in commit.modified_files:

                        # disregard non-Java files
                        if (".java" not in modified_file.filename):
                            continue

                        prevContexts = __getChangedMethodsPrev__()
                        postContexts = modified_file.changed_methods

                        contexts = __getCombinedContexts__(prevContexts, postContexts)

                        for context in contexts:

                            # Prepare Frames
                            if modified_file.source_code_before is not None:

                                prevDiffBlocks = __getDiffBlocks__(modified_file.diff_parsed, "deleted")

                                prevSource = modified_file.source_code_before.splitlines()
                                if contextType == "method":
                                    prev = __prepareMethod__(prevSource, context.startLinePrev, context.endLinePrev)
                                else:
                                    prev = __prepareFrame__(prevSource, context.startLinePrev, context.endLinePrev, prevDiffBlocks)

                            if modified_file.source_code is not None:

                                postDiffBlocks = __getDiffBlocks__(modified_file.diff_parsed, "added")

                                postSource = modified_file.source_code.splitlines()

                                if contextType == "method":
                                    post = __prepareMethod__(postSource, context.startLinePost, context.endLinePost)
                                else:
                                    post = __prepareFrame__(postSource, context.startLinePost, context.endLinePost, postDiffBlocks)

                            isTrain = random.random() < trainingPercentage

                            try :
                                writer.writerow([modified_file.filename, commit.hash, commit.msg, ' '.join(prev), ' '.join(post), isTrain])
                            except UnicodeEncodeError:
                                print("Error writing to csv for method " + context.name)

        print("finished repo " + repoName)
    except PermissionError:
        print("Error writing to csv: file still open.")
    except GitCommandError:
        print("Something went wrong with git. skipping this")
        continue