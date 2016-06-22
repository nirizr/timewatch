import requests
import os
import datetime
import time
import BeautifulSoup

class TimeWatchException(Exception):
  pass

class TimeWatch:
  def __init__(self):
    self.site = "http://checkin.timewatch.co.il/"
    self.editpath = "punch/editwh3.php"
    self.loginpath = "punch/punch2.php"
    self.dayspath = "punch/editwh.php"

    # negative shift means start of `abs(shift)`-th day of previous month, until `abs(shift)-1`-th day of currnt month
    # for example, shift -25 for March will yield Feb 25th until Mar 24th.
    # positive shift means start of `shift`-th day of current month, until `shift-1`-th day of next month
    self.shift = -25
    self.offdays = ['friday', 'saturday']
    self.override = 'incomplete'
    self.config = ['shift', 'offdays', 'override']

    self.loggedin = False
    self.session = requests.Session()

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
    self.employeeid = int(BeautifulSoup.BeautifulSoup(r.text).find('input', id='ixemplee').get('value'))

    return r

  def set_config(self, **kws):
    for key, value in kws.items():
      if not key in self.config:
        continue

      if hasattr(self, "set_" + key):
        getattr(self, "set_" + key)(value)
      else:
        setattr(self, key, value)

  def edit_date(self, date, start_hour=10, start_minute=0, end_hour=19, end_minute=0, time=None):
    date_str = '{y}-{m}-{d}'.format(y=date.year, m=date.month, d=date.day)

    if time is 0:
      start_hour, start_minute, end_hour, end_minute = '', '', '', ''
    elif time:
      time_hour, time_minute = time
      end_hour, end_minute = start_hour + time_hour, start_minute + time_minute

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
      raise TimeWatchException("edit failed!")
    self.validate_date(date, start_hour, start_minute, end_hour, end_minute)
    return r

  def clean_text(self, text):
    return text.strip().replace("&nbsp;", "")

  def parse_expected_times(self, year, month, dates=[]):
    data = {'ee': self.employeeid, 'e': self.company, 'y': year, 'm': month}
    r = self.get(self.dayspath, data)

    date_times = {}
    for tr in BeautifulSoup.BeautifulSoup(r.text).findAll('tr', attrs={'class': 'tr'}):
      tds = tr.findAll('td')
      date = datetime.datetime.strptime(tds[0].getText().split(" ")[0], "%d-%m-%Y").date()
      time = self.clean_text(tds[10].getText())
      date_times[date] = map(int, time.split(":")) if time and (not dates or date in dates) else 0
    return date_times

  def validate_date(self, expected_date, expected_start_hour, expected_start_minute, expected_end_hour, expected_end_minute):
    data = {'ee': self.employeeid, 'e': self.company, 'y': expected_date.year, 'm': expected_date.month}
    r = self.get(self.dayspath, data)

    date_times = {}
    for tr in BeautifulSoup.BeautifulSoup(r.text).findAll('tr', attrs={'class': 'tr'}):
      tds = tr.findAll('td')
      date = datetime.datetime.strptime(tds[0].getText().split(" ")[0], "%d-%m-%Y").date()
      if date != expected_date:
        continue
      start_time = [int(i) for i in self.clean_text(tds[2].getText()).split(":") if i]
      end_time = [int(i) for i in self.clean_text(tds[3].getText()).split(":") if i]

      expected_start_time = [int(i) for i in (expected_start_hour, expected_start_minute) if i != '']
      expected_end_time = [int(i) for i in (expected_end_hour, expected_end_minute) if i != '']
      if start_time != expected_start_time or end_time != expected_end_time:
        raise TimewatchError("validation failed", start_time, expected_start_time, end_time, expected_end_time)

  def workday(self, date):
    weekday_representation = [date.strftime(fmt).lower() for fmt in ('%a', '%A', '%w')]

    for offday in self.offdays:
      if str(offday).lower() in weekday_representation:
        return False

    return True

  def month_number(self, month):
    if month.isdigit():
      return int(month)

    for fmt in ['%b', '%B']:
      return time.strptime(month, fmt).tm_mon
    return month

  def monthdays(self, year, month, shift):
    if shift < 0:
      if month == 1:
        start_month = 12
        start_year = year - 1
      else:
        start_month = month - 1
        start_year = year
      start_day = -shift
    elif shift >= 0:
      start_day = 1 + shift
      start_month = month
      start_year = year

    start_date = datetime.date(start_year, start_month, start_day)

    if shift < 0:
      end_day = -shift
      end_month = month
      end_year = year
    elif shift >= 0:
      if month == 12:
        end_month = 1
        end_year = year + 1
      else:
        end_month = month + 1
        end_year = year
      end_day = 1 + shift

    end_date = datetime.date(end_year, end_month, end_day)

    for n in range(int ((end_date - start_date).days)):
      date = start_date + datetime.timedelta(n)
      if self.workday(date):
        yield date

  def edit_month_blind(self, year, month):
    for date in self.monthdays(year, month, self.shift):
      self.edit_date(date)

  def edit_month(self, year, month):
    # get days to work on
    month = self.month_number(month)
    dates = list(self.monthdays(year, month, self.shift))
    default_time = None

    if self.override == 'all':
      # in override=all mode, make sure all times are cleaned
      for date in dates:
        self.edit_date(date, end_hour='', end_minute='')
    elif self.override == 'incomplete':
      # in override=incomplete mode, only override incomplete data
      # so simply clear dates without expected time
      default_time = 0
    elif self.override == 'regular':
      raise NotImplemented("override='regular' is not implemented. expected: wont override days with a cause (vacation, sick day, etc)")

    date_times = self.parse_expected_times(year, month)

    for date in dates:
      time = date_times.get(date, default_time)
      self.edit_date(date, time=time)
