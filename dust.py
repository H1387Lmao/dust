import os
import sys
import glob
import signal
import time
import importlib
import inspect
import traceback
RECENT_PROMPT=""

class Location:
	def __init__(self, loc=__file__):# If loc is the default (__file__), normalize it to the directory of the file
		if loc == __file__:
			loc = os.path.dirname(loc)
		if os.name!="nt":
			if loc[0]=="/":
				loc="root__++dir"+loc
		self.loc = self.normalize(loc)
		self._parent = self.normalize(os.path.dirname(self.loc))
		if os.path.isfile(loc):
			self.file_name = os.path.basename(loc)
	@property
	def parent(self):
		return Location(self._parent)
	
	@staticmethod
	def join(loc1, loc2):
		# If loc1 or loc2 is a Location instance, extract its loc attribute
		if isinstance(loc1, Location):
			loc1 = loc1.loc
		if isinstance(loc2, Location):
			loc2 = loc2.loc

		# If loc2 is absolute, return it directly
		if loc2.startswith(("/", "\\")) or ":" in loc2:
			return Location.normalize(loc2)

		# Otherwise, join loc1 and loc2
		joined = loc1.rstrip("/\\") + "/" + loc2.lstrip("/\\")
		return Location.normalize(joined)

	@staticmethod
	def normalize(path):
		# Normalize the path manually
		parts = []
		for part in path.replace("\\", "/").split("/"):
			if part == "..":
				if parts:  # Pop the last part if possible
					parts.pop()
			elif part and part != ".":  # Ignore empty parts and "."
				parts.append(part)
		# Reconstruct the path
		new = "/".join(parts)
		return new.replace("root__++dir", "")

	@staticmethod
	def glob(location, pattern):
		# If location is a Location instance, use its loc attribute
		if isinstance(location, Location):
			location = location.loc

		# Use glob to find matching paths based on the pattern (supports wildcards)
		matches = glob.glob(Location.join(location, pattern))
		# Return a list of Location objects for matched paths
		return [Location(loc) for loc in matches]

	def __repr__(self):
		return self.loc

class CommandCancelled(Exception):
	pass

# Global signal handler to prevent shell exit
def global_signal_handler(sig, frame):
	if os.name=="nt":
		sys.stdout.write(Format("&1^C&7\n"))
	sys.stdout.flush()

# Register the global signal handler
signal.signal(signal.SIGINT, global_signal_handler)
ctrl_codes = [chr(a) for a in range(1, 26)]
def cancelable(func):
	def wrapper(*args, **kwargs):
		def signal_handler(sig, frame):
			print("Command cancelled.")
			raise CommandCancelled
		signal.signal(signal.SIGINT, signal_handler)
		try:
			return func(*args, **kwargs)
		except CommandCancelled:
			return None
		finally:
			# Restore the global signal handler after function execution
			signal.signal(signal.SIGINT, global_signal_handler)
	return wrapper

# Input function with custom handling for Ctrl+C
def Input(prompt='', max_length=None, default=None, case_sensitive=True, show_echo=False):
	global RECENT_PROMPT
	if not case_sensitive:
		prompt = prompt.lower()
	prompt = Format(prompt)
	RECENT_PROMPT = prompt
	sys.stdout.write(prompt)
	sys.stdout.flush()
	user_input = ""
	
	while True:
		try:
			char = sys.stdin.read(1)
		except KeyboardInterrupt:
			if os.name=="nt":
				sys.stdout.flush()
				user_input = ""
				return ""
		if char == '':
			sys.stdout.flush()
			user_input = ""
			return ""
		if char == '\n':
			break
		if max_length and len(user_input) >= max_length:
			break
		if char in ctrl_codes: continue
		if char == '\x7f':  # Backspace
			user_input = user_input[:-1]
			if show_echo:
				sys.stdout.write('\b \b')
		else:
			user_input += char
			if show_echo:
				sys.stdout.write(char)
	sys.stdout.write("\033[0m")
	if not user_input and default is not None:
		return default
	return user_input

# Feature folder and command imports
feature_folder = "feature_folder"

command_files = [
	f[:-3] for f in os.listdir(feature_folder)
	if f.endswith(".py") and not f.startswith('__')
]
commands = {}
for command_file in command_files:
	module_path = f"{feature_folder}.{command_file}"
	try:
		module = importlib.import_module(module_path)
		if hasattr(module, "main") and inspect.isfunction(module.main):
			commands[command_file.removeprefix('.py')] = cancelable(module.main)
	except Exception as e:
		print(f"Error while importing {command_file.removeprefix('.py')}: {e}")

formats = {f'{key:X}': (30 + key if key <= 7 else 82 + key) for key in range(16)}

def Format(string):
	a = ""
	in_code = False
	for char in string:
		if char == "&":
			in_code = True
			continue
		if in_code:
			in_code = False
			a += "\033[" + str(formats[char.upper()]) + "m"
		else:
			a += char
	return a

welcome = Format("&8Welcome to &4DISAPPOINTING USER SHELL TERMINAL &8(&1D.U.S.T&8)!")

print(welcome)

# Shell loop
location = Location()
breaked=False
while not breaked:
	try:
		user_input = Input("&2Hello world> &7", show_echo=False)
		if user_input.strip() == '':
			continue

		cmd_pipes = user_input.split('|')
		prev_output = (None, None)
		is_last_pipe = 0
		for command in cmd_pipes:
			is_last_pipe+=1
			user_input = command.strip()
			coms = user_input.split(" ")
			cmd_name = coms[0]
			cmd_args = coms[1:]

			if cmd_name == "quit":
				breaked=True
				break

			if cmd_name in commands.keys():
				cmd = commands[cmd_name]
				try: prev_output = cmd(*cmd_args, prev_output=prev_output, location=location, quiet=not is_last_pipe==len(cmd_pipes)), cmd_name
				except Exception as e: print(Format(f'&1Got this error whilst trying to run `{cmd_name}`:\n\n{traceback.format_exc()}&7')) 
			else:
				print(Format(f"&1Unknown command: {cmd_name}&7"))
	except KeyboardInterrupt:
		if os.name=="nt":
			sys.stdout.write(Format("&1^C&7\n"))
		sys.stdout.flush()
