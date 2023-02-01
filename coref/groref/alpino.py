# This assumes that Alpino is installed
# On LWP this can be done by 
# export ALPINO_HOME=/net/aps/64/src/Alpino
# PATH=/net/aps/64/bin:$PATH

import os
import sys
import shutil

def esc_squares(word):
	word = word.replace('[','\[')
	return word.replace(']','\]')

def parse(conllFile, tokenIdx, nameCut):
    tmpFile = open('tmp', 'w')
    for line in open(conllFile, 'r'):
        if line.startswith('doc_id'):
            pass
        else:
            if len(line.split('\t')) > 1:
                tmpFile.write(esc_squares(line.split('\t')[tokenIdx] + ' '))
            else:
                tmpFile.write('\n\n')
    tmpFile.close()
    
    folder = conllFile[:conllFile.find('_')]
    if os.path.exists(folder):
        shutil.rmtree(folder)
    print(folder)
    os.mkdir(folder)
    
    os.system('cat tmp | Alpino number_analyses=1 end_hook=xml -flag treebank ' + folder + ' -parse')

def runAlpino(working, tokenIdx, nameCut):
    tmpPath = 'tmp'
    for conllFile in os.listdir(working):
        if conllFile.endswith('ne'):
            parse(working+conllFile, tokenIdx, nameCut)

if __name__ == '__main__':
    #runAlpino('DCOI/conll/', 6, 30)
    #runAlpino('clinDevData/', 2, 21)
    runAlpino('clinTestData/boeing/corefne/', 2, 21)
    #runAlpino('clinTestData/gm/corefne/', 2, 21)
    #runAlpino('clinTestData/stock/corefne/', 2, 21)

