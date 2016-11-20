import requests
from bs4 import BeautifulSoup as BS

from tqdm import tqdm
import os
import datetime
import time
import logging
import random

try:
  strtypes = (str, unicode)
except:
  strtypes = str

def BeautifulSoup(t):
    return BS(t, 'html.parser')

class TimeWatchException(Exception):
  pass

class TimeWatch:
  def __init__(self, loglevel=logging.WARNING, **kwargs):
    self.site = "http://checkin.timewatch.co.il/"
    self.editpath = "punch/editwh3.php"
    self.loginpath = "punch/punch2.php"
    self.dayspath = "punch/editwh.php"

    self.offdays = ['friday', 'saturday']
    self.override = 'incomplete'
    self.jitter = 0
    self.starttime = '10:00'
    self.duration = '9:00'
    self.retries = 5
    self.config = ['offdays', 'override', 'jitter', 'starttime', 'duration', 'retries']

    logging.basicConfig()
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(loglevel)

    self.loggedin = False
    self.session = requests.Session()

    self.set_config(**kwargs)

  def set_config(self, **kws):
    for key, value in kws.items():
      if not key in self.config:
        self.logger.warn("Skipping parameter not listed in config: {}".format(key))

      if hasattr(self, "set_" + key):
        getattr(self, "set_" + key)(value)
      else:
        setattr(self, key, value)

      self.logger.debug("Set {} = '{}'".format(key, value))

  def post(self, path, data):
    return self.session.post(os.path.join(self.site, path), data)

  def get(self, path, data):
    return self.session.get(os.path.join(self.site, path), params=data)

  def login(self, company, user, password):
    """Company - company number is filled by user when logging in
    user - id/employee number as filled by user when logging in
    password - password as filled by user when logging in
    employeeid - id as internally represented by website after successful login"""
    data = {'comp': company, 'name': user, 'pw': password}
    r = self.post(self.loginpath, data)
    if "The login details you entered are incorrect!" in r.text:
      raise TimeWatchException("Login failed!")

    self.loggedin = True
    self.company = company
    self.user = user
    self.password = password
    self.employeeid = int(BeautifulSoup(r.text).find('input', id='ixemplee').get('value'))

    self.logger.info("successfully logged in as {} with id {}".format(self.user, self.employeeid))

    return r

  def time_to_tuple(self, t):
    if isinstance(t, strtypes):
      t = self.clean_text(t)
      if ':' in t:
        t = list(map(int, t.split(':')))
      else:
        t = ('', '')

    if isinstance(t, list):
      t = tuple(t)

    if not isinstance(t, tuple) or not len(t) == 2:
      raise Exception("couldn't convert time to tuple: {}".format(t))

    return t

  def tuple_to_str(self, t):
    return ':'.join(map(str, t))

  def edit_date(self, year, month, date, start=None, end=None, duration=None, jitter=None):
    if start is None:
      start = self.starttime
    start = self.time_to_tuple(start)

    if jitter is None:
      jitter = self.jitter
    jitter = random.randint(-self.jitter/2, self.jitter/2)
    start = start[0] + int(jitter / 60), start[1] + jitter % 60

    if duration is None:
      duration = self.duration

    if duration == ('', ''):
      start, end = ('', ''), ('', '')
    else:
      duration = self.time_to_tuple(duration)

    if not end:
      end = start[0] + duration[0], start[1] + duration[1]

    failures = 0
    while not (self.edit_date_post(date, start, end) and self.validate_date(year, month, date, start, end)):
      failures += 1
      if failures >= self.retries:
        self.logger.warn('Failed punching in {} times on {}'.format(failures, date))
        return False

    return True

  def edit_date_post(self, date, start, end):
    date_str = '{y}-{m}-{d}'.format(y=date.year, m=date.month, d=date.day)
    start_hour, start_minute = start
    end_hour, end_minute = end

    data = {'e': self.employeeid, 'tl': self.employeeid, 'c': self.company, 'd': date_str, 'next_date': ''}
    #data.update({'inclcontracts': 0, 'job': 0, 'allowabsence': 3, 'allowremarks': 1, 'teken': 0, 'remark': '', 'speccomp': '', 'atype': 0, 'excuse': 0, 'atypehidden': 0, 'jd': '2016-04-01', 'nextdate': ''})
    data.update({'task0': 0, 'taskdescr0': '', 'what0': 1, 'emm0': start_minute, 'ehh0': start_hour, 'xmm0': end_minute, 'xhh0': end_hour})
    #data.update({'task1': 0, 'taskdescr1': '', 'what1': 1, 'emm1': start_minute, 'ehh1': start_hour, 'xmm1': end_minute, 'xhh1': end_hour})
    #data.update({'task2': 0, 'taskdescr2': '', 'what2': 1, 'emm2': start_minute, 'ehh2': start_hour, 'xmm2': end_minute, 'xhh2': end_hour})
    #data.update({'task3': 0, 'taskdescr3': '', 'what3': 1, 'emm3': start_minute, 'ehh3': start_hour, 'xmm3': end_minute, 'xhh3': end_hour})
    #data.update({'task4': 0, 'taskdescr4': '', 'what4': 1, 'emm4': start_minute, 'ehh4': start_hour, 'xmm4': end_minute, 'xhh4': end_hour})
    #data.update({'fhhh': '', 'fhmm': '', 'thhh': '', 'thmm': ''})
    r=self.post(self.editpath, data)
    if "TimeWatch - Reject" in r.text:
      self.logger.info('Failure punching in on {} as {} to {}'.format(date_str, self.tuple_to_str(start), self.tuple_to_str(end)))
      return False

    self.logger.info('Punched in on {} as {} to {}'.format(date_str, self.tuple_to_str(start), self.tuple_to_str(end)))
    return True

  def clean_text(self, text):
    return text.strip().replace("&nbsp;", "")

  def parse_dates(self, year, month, keep_cause):
    data = {'ee': self.employeeid, 'e': self.company, 'y': year, 'm': month}
    r = self.get(self.dayspath, data)

    dates = set()
    for tr in BeautifulSoup(r.text).findAll('tr', attrs={'class': 'tr'}):
      tds = tr.findAll('td')
      date = datetime.datetime.strptime(tds[0].getText().split(" ")[0], "%d-%m-%Y").date()
      cause = True if self.clean_text(tds[8].getText()) else False
      if keep_cause is False or cause is False:
        dates.add(date)

    return dates

  def parse_expected_durations(self, year, month):
    data = {'ee': self.employeeid, 'e': self.company, 'y': year, 'm': month}
    r = self.get(self.dayspath, data)
    durations  = BeautifulSoup(r.text).findAll('tr', attrs={'class': 'tr'})
    date_durations = {}

    for tr in durations:
      tds = tr.findAll('td')
      date = datetime.datetime.strptime(tds[0].getText().split(" ")[0], "%d-%m-%Y").date()
      duration = self.time_to_tuple(tds[10].getText())
      date_durations[date] = duration
      self.logger.debug('parsed expected durarion for {} as {}'.format(date, duration))

    return date_durations

  def validate_date(self, year, month, expected_date, expected_start, expected_end):
    data = {'ee': self.employeeid, 'e': self.company, 'y': year, 'm': month}
    r = self.get(self.dayspath, data)

    for tr in BeautifulSoup(r.text).findAll('tr', attrs={'class': 'tr'}):
      tds = tr.findAll('td')
      date = datetime.datetime.strptime(tds[0].getText().split(" ")[0], "%d-%m-%Y").date()
      if date != expected_date:
        continue
      start = self.time_to_tuple(tds[2].getText())
      end = self.time_to_tuple(tds[3].getText())

      if start != expected_start or end != expected_end:
        self.logger.info('Validation failed, expected: {} - {}. read: {} - {}'.format(expected_start, expected_end, start, end))
        return False

      self.logger.debug('Successful validation for {} as {}-{}'.format(expected_date, start, end))
      return True

    self.logger.info('Validation failed reading punch time for {}'.format(expected_date))
    return False

  def month_number(self, month):
    if isinstance(month, int):
      return month

    if isinstance(month, strtypes) and month.isdigit():
      return int(month)

    for fmt in ['%b', '%B']:
      return time.strptime(month, fmt).tm_mon

    raise ValueError("Invalid month input: {}".format(month))

  def edit_month(self, year, month):
    month = self.month_number(month)

    if self.override == 'all':
      # in override=all mode, make sure all times are cleaned
      self.override_all = True
      self.keep_cause = False
      self.default_duration = None
    elif self.override == 'incomplete':
      # in override=incomplete mode, only override incomplete data
      # so simply clear dates without expected time
      self.override_all = False
      self.keep_cause = False
      self.default_duration = 0
    elif self.override == 'regular':
      self.override_all = True
      self.keep_cause = True
      self.default_duration = None

    self.logger.info('parsing dates to operate on')
    dates = sorted(self.parse_dates(year, month, self.keep_cause))

    if self.override_all:
      self.logger.info('overwriting all entries to retrieve expected durations')
      for date in tqdm(dates):
        self.edit_date(year, month, date, end=('', ''))

    self.logger.info('parsing expected durations')
    date_durations = self.parse_expected_durations(year, month)

    self.logger.info('punching in')

    for date in tqdm(dates):
      duration = date_durations.get(date, self.default_duration)
      self.edit_date(year, month, date, duration=duration)
