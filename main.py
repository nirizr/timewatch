#!/usr/bin/python

import timewatch
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Fill timewatch form')
  
  parser.add_argument('company', type=int, help='Company ID')
  parser.add_argument('user', help='user name/id')
  parser.add_argument('password', help='user password')

  parser.add_argument('year', type=int, help='Year number to fill')
  parser.add_argument('month', type=int, help='Month number to fill (1=Jan, 12=Dec)')

  args = parser.parse_args()

  tw=timewatch.TimeWatch()
  tw.login(args.company, args.user, args.password)
  tw.edit_month(args.year, args.month)
