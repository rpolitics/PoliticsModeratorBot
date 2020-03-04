from peewee import *
import json
import html
from prettytable import PrettyTable, from_db_cursor

with open('config.json', 'r') as f:
	config = json.load(f)['database']

mysql_db = MySQLDatabase(config['database'], user=config['user'], password=config['password'], host=config['host'], port=config['port'], charset=config['charset'])

mysql_db.connect()

class BaseModel(Model):
	class Meta:
		database = mysql_db

class BotLog(BaseModel):
	class Meta:
		table_name = 'botlog'

	id = CharField(max_length=10, null=False)
	module = CharField(max_length=15, null=False)
	created_utc = DateTimeField(null=False)
	action = CharField(max_length=50, null=False)
	details = CharField(max_length=300, null=False)
	author = CharField(max_length=20, null=False)
	body = CharField(max_length=10000, null=False)

class Comment(BaseModel):
	class Meta:
		table_name = 'comments'

	id = CharField(max_length=7, primary_key=True)
	submission_id = CharField(max_length=6, null=False)
	created_utc = DateTimeField(null=False)
	author = CharField(max_length=20, null=False)
	body = CharField(max_length=10000, null=False)
	author_created_utc = DateTimeField(null=False)
	author_flair_text = CharField(max_length=64, null=True)
	author_link_karma = IntegerField(null=False)
	author_comment_karma = IntegerField(null=False)
	is_removed = BooleanField(default=False, null=False)

class ModAction(BaseModel):
	class Meta:
		table_name = 'modlog'

	id = CharField(max_length=50, primary_key=True)
	created_utc = DateTimeField(null=False)
	moderator = CharField(max_length=20, null=False)
	action = CharField(max_length=50, null=False)
	details = CharField(max_length=300, null=True)
	target_fullname = CharField(max_length=10, null=True)
	target_author = CharField(max_length=20, null=True)
	target_title = CharField(max_length=300, null=True)

class Perspective(BaseModel):
	class Meta:
		table_name = 'perspective'

	id = CharField(max_length=10, primary_key=True)
	created_utc = DateTimeField(null=False)
	author = CharField(max_length=20, null=False)
	scores = TextField(null=False)
	body = CharField(max_length=10000, null=False)

class Removal(BaseModel):
	class Meta:
		table_name = 'removals'

	submission_id = CharField(max_length=6, null=False)
	comment_id = CharField(max_length=7, null=False)
	created_utc = DateTimeField(null=False)
	moderator = CharField(max_length=20, null=False)
	flair = CharField(max_length=64, null=True)
	is_active = BooleanField(null=False)

class Report(BaseModel):
	class Meta:
		table_name = 'reports'
		primary_key = CompositeKey('submission_id', 'author', 'reason')

	id = CharField(max_length=10)
	author = CharField(max_length=20)
	reason = CharField(max_length=100)
	count = IntegerField(null=True)
	is_ignored = BooleanField(null=False)

class Submission(BaseModel):
	class Meta:
		table_name = 'submissions'

	id = CharField(max_length=6, primary_key=True)
	created_utc = DateTimeField(null=False)
	author = CharField(max_length=20, null=False)
	title = CharField(max_length=300, null=False)
	url = CharField(max_length=256, null=False)
	flair = CharField(max_length=64, null=True)
	author_created_utc = DateTimeField(null=False)
	author_flair_text = CharField(max_length=64, null=True)
	author_link_karma = IntegerField(null=False)
	author_comment_karma = IntegerField(null=False)
	is_removed = BooleanField(default=False, null=False)

def print_query_results(sql):
	sql = sql.replace('“', '"').replace('”', '"').replace('‘', '\'').replace('’', '\'')
	sql = html.unescape(sql)
	if not sql.upper().startswith("SELECT"):
		return "Only SELECT queries are allowed."

	try:
		cursor = mysql_db.execute_sql(sql)
	except Exception as e:
		return str(e)

	table = from_db_cursor(cursor)
	table.align = 'l'
	if len(table.get_string()) > 4000:
		return  "Max message length exceeded. Please query via phpMyAdmin."
	
	return "```" + table.get_string() + "```"
