import os
def main(*args, **kwargs):
	quiet = kwargs['quiet']
	items = os.listdir(kwargs['location'].loc)
	if not quiet:
		print('FOLDER CONTENT:\n\t', '\n\t'.join(items), sep='')
	return items