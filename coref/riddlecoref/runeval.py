r"""Run coreference and evaluate.

Prints a table of results and stores results in
results/novel<subset>/<time>/..
to keep track of experimental results.

Usage: python3 runeval.py <dev|test|gbdev|gbtest> [OPTIONS] model context
Options: --goldmentions --goldclusters --neural=<span,feat,pron>
Example: python3 runeval.py test --neural=span,feat,pron bertje-long 2048

Models available:
- bertje-long
- robbert-long
- bertje
- robbert
- pino
- xlm-l

Context:
- sent (per sentence)
- 128
- 512
- 1024
- 2048

To get quote attribution accuracy for the dev set used in CLINjournal (2019):

~/ $ python3 runeval.py olddev --oldquotes

(see also `evalquotes.py` which evaluates a longer fragment,
as reported in the paper).

Requirements:
Expects dutchcoref repositories in the parent directories:

~/riddlecoref $ cd ..
~/ $ git clone https://github.com/andreasvc/dutchcoref.git
~/ $ pip3 install git+https://github.com/andreasvc/coval
~/ $ cd riddlecoref
~/ $ python3 runeval.py dev
                              mentions                  lea
                              recall    prec    f1      recall  prec    f1      CoNLL
Gilbert_EtenBiddenBeminnen    80.56&    89.82&  84.94&  60.99&  70.96&  65.60&  72.48\\
Kluun_Haantjes                86.36&    88.37&  87.36&  59.25&  65.69&  62.30&  71.89\\
Kooten_Verrekijker            85.73&    85.98&  85.85&  51.60&  57.65&  54.45&  66.40\\
Mitchell_NietVerhoordeGebeden 90.39&    86.16&  88.22&  47.72&  55.93&  51.50&  65.98\\
Springer_Quadriga             86.07&    83.91&  84.98&  42.35&  55.72&  48.12&  61.90\\

Overall                       86.85&    85.87&  86.36&  49.09&  58.04&  53.20&  65.91\\
"""
import os
import sys
import getopt
from glob import glob
from datetime import datetime
from lxml import etree
import pandas
from coval.conll import reader
from coval.eval import evaluator
sys.path.append('../dutchcoref')
import coref
from nltk import accuracy

# The new dev set as used in the CRAC 2020 paper
DEVSET = """\
Gilbert_EtenBiddenBeminnen
Kluun_Haantjes
Kooten_Verrekijker
Mitchell_NietVerhoordeGebeden
Springer_Quadriga""".splitlines()

# The new test set as used in the CRAC 2020 paper
TESTSET = """\
Forsyth_Cobra
Japin_Vaslav
Proper_GooischeVrouwen
Royen_Mannentester
Verhulst_LaatsteLiefdeVan""".splitlines()

# Gutenberg subset
GBDEV = ['Multatuli_MaxHavelaar']
GBTEST = ['Couperus_ElineVere']

# This dev set was used for the CLIN 2019 paper
OLDDEVSET = """\
Barnes_AlsofVoorbijIs
Carre_OnsSoortVerrader
Eco_BegraafplaatsVanPraag
Eggers_WatIsWat
Grunberg_HuidEnHaar
James_VijftigTintenGrijs
Koch_Diner
Moor_SchilderEnMeisje
Voskuil_Buurman
Yalom_RaadselSpinoza""".splitlines()

# This test set was used for the CLIN 2019 paper
# 8000+ words;
OLDTESTSET = """\
Abdolah_Koning
Bernlef_ZijnDood
Binet_Hhhh
Dewulf_KleineDagen
Forsyth_Cobra
Japin_Vaslav
Kooten_Verrekijker
Mitchell_NietVerhoordeGebeden
Siebelink_Oscar
Springer_Quadriga
Verhulst_LaatsteLiefdeVan""".splitlines()

# 3 chapters
EXTRA1 = """Collins_Hongerspelen
Rowling_HarryPotterEn""".splitlines()

# 2000+ sentences
EXTRA2 = """\
Bezaz_Vinexvrouwen
Gilbert_EtenBiddenBeminnen
Kinsella_ShopaholicBaby
Kluun_Haantjes
Mansell_VersierMeDan
Proper_GooischeVrouwen
Royen_Mannentester
Vermeer_Cruise
Weisberger_ChanelChic
Worthy_JamesWorthy""".splitlines()


