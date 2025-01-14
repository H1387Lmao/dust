import os
def main(*args, **kwargs):
	location = kwargs['location']
	if len(args)!=1:
		print('\033[31mInvalid amount of arguments.\033[0m')
		return
	filter_type = args[0].lower()
	prev_output = kwargs['prev_output']
	if prev_output[0] == None:
		print('\033[31mPrevious Output is none.\033[0m')
		return
	locations=[]
	glob_filter = False
	if filter_type == 'folder':
		sorter = os.path.isdir
	elif filter_type == "file":
		sorter = os.path.isfile
	else:
		glob_filter = True
	if not glob_filter:
		for item in prev_output[0]:
			item_loc = location.join(location, item)
			if sorter(item):
				locations.append(item)
		print(f'FOLDER CONTENT WITH FILTER: `{filter_type}`')
		for loc in locations:
			print(f'\t{loc}')
		return locations
	else:
		locations = location.glob(location, filter_type)
		if not kwargs['quiet']:
			print(f'FOLDER CONTENT WITH FILTER: {filter_type}')
			for loc in locations:
				print(f'\t{loc.file_name}')
		return locations