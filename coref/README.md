## Coreference resolution
For the full set-up, see: https://github.com/andreasvc/dutchcoref/. The RiddleCoref data is copyrighted

How to run:
1. First, for each model and context, all three classifiers need to be trained:
   ```
   cd dutchcoref
   python3 mentionspanclassifier.py <train> <validation> <parsesdir> <model> <context>
   python3 mentionfeatureclassifier.py <train> <validation> <parsesdir> <model> <context>
   python3 pronounresolution.py <train> <validation> <parsesdir> <model> <context>
   ```
   For example:
   ```
   python3 mentionspanclassifier.py '../riddlecoref/split/riddle/train' '../riddlecoref/split/riddle/dev' ../riddlecoref/parses/ bertje-long 2048
   ```
   
   Models available:
   - bertje-long
   - robbert-long
   - bertje
   - robbert
   - pino

   For the context, any number can be used, for this experiment the following are chosen:  
   - sent (sentence-only)
   - 128
   - 512
   - 1024
   - 2048

2. To evaluate, run:
   ```
   cd ..
   cd riddlecoref
   python3 runeval.py test --neural=span,feat,pron <model> <context>
   ```
