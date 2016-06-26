# harbour-app-info-bot
A simple web scraper bot for reading app download/active/likes/comment information from harbour.jolla.com.
Notifies about new likes or comments through IRC.

## Requirements
pip install -r requirements.txt

### Additional requirements
apt-get install xvfb python-mysqldb libmysqlclient-dev

## Usage
- Install the requirements
- Create a secrets.py file including your username and password
- Sun python run.py to see if it works
- Set a cron script to run it as often as you desire to (eg. */30 * * * * /path-to-destination/run.py)