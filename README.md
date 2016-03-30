# timewatch

This script automatically sets default working hours for all work days using timewatch.co.il's web interface.
It reads the expected work hours for each day and automatically sets each day's work to that amount.
It is therefor handling govt. off days and weekends.

Usage is trivial:
./main <company id> <employee number> <password> <report year> <report month>

Known issues:
* Doesn't sign the doc (I suggest you do it manually after reviewing there are no bugs in the report).
* it'll overwrite any manually/automatically reported events, including vacation/sick days you reported prior to running the script for the specific month