def evaluate(keyfile, sysfile):
	"""Return a tuple of scores (m_r, m_p, m_f1, l_r, l_p, l_f1, conll)

	where m are mention scores, and l are LEA sccores; in both cases consisting
	of recall, precision and F1."""
	nponly = removenested = False
	keepsingletons = True
	doccoref = reader.get_coref_infos(
			keyfile, sysfile, nponly, removenested, keepsingletons)
	conll = 0
	for metric in (evaluator.muc, evaluator.b_cubed, evaluator.ceafe):
		_recall, _precision, f1 = evaluator.evaluate_documents(
				doccoref, metric, beta=1)
		conll += f1
	conll /= 3
	mentions = evaluator.evaluate_documents(
			doccoref, evaluator.mentions, beta=1)
	lea = evaluator.evaluate_documents(
			doccoref, evaluator.lea, beta=1)
	return tuple(a * 100 for a in mentions + lea + (conll, ))


def evalquotes(keyfile, outputprefix):
	"""Evaluate quote attribution.

	:param keyfile: a tsv file with columns token, speaker, addressee, quote.
		quote has the text of the quotation, token is the start token of the
		quote, speaker and addressee are the head tokens of the
		speaker/addressee mentions of the quote.
	:param outputprefix: the prefix of the output files
		(see --outputprefix option of coref.py).
	"""
	gold = pandas.read_csv(keyfile, sep='\t', index_col=0, quoting=3)
	# contains the mention and cluster ID to which the quote is attributed.
	sysquotes = pandas.read_csv('%s.quotes.tsv' % outputprefix,
			sep='\t', index_col=0, quoting=3)
	# contains the indices of mentions
	sysmentions = pandas.read_csv('%s.mentions.tsv' % outputprefix,
			sep='\t', index_col=0, quoting=3)

	def getcluster(tokenidx):
		"""Map token idx to system cluster ID.

		Returns the longest span when there are multiple matches."""
		cand = [row for _, row in sysmentions[
					(sysmentions.start <= tokenidx)
						& (tokenidx <= sysmentions.end)].iterrows()]
		if not cand:
			return -1
		row = max(cand, key=lambda x: x.end - x.start)
		return row.cluster

	def getclusters(goldcol, syscol):
		# gold has token index of mention
		# sys output has mention ID, map to mention span,
		# map gold token index to mention,
		# check if it is coreferent with sys output
		goldclusters = [str(getcluster(int(gold.at[row.start, goldcol])))
					if gold.at[row.start, goldcol] != '-'
					else gold.at[row.start, goldcol]
					for _, row in sysquotes.iterrows()]
		sysclusters = [str(a) for a in sysquotes[syscol]]
		# for a, b, (_, row) in zip(
		# 		goldclusters, sysclusters, sysquotes.iterrows()):
		# 	print(
		# 			int(a == b),
		# 			sysmentions.at[int(row['speakermention']), 'text']
		# 				if row['speakermention'] != '-' else '-',
		# 			row.text)
		return goldclusters, sysclusters

	return getclusters('speaker', 'speakercluster')
	# 		+ getclusters('addressee', 'addresseecluster')


