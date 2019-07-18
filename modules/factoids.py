def cmd_get_ac():
	with open('data/ac.txt', 'r') as f:
		return f.read()

def cmd_get_mentors():
	with open('data/mentors.txt', 'r') as f:
		return f.read()