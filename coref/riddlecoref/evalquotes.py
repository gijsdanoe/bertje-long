"""Quote attribution evaluation.

Usage: evalquotes.py <gold.xml> <outputprefix>

where `gold.xml` is a file produced by https://github.com/muzny/quoteannotator/
and `outputprefix` is a prefix as used by dutchcoref.

For example, to reproduce the results in section 5.3
of https://clinjournal.org/clinj/article/view/91
$ cd quotes
$ tar -xzf Voskuil_Buurman.tar.gz
$ cd ../../dutchcoref
$ python3 coref.py --outputprefix /tmp/Voskuil_Buurman --slice 0:2031 quotes/Voskuil_Buurman
$ cd ../riddlecoref
$ python3 evalquotes.py quotes/Voskuil_Buurman.xml /tmp/Voskuil_Buurman

"""
import sys
from lxml import etree
import pandas


def main():
	try:
		goldfile, outputprefix = sys.argv[1:]
	except Exception:
		print(__doc__)
		return
	gold = etree.parse(goldfile)
	cand = pandas.read_csv(
			outputprefix + '.quotes.tsv', sep='\t', index_col=0, quoting=3)
	mentions = pandas.read_csv(
			outputprefix + '.mentions.tsv', sep='\t', index_col=0, quoting=3)
	speakers = {}
	loweredmentions = mentions.text.str.lower()
	for char in gold.findall('.//character'):
		name = char.get('name')
		if (loweredmentions == name.lower().replace('_', ' ')).any():
			c = mentions[loweredmentions == name.lower().replace('_', ' ')
					].iloc[0, :]['cluster']
			speakers[str(c)] = name
			print(c, name)
		else:
			print('not mapped:', name)
	print('effective mapping:')
	for c, name in speakers.items():
		print(c, name)

	goldquotes = gold.findall('.//quote')
	correct = 0
	nospeaker = 0
	n = 0
	for quote, (_, row) in zip(
			goldquotes,
			cand.iterrows()):
		assert quote.text.replace('\n', '').strip() == row.text.strip(), (
				quote.text, row.text)
		correct += quote.get('speaker') == speakers.get(
				str(row.speakercluster))
		nospeaker += speakers.get(str(row.speakercluster)) is None
		print(quote.get('speaker'), speakers.get(row.speakercluster), row.text,
				sep='\t')
		n += 1
		if False and n == 55:
			print('recall %d / %d = %g %%' % (correct, 55, 100 * correct / 55))
			print('precision %d / %d = %g %%' % (correct, (55 - nospeaker),
					100 * correct / (55 - nospeaker)))
			print('no speaker:', nospeaker)
			return
	print('precision: %d / %d = %g %%' % (correct, len(goldquotes) - nospeaker,
			100 * correct / (len(goldquotes) - nospeaker)))
	print('recall: %d / %d = %g %%' % (correct, len(goldquotes),
			100 * correct / len(goldquotes)))
	print('no speaker:', nospeaker)


if __name__ == '__main__':
	main()
