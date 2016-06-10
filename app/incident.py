import datetime
import rethinkdb as r
import app.channels as channels
from templates.responses import NEW_CHANNEL_MESSAGE

class Incident:
    def __init__(self):
        self.start_date = None
        self.resolved_date = None
        self.status = None
        self.name = None
        self.app = None
        self.severity = None
        self.slack_channel = None
        self.description = None
        self.tasks = []
        self.config = None

    @staticmethod
    def create_new_incident(app_name, config):
        incident = Incident()
        incident.start_date = datetime.datetime.now(r.make_timezone('-07:00'))
        incident.resolved_date = None
        incident.status = 'Identified'  # should be an enum-type thing
        incident.name = "{today_format}-{app_name}"\
            .format(today_format=incident.start_date.strftime("%Y-%m-%d"),
                    app_name=app_name)
        incident.app = app_name
        incident.severity = None  # should be another enum-like thing
        incident.slack_channel = None
        incident.description = None
        incident.tasks = []
        incident.leader = None
        incident.config = config
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff
        return incident

    @staticmethod
    def get_incident_by_channel(db_conn, slack_channel):
        result = r.table('incidents')\
            .filter({'slack_channel': slack_channel})\
            .run(db_conn).next()
        incident = Incident()
        incident.start_date = result['start_date']
        incident.resolved_date = result['resolved_date']
        incident.status = result['status']
        incident.name = result['name']
        incident.app = result['app']
        incident.severity = result['severity']
        incident.slack_channel = result['slack_channel']
        incident.description = result['description']
        incident.tasks = result['tasks']
        return incident

    def add_task(self, task):
        self.tasks.append(task)
        # todo: needs some database saving stuff

    def create_channel(self):
        """Ensures that a channel is created for the incident"""
        # todo: create channel in slack - hopefully it doesn't already exist
        try:
            resp = channels.create(self.name, self.config)
            self.slack_channel = resp['channel']['id']
            self.name = resp['channel']['name']
            channels.join(self.slack_channel, self.config)
            channels.post(self.slack_channel, self.config, NEW_CHANNEL_MESSAGE.render())
        except ValueError as err:
            print(err)

    def summarize(self):
        """Returns a summary of the incident"""

    @staticmethod
    def get_incident(db_conn, id):
        return r.table('incidents').get(id).run(db_conn)

    def save(self, db_conn):
        r.table('incidents')\
            .insert({'name': self.name,
                     'status': self.status,
                     'app': self.app,
                     'severity': self.severity,
                     'slack_channel': self.slack_channel,
                     'description': self.description,
                     'tasks': self.tasks,
                     'start_date': r.expr(self.start_date),
                     'resolved_date': self.resolved_date},
                    conflict="update")\
            .run(db_conn)
