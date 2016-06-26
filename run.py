#!/usr/bin/env python
# -*- coding: koi8-r -*-
from __future__ import print_function
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import re
import os
from bs4 import BeautifulSoup
import MySQLdb
import MySQLdb.cursors
import sys
import logging
from secrets import USERNAME, PASSWORD, APP_NAMES, IRC_BOT_NICK, IRC_REAL_NICK
import socket

# Variables
username = USERNAME
password = PASSWORD
app_names = APP_NAMES
irc_bot_nick = IRC_BOT_NICK
irc_real_nick = IRC_REAL_NICK
base_url = "https://harbour.jolla.com/auth/jolla"
msg = ""


# For saving the stats to a local mysql database
# db = MySQLdb.connect(host="localhost",
#                      port=3306,
#                      user="root",
#                      passwd="",
#                      db="harbour",
#                      charset="utf8",
#                      use_unicode=True,
#                      cursorclass=MySQLdb.cursors.DictCursor)

# db.autocommit(True)
# cursor = db.cursor()
# cursor.execute('SET NAMES utf8;')
# cursor.execute('SET CHARACTER SET utf8;')
# cursor.execute('SET character_set_connection=utf8;')

# Notify yourself through IRC
def notify(msg):
    global irc_bot_nick
    global irc_real_nick

    server = "irc.freenode.net"
    botnick = irc_bot_nick
    realnick = irc_real_nick

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.settimeout(12)
    irc.connect((server, 6667))
    irc.send("USER " + botnick + " " + botnick + " " + botnick + " :This is a fun bot!\n")
    irc.send("NICK " + botnick + "\n")
    irc.send("PRIVMSG nickserv :iNOOPE\r\n")
    irc.send('PRIVMSG '+realnick+' :' + msg + ' \r\n')

    for i in range(15):
        text = irc.recv(2040)

        if text.find('PING') != -1:
            # returns 'PONG' back to the server (prevents pinging out!)
            irc.send('PONG ' + text.split()[1] + '\r\n')
        time.sleep(1)


def get_soup():
    global username
    global password
    global app_name
    global base_url

    profile = webdriver.FirefoxProfile()
    driver = webdriver.Firefox(profile)
    driver.implicitly_wait(80)
    verificationErrors = []
    accept_next_alert = True
    driver = driver
    driver.get(base_url)

    # Sign in button present?
    for i in range(45):
        try:
            if is_element_present(By.CLASS, "form-horizontal"):
                break
        except:
                pass
        time.sleep(1)

    driver.find_element_by_id("id_username").clear()
    driver.find_element_by_id("id_username").send_keys(username)
    driver.find_element_by_id("id_password").clear()
    driver.find_element_by_id("id_password").send_keys(password)
    driver.find_element_by_css_selector("button.btn").click()

    # Applist present?
    for i in range(30):
        try:
            if is_element_present(By.ID, "app-list"):
                break
        except:
            pass
        time.sleep(1)

    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")
    return soup


def get_app_qa_status(soup, app_name):
    try:
        firstt = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong").text
        secondt = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong").find_next("strong").text
        thirdt = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong").find_next("strong").find_next("strong").text
        first = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong")
        second = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong").find_next("strong")
        third = soup.find('h3', text=re.compile(app_name)).find_next("span").find_next("span").find_next("strong").find_next("strong").find_next("strong")

        d = "display: none"
        if d not in str(first):
            return firstt
        if d not in str(second):
            return secondt
        if d not in str(third):
            return thirdt
        else:
            return "Not found"
    except Exception as e:
        logging.error(e)
        return None


def get_app_numbers(soup, app_name):
    try:
        downloads = soup.find('h3', text=re.compile(app_name)).find_next("td").text
        active = soup.find('h3', text=re.compile(app_name)).find_next("td").find_next("td").text
        likes = soup.find('h3', text=re.compile(app_name)).find_next("td").find_next("td").find_next("td").text
        reviews = soup.find('h3', text=re.compile(app_name)).find_next("td").find_next("td").find_next("td").find_next("td").text
        return [downloads, active, likes, reviews]
    except Exception as e:
        logging.error(e)
        return None


def is_element_present(how, what):
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def compare(app, now, previous):
    global msg
    changed = False

    nowlist = now.split(",")
    prevlist = previous.split(",")

    # Notify if status has changed
    if nowlist[0] != prevlist[0]:
        changed = True
        msg += "Status: " + nowlist[0] + " for " + app + " | "

    # Notify for comments
    if int(nowlist[5]) != int(prevlist[5]):
        changed = True
        msg += "New COMMENT! for " + app + " | "

    if int(nowlist[2]) != int(prevlist[2]):
        changed = True
        msg += "D|"

    if int(nowlist[3]) != int(prevlist[3]):
        changed = True
        msg += "A|"

    if int(nowlist[4]) != int(prevlist[4]):
        changed = True
        msg += "L|"

    if changed:
        msg += " " + app + " " + ','.join(nowlist[2:]) + " | "
        
        # Mysql stuff
        # cursor.execute("""INSERT INTO harbour.appname (status, downloads, actives, likes, comments) VALUES (%s, %s, %s, %s, %s)""", (nowlist[0], int(nowlist[2]), int(nowlist[3]), int(nowlist[4]), int(nowlist[5])))
        # if not cursor.rowcount:
        #     logging.warn("[WARNING] Insert failed for " + app)
        #     notify("[WARNING] Insert failed" + app + " " + now)


# def init_db_if_needed():
    # cursor.execute("""CREATE TABLE IF NOT EXISTS `appname` (
    #                   `id` int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    #                   `status` varchar(32) NOT NULL,
    #                   `downloads` int NOT NULL,
    #                   `actives` int NOT NULL,
    #                   `likes` int NOT NULL,
    #                   `comments` int NOT NULL,
    #                   `inserted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
    #                 ) ENGINE='InnoDB' COLLATE 'utf8_swedish_ci';""")


def main(args):
    try:
        logging.basicConfig(filename='./bot.log',level=logging.INFO,format='%(asctime)s %(message)s')
        logging.info("Starting: " + ' & '.join(app_names))

        # For testing, set visible=1
        display = Display(visible=0, size=(800, 600))
        display.start()
        soup = get_soup()

        for app in app_names:
            status = get_app_qa_status(soup, app)
            numbers = get_app_numbers(soup, app)
            # logging.info(app + " " + status + " " + ' '.join(numbers))

            appinfo = status + ',' + ','.join(numbers)
            filename = app.replace(" ", "")
            # filename = app.replace(" ", "")

            # init_db_if_needed()

            try:
                if os.path.exists(filename):
                    with open(filename, 'r+') as f:
                        previous = f.readline()
                        # logging.info(appinfo)
                        # logging.info(previous)
                        with open(filename, "w+") as f:
                            print(appinfo, file=f)

                        compare(app, appinfo, previous)
                else:
                    with open(filename, "w+") as f:
                        print(appinfo, file=f)

            except Exception as e:
                logging.error(e)
        display.stop()

        if msg != "":
            # logging.info(msg)
            notify(msg)

        # Cleanup to free some space on device
        # os.system("rm -r /tmp/*")

    except Exception as e:
        logging.error(e)
        return 1  # exit on error
    else:
        return 0  # exit errorlessly

if __name__ == '__main__':
    sys.exit(main(sys.argv))