def evalpronouns(keyfile, outputprefix, parsesdir, debug=False):
	"""Return pronoun accuracy."""
	def revidx(start, end):
		sentno, begin = idx[start - 1]
		sentno_, end_ = idx[end - 1]
		if sentno != sentno_:
			raise ValueError('expected matching sentence numbers')
		return sentno, begin, end_ + 1

	# load gold data: coreference clusters, trees, mentions
	# assume single doc per conll file
	conlldata = next(iter(coref.readconll(keyfile).values()))
	goldspansforcluster = coref.conllclusterdict(conlldata)
	docname = os.path.basename(os.path.splitext(keyfile)[0])
	pattern = os.path.join(parsesdir, docname, '*.xml')
	filenames = sorted(glob(pattern), key=coref.parsesentid)
	if not filenames:
		raise ValueError('parse trees not found: %s' % pattern)
	trees = [(coref.parsesentid(filename), etree.parse(filename))
			for filename in filenames]
	ngdata, gadata = coref.readngdata()
	mentions = coref.extractmentionsfromconll(
			conlldata, trees, ngdata, gadata, goldclusters=True)
	# load system output
	# sysconlldata = next(iter(coref.readconll(
	# 		outputprefix + '.conll').values()))
	# sysspansforcluster = coref.conllclusterdict(sysconlldata)
	# sysclusterforspan = {span: cluster
	# 		for cluster, spans in sysspansforcluster.items()
	# 			for span in spans}

	# map global token index to sentno, tokno
	idx = {}
	n = 0
	for sentno, sent in enumerate(conlldata):
		for tokno, _token in enumerate(sent):
			idx[n] = (sentno, tokno)
			n += 1
	# contains the indices of system mentions
	sysmentions = pandas.read_csv('%s.mentions.tsv' % outputprefix,
			sep='\t', index_col=0, quoting=3, engine='python')
	# contains the ids for all pairs of mentions that have been linked
	syslinks = pandas.read_csv('%s.links.tsv' % outputprefix,
			sep='\t', quoting=3)
	# construct dict mapping system pronoun spans to antecedent spans
	syslinkdict = {}
	for _, row in syslinks.iterrows():
		if row['sieve'].startswith('resolvepronouns'
				) or row['sieve'].startswith('gold'):
			if row['mention1'] == -1 or row['mention2'] == -1:
				# no link (i.e., pronoun has no antecedent / postcedent)
				continue
			# look up spans of mention1 / mention2
			columns = ['start', 'end', 'text']
			start1, end1, text1 = sysmentions.loc[row['mention1'], columns]
			start2, end2, text2 = sysmentions.loc[row['mention2'], columns]
			# convert global token idx to sentno, tokidx
			sentno1, begin1, end1_ = revidx(start1, end1)
			sentno2, begin2, end2_ = revidx(start2, end2)
			syslinkdict[(sentno2, begin2, end2_, text2)] = (
					sentno1, begin1, end1_, text1)
	if debug:
		for a, b in syslinkdict.items():
			print(a, '\t', b)
	num = denom = 0
	for mention in mentions:
		if (mention.type == 'pronoun'
				# no relative/reciprocal/reflexive pronouns
				and mention.node.get('vwtype') not in (
					'betr', 'recip', 'refl')
				and mention.features['person'] not in ('1', '2')):
			# NB: this score does not reach 100% if system produced
			# no antecedent (even if that is correct)
			# TODO: change metric?
			# - could limit denominator to pronouns with a link of interest
			#   (reciprocal/reflective pronouns shouldn't count)
			# - could count pronouns without antecedent (strictly preceding) as
			#   correct if predicted as such (but how to handle cataphora?)
			# maybe https://aclanthology.org/J01-4006.pdf
			denom += 1
			pronspan = (mention.sentno, mention.begin, mention.end,
					' '.join(mention.tokens))
			# check whether antecedent linked by system
			# is part of gold cluster.
			sysantecedentspan = syslinkdict.get(pronspan)
			if sysantecedentspan in goldspansforcluster[mention.clusterid]:
				# 	or (sysantecedentspan is None
				# 		and (mention.sentno, mention.begin, mention.end)
				# 		== min(goldspansforcluster[mention.clusterid])[:3])):
				num += 1
			elif debug:
				print(mention)
				print(pronspan)
				print(sysantecedentspan)
				print(goldspansforcluster[mention.clusterid])
				print()
			# also count as correct if the pronoun did not get a link,
			# and it is a singleton in the gold cluster.
			# elif (sysantecedentspan is None
			# 		and len(goldspansforcluster[mention.clusterid]) == 1):
			# 	num += 1
	return num, denom


