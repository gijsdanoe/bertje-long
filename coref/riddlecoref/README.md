# riddlecoref

Copyrighted material, do not distribute.

## Contents:

- coref: exported files in [CoNLL 2012 format](http://conll.cemantix.org/2012/data.html).
  The coreference column is manually corrected. The POS, parse bit, and NER
  columns are extracted from the automatically derived parse trees.
- parses: parse trees produced by [Alpino](http://www.let.rug.nl/vannoord/alp/Alpino/),
  one XML file per sentence. Not manually corrected.
- xmi: source files with manually corrected coreference, produced by
  [CorefAnnotator](https://github.com/nilsreiter/CorefAnnotator/).
  Does not contain POS, parse bit, and NER information.
- features: tab-separated files with entity features: gender and number.
  Each entity is identified by the indices (sentence number, begin/end token)
  of its first mention.
  Gender has values:
  - f (female)
  - m (male)
  - fm (unknown or mixed gender)
  - n (neuter, non-human)

  Any gender except n implies a human entity.

  Number:
  - sg (singular)
  - pl (plural; an entity consisting of multiple individuals/objects)

  The semantic number is annotated (e.g., "the group" is plural since it could be
  referred to by "they"), regardless of the syntactic number.
- split: contains subdirectories with train/dev/test split with symlinks to conll files.
- runeval.py: evaluate using https://github.com/andreasvc/dutchcoref/
  
  Prints a table of results and stores results in
  `results/novel<subset>/<time>/...`
  to keep track of experimental results.

  Usage: `python3 runeval.py <dev|test|gbdev|gbtest> [OPTIONS]`
  Options: `--goldmentions --neural=<span,feat,pron>`

  Requirements:
  Expects dutchcoref repositories in the parent directories:
  
  ```bash
  ~/riddlecoref $ cd ..
  ~/ $ git clone https://github.com/andreasvc/dutchcoref.git
  ~/ $ git clone https://github.com/andreasvc/coval.git
  ~/ $ cd riddlecoref
  ~/ $ python3 runeval.py dev
  ```
- quotes: quote attribution annotations in two formats:
  1. `*.xml` files annotated with https://github.com/muzny/quoteannotator/
    See `evalquotes.py` for an evaluation tool.
  2. `*.tsv` tab-separated files where speaker and addressee is indicated
    with a token index of the head of the mention.
    See `runeval.py` for an evaluation tool.
    TODO: better evaluation metric (precision, recall) and file format.
