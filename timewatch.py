import requests
import os
import datetime
import BeautifulSoup

class TimeWatchException(Exception):
  pass

class TimeWatch:
  def __init__(self):
    self.site = "http://checkin.timewatch.co.il/"
    self.editpath = "punch/editwh3.php"
    self.loginpath = "punch/punch2.php"

    # negative shift means start of `abs(shift)`-th day of previous month, until `abs(shift)-1`-th day of currnt month
    # for example, shift -25 for March will yield Feb 25th until Mar 24th.
    # positive shift means start of `shift`-th day of current month, until `shift-1`-th day of next month
    self.shift = -25
    self.offdays = [4, 5]
    
    self.loggedin = False
    self.session = requests.Session()

  def post(self, path, data):
    return self.session.post(os.path.join(self.site, path), data)

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

  def edit_day(self, date):
    date_str = '{y}-{m}-{d}'.format(y=date.year, m=date.month, d=date.day)
    start_hour, start_minute, end_hour, end_minute = 10, 0, 19, 0
    data = {'e': self.employeeid, 'tl': self.employeeid, 'c': self.company, 'd': date_str}
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
    return r

  def workday(self, date):
    if date.weekday() in self.offdays:
      return False
    # TODO: handle holidays
    return True

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
      yield date

  def edit_month(self, year, month):
    for date in self.monthdays(year, month, self.shift):
      if not self.workday(date):
        continue

      self.edit_day(date)