def main():
	"""CLI."""
	longopts = ['goldmentions', 'goldclusters', 'debug', 'oldquotes',
			'neural=','context=','model=']
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], '', longopts)
	except getopt.GetoptError:
		print(__doc__)
		return
	if len(args) != 3:
		print('expected exactly 1 argument; try --help')
		return
	opts = dict(opts)
	subset = args[0]
	context = args[-1]
	name = args[-2]
	if '--goldclusters' in opts and '--goldmentions' not in opts:
		raise NotImplementedError('--goldclusters requires --goldmentions')
	if '--oldquotes' in opts and subset != 'olddev':
		raise ValueError('--oldquotes requires "olddev" subset')
	if subset == 'dev':
		filenames = DEVSET
	elif subset == 'test':
		filenames = TESTSET
	elif subset == 'gbdev':
		filenames = GBDEV
	elif subset == 'gbtest':
		filenames = GBTEST
	elif subset == 'olddev':
		filenames = OLDDEVSET
	else:
		raise ValueError('expected subset as first argument, '
				'one of: dev, test, gbdev, gbtest')
	neural = [a for a in opts.get('--neural', '').split(',') if a]
	riddlecorefcommit = coref.getcommit()
	os.chdir('../dutchcoref')
	ngdata, gadata = coref.readngdata()
	dutchcorefcommit = coref.getcommit()
	path = '../riddlecoref/results/novel%s/%s' % (
			subset, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
	os.makedirs(path, exist_ok=False)
	width = 30
	with open('%s/scores.tsv' % path, 'w', encoding='utf8') as scorefile:
		def printlog(line):
			"""Print both to a file and to stdout."""
			print(line)
			print(line, file=scorefile)

		printlog('riddlecoref=%s dutchcoref=%s %s' % (
				riddlecorefcommit, dutchcorefcommit, ' '.join(sys.argv)))
		printlog(coref.getcmdlines(neural))
		printlog('%smentions\t\t\tlea\t\t\t\tpron' % ''.ljust(width)
				+ ('\tspeaker' if '--oldquotes' in opts else ''))
		printlog('%srecall\tprec\tf1\trecall\tprec\tf1\tCoNLL\tacc'
				% ''.ljust(width)
				+ ('\tacc' if '--oldquotes' in opts else ''))
		goldspeakers, sysspeakers = [], []
		totpronnum = totpronden = 0
		for novel in filenames:
			outputprefix = '%s/%s' % (path, novel)
			conlldata = None
			if '--goldmentions' in opts:
				conlldata = coref.getmatchingdoc(
						coref.readconll('../riddlecoref/coref/%s.conll'
							% novel), novel)
			with open(
					'%s/%s.conll' % (path, novel), 'w',
					encoding='utf8') as out:
				coref.process('../riddlecoref/parses/%s/*.xml' % novel, out,
						ngdata, gadata,context,name, docname=novel, conlldata=conlldata,
						fmt='conll2012', goldmentions='--goldmentions' in opts,
						goldclusters='--goldclusters' in opts,
						neural=neural, outputprefix=outputprefix)
			scores = evaluate('../riddlecoref/coref/%s.conll' % novel,
						'%s/%s.conll' % (path, novel))
			pronnum, pronden = evalpronouns(
					'../riddlecoref/coref/%s.conll' % novel,
					outputprefix,
					'../riddlecoref/parses',
					debug='--debug' in opts)
			totpronnum += pronnum
			totpronden += pronden
			scores += (100 * pronnum / pronden, )
			# NB: speaker annotations are only available for OLDDEVSET
			if '--oldquotes' in opts and os.path.exists(
					'../riddlecoref/quotes/%s.tsv' % novel):
				goldspeakers1, sysspeakers1 = evalquotes(
						'../riddlecoref/quotes/%s.tsv' % novel, outputprefix)
				goldspeakers.extend(goldspeakers1)
				sysspeakers.extend(sysspeakers1)
				scores += (accuracy(goldspeakers1, sysspeakers1) * 100, )
			printlog(novel.ljust(width)
					+ '&\t'.join('%.2f' % a for a in scores) + '\\\\')
		keyfile = '%s/gold.conll' % path
		sysfile = '%s/output.conll' % path
		with open(keyfile, 'w', encoding='utf8'
				) as keyout, open(sysfile, 'w', encoding='utf8') as sysout:
			for novel in filenames:
				with open(
						'../riddlecoref/coref/%s.conll' % novel,
						encoding='utf8') as inp:
					keyout.write(inp.read())
				with open(
						'%s/%s.conll' % (path, novel), encoding='utf8') as inp:
					sysout.write(inp.read())
		printlog('\n%s%s' % (
				'Overall'.ljust(width),
				'&\t'.join('%.2f' % a for a in evaluate(keyfile, sysfile)
					+ (100 * totpronnum / totpronden, )
					+ ((100 * accuracy(goldspeakers, sysspeakers), )
						if '--oldquotes' in opts else ())
					)) + '\\\\')


if __name__ == '__main__':
	main()
