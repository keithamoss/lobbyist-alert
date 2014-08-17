import ConfigParser
import requests
from datetime import datetime, date
from pprintpp import pprint as pp
from db import Session, User, AppSettings
import sqlalchemy.orm.exc
import time
import mandrill

# Config
Config = ConfigParser.ConfigParser()
Config.read("config.ini")
MORPHIO_API_KEY = Config.get("MORPH.IO", "API_KEY")
MANDRILL_API_KEY = Config.get("MANDRILL", "API_KEY")

db = Session()

def get_updated_lobbyists(last_run_date):
  """Get a list of updated lobbyists from all of the
  available registers based on their last updated date.

  Parameters
  ----------
  last_run_date : datetime
    The date of the last time lobbyist-alert ran.
  """
  response = requests.get(
    "https://api.morph.io/keithamoss/lobbyists-registers/data.json",
    params={"key": MORPHIO_API_KEY, "query": "select * from 'data'"},
    verify=False)

  lobbyists = []
  for l in response.json():
    if datetime.strptime(l["last_update"], "%d/%m/%Y") >= last_run_date:
     lobbyists.append(l)
  return lobbyists

def send_email(lobbyists, emails):
  """Sends an email with lobbyist updates to all
  subscribed users.

  Parameters
  ----------
  lobbyists : list
    A list of lobbyist objects that have changed since the last
      time the app ran.
  emails : list
    A list of emails to send to.
  """

  # Group lobbyists by location for prettier emails
  lobbyists_grouped = {}
  for l in lobbyists:
    if l["location"] not in lobbyists_grouped:
      lobbyists_grouped[l["location"]] = []
    lobbyists_grouped[l["location"]].append(l)

  register_name = {
    "wa": "Western Australia",
    "sa": "South Australia",
    "nsw": "New South Wales",
    "tas": "Tasmania",
    "qld": "Queensland",
    "vic": "Victoria",
    "fed": "Federal"
  }

  lobbyist_html = ""
  for k, v in lobbyists_grouped.iteritems():
    lobbyist_html += "<h3>{0}</h3>".format(register_name[k])
    for l in v:
      lobbyist_html += """
      <h4>{0}</h4>
      <p style="margin-top: 0px !important;">
        Updated: {1} - <a href="{2}">Details</a>
      </p>
      """.format(l["business_name"], l["last_update"], l["url"])
    lobbyist_html += "<br>"

  try:
    mandrill_client = mandrill.Mandrill(MANDRILL_API_KEY)
    message = {
     'auto_text': True,
     'from_email': 'message.from_email@example.com',
     'from_name': 'Lobbyist Alerts',
     'headers': {'Reply-To': 'message.reply@example.com'},
     'inline_css': True,
     'merge': True,
     'global_merge_vars': [{"name": "CONTENT", "content": lobbyist_html}],
     'metadata': {'website': 'lobbyist-alert'},
     'subject': 'Lobbyist Alert!',
     'to': [{"email": v} for v in emails],
     'track_clicks': True,
     'track_opens': True
    }
    result = mandrill_client.messages.send_template(
      template_name='lobbyist-alert',
      template_content=[],
      message=message
    )
  except mandrill.Error, e:
      # Mandrill errors are thrown as exceptions
      print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
      raise

# Get last run date, or default to today if it's not yet set.
try:
  last_run_record = db.query(AppSettings).filter(AppSettings.key == "last_run_date").one()
except sqlalchemy.orm.exc.NoResultFound:
  last_run_record = AppSettings(key="last_run_date", val=date.today().strftime("%d/%m/%Y"))
  db.add(last_run_record)
  db.commit()
last_run_date = datetime.strptime(last_run_record.val, "%d/%m/%Y")

# Get any changed lobbyists
lobbyists = get_updated_lobbyists(last_run_date)
if len(lobbyists) > 0:
  send_email(lobbyists, ["keithamoss@gmail.com", "helen.ensikat@gmail.com"])

# Finally, update the last run date
last_run_record.val = date.today().strftime("%d/%m/%Y")
db.commit()
