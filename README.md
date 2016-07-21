## timewatch

Tired of reporting work hours every day/month?
Your boss trusts you with your time, but HR demands you fill timewatch's form?
You're too preoccupied with work, and forget filling up timewatch.co.il?

We've all been there, just set up a monthly timewatch cron and get back to work!

### What is this?
This script automatically sets default working hours for all work days using timewatch.co.il's web interface.
It reads expected work hours for each day and automatically sets each day's work to that amount.
It is therefor handling govt. off days and weekends, and is quite configurable.

## Usage
To report required working hours for the current month, simply execute
```./main <company id> <employee number> <password>```

### Full usage and functionality

```
usage: main.py [-h] [-y YEAR] [-m MONTH] [-v] [-o {all,incomplete,regular}]
               [-s STARTTIME] [-j JITTER]
               company user password

Automatic work hours reporting for timewatch.co.il

positional arguments:
  company               Company ID
  user                  user name/id
  password              user password

optional arguments:
  -h, --help            show this help message and exit
  -y YEAR, --year YEAR  Year number to fill
  -m MONTH, --month MONTH
                        Month number or name
  -v, --verbose         increase logging level
  -o {all,incomplete,regular}, --override {all,incomplete,regular}
                        Control override behavior. all - override all working
                        days, unsafe to vacation/sick days. incomplete = only
                        override days with partial records. regular - override
                        regular days (without absence reason) only
  -s STARTTIME, --starttime STARTTIME
                        punch-in time
  -j JITTER, --jitter JITTER
                        punching time random range in minutes.
```

### Installation

```
git clone https://github.com/nirizr/timewatch.git
cd timewatch
pip install -r requirements.txt
```

or

```
pip install timewatch
```

### Known issues
* Doesn't sign the doc (I suggest you do it manually after reviewing there are no bugs in the report).
* no support for reporting vacation/sick days through the script yet (You can report using timewatch's web interface before/after running the script)
