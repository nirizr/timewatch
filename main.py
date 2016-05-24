#!/usr/bin/python

import timewatch
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Fill timewatch form')
  
  parser.add_argument('company', type=int, help='Company ID')
  parser.add_argument('user', help='user name/id')
  parser.add_argument('password', help='user password')

  parser.add_argument('year', type=int, help='Year number to fill')
  parser.add_argument('month', help='Month number or name')

  parser.add_argument('-o', '--override', default='incomplete', choices=['all', 'incomplete', 'regular'], help='Control override behavior. all - override all working days, unsafe to vacation/sick days. incomplete = only override days with partial records. regular - override regular days (without absence reason) only')

  args = parser.parse_args()

  tw=timewatch.TimeWatch()
  tw.login(args.company, args.user, args.password)
  tw.set_config(override = args.override)
  tw.edit_month(args.year, args.month)
