"""
Horner Bible Reading Plan
"""

from datetime import datetime, timedelta
from argparse import ArgumentParser
from collections.abc import Sequence
from collections import UserList
import json
import os

from meaningless import WebExtractor
import arrow
import yaml


BIBLE_YAML = """
---
readings_start: 0
readings_end: 364
list_1:
  - Matthew, 28
  - Mark, 16
  - Luke, 24
  - John, 21
list_2:
  - Genesis, 50
  - Exodus, 40
  - Leviticus, 27
  - Numbers, 36
  - Deuteronomy, 34
list_3:
  - Romans, 16
  - 1 Corinthians, 16
  - 2 Corinthians, 13
  - Galatians, 6
  - Ephesians, 6
  - Philippians, 4
  - Colossians, 4
  - Hebrews, 13
list_4:
  - 1 Thessalonians, 5
  - 2 Thessalonians, 3
  - 1 Timothy, 6
  - 2 Timothy, 4
  - Titus, 3
  - Philemon, 1
  - James, 5
  - 1 Peter, 5
  - 2 Peter, 3
  - 1 John, 5
  - 2 John, 1
  - 3 John, 1
  - Jude, 1
  - Revelation, 22
list_5:
  - Job, 42
  - Ecclesiastes, 12
  - Song of Solomon, 8
list_6:
  - Psalms, 150
list_7:
  - Proverbs, 31
list_8:
  - Joshua, 24
  - Judges, 21
  - Ruth, 4
  - 1 Samuel, 31
  - 2 Samuel, 24
  - 1 Kings, 22
  - 2 Kings, 25
  - 1 Chronicles, 29
  - 2 Chronicles, 36
  - Ezra, 10
  - Nehemiah, 13
  - Esther, 10
list_9:
  - Isaiah, 66
  - Jeremiah, 52
  - Lamentations, 5
  - Ezekiel, 48
  - Daniel, 12
  - Hosea, 14
  - Joel, 3
  - Amos, 9
  - Obadiah, 1
  - Jonah, 4
  - Micah, 7
  - Nahum, 3
  - Habakkuk, 3
  - Zephaniah, 3
  - Haggai, 2
  - Zechariah, 14
  - Malachi, 4
list_10:
  - Acts, 28
"""

class BibleChapterList(UserList):
    """A List to hold a list of BibleChapter() instances"""

    def __init__(self, data=None):
        if data is None:
            data = []
        elif not isinstance(data, Sequence):
            raise ValueError("BibleChapterList() must get a sequence / list of BibleChapter() instances as the argument")
        super().__init__(data)

        self.data = data

    def __str__(self):
        return f"<BibleChapterList {self.data}>"

    def __repr__(self):
        return self.__str__()

class BibleChapter:
    """A class to represent a Bible Chapter"""
    def __init__(self, book="", chapter=-1):
        if book == "":
            raise ValueError("BibleChapter() book must be specified")
        if chapter==-1:
            raise ValueError("BibleChapter() chapter must be specified")
        self.book = book
        self.chapter = int(str(chapter).strip())

    def __str__(self):
        return f"<{self.book} {self.chapter}>"

    def __repr__(self):
        return self.__str__()

    def get_url(self, translation="NASB1995"):
        """Download and return the BibleChapter from BibleGateway.com"""

        bible = WebExtractor(translation=translation)
        passage = bible.get_chapter(self.book, self.chapter)
        return f"""\n{self.book} {self.chapter}\n{passage}\n"""

class JsonBookmark:
    """A bible bookmark datestamp that updates no more than every 24 hours"""

    def __init__(self, args):
        self.filepath = os.path.expanduser("~/.horner_bible_readings.json")
        self.args = args

        if not os.path.exists(self.filepath):
            self.create_bookmark()

        with open(self.filepath) as fh:
            self.bookmark = json.load(fh)

        # Ensure we have updated the bookmark to the most recent timestamp
        self.update_bookmark()

    @property
    def day_index_number(self):
        return int(self.bookmark["day_index_number"])

    @property
    def translation(self):
        return self.bookmark["translation"]

    def create_bookmark(self):
        """Create a new json bookmark file in ~/.horner_bible_readings.json"""

        if self.args.translation == "":
            raise ValueError("Cannot save translation preferences without a translation.  Use -t from the CLI")

        bookmark = {"day_index_number": 0, "last_updated": str(arrow.now()), "translation": self.args.translation}

        with open(self.filepath, 'w') as fh:
            json.dump(bookmark, fh)

    def update_bookmark(self):
        """If it's past midnight since updating the bookmark, update the bookmark and roll the day index to zero after 365 readings"""

        # Strip hh:mm:ss from last_updated timestamp
        update_date = self.bookmark["last_updated"].split("T")[0]

        # If past midnight since the last reading, bump the day index number...
        now = arrow.now()
        days = (now - arrow.get(update_date)).days
        if (args.save_settings is True) or (days > 0):
            if (days > 0):
                if self.day_index_number < 365:
                    self.bookmark["day_index_number"] += 1
                else:
                    self.bookmark["day_index_number"] = 0

            # Update translation in the settings file if --save_settings is used
            if args.save_settings is True:
                self.bookmark["translation"] = self.args.translation

            self.bookmark["last_updated"] = str(now)

            with open(self.filepath, 'w') as fh:
                json.dump(self.bookmark, fh)

def parse_args():
    """Parse the command-line arguments"""

    parser = ArgumentParser(prog='horner_readings.py',
            description='Bible reading automation (Horner Bible reading plan)',)
    parser.add_argument("-d", "--daily",
                        action='store_true',
                        help="Daily readings, default")
    parser.add_argument("-y","--year",
                        action='store_true',
                        help="Yearly readings")
    parser.add_argument("-t", "--translation",
                        choices=("NASB1995", "NIV", "ASV", "ESV", "KJV", "NKJV"),
                        default="")
    parser.add_argument("-s", "--save_settings",
                        action='store_true',
                        help="Save settings to the preferences file")
    return parser.parse_args()


def get_chapter_readings_from_yaml(items):
    """
    Returns a list of all Bible chapter readings for a given list of books in the yaml config.
    """

    readings_list = BibleChapterList()

    # Loop through list:
    for item in items:

        # Split into book and total chapters:
        bible_book, total_chapters = item.split(", ")

        # Make chapters an integer:
        total_chapters = int(total_chapters)

        # Keep looping through available chapters from books in list:
        for chapter in range(1, total_chapters + 1):

            # Append book and chapter (as string) to list,
            # giving us the full list of readings for this list:
            readings_list.append(BibleChapter(book=bible_book, chapter=chapter))

    return readings_list


def get_book_lists_from_yaml_config():

    # Read the embedded global yaml string...
    config = yaml.safe_load(BIBLE_YAML)

    # Configuration variables:
    readings_start = config["readings_start"]
    readings_end = config["readings_end"]

    # Load each list of Bible books from the yaml config:
    list_1 = config["list_1"]
    list_2 = config["list_2"]
    list_3 = config["list_3"]
    list_4 = config["list_4"]
    list_5 = config["list_5"]
    list_6 = config["list_6"]
    list_7 = config["list_7"]
    list_8 = config["list_8"]
    list_9 = config["list_9"]
    list_10 = config["list_10"]
    return  (list_1, list_2, list_3, list_4, list_5, list_6, list_7, list_8, list_9, list_10)

def build_readings():

    lists = get_book_lists_from_yaml_config()

    # Create empty lists to populate with readings:
    readings_list_1 = get_chapter_readings_from_yaml(lists[0])
    readings_list_2 = get_chapter_readings_from_yaml(lists[1])
    readings_list_3 = get_chapter_readings_from_yaml(lists[2])
    readings_list_4 = get_chapter_readings_from_yaml(lists[3])
    readings_list_5 = get_chapter_readings_from_yaml(lists[4])
    readings_list_6 = get_chapter_readings_from_yaml(lists[5])
    readings_list_7 = get_chapter_readings_from_yaml(lists[6])
    readings_list_8 = get_chapter_readings_from_yaml(lists[7])
    readings_list_9 = get_chapter_readings_from_yaml(lists[8])
    readings_list_10 = get_chapter_readings_from_yaml(lists[9])

    # Combine each list:
    all_chapter_lists = (
        readings_list_1,
        readings_list_2,
        readings_list_3,
        readings_list_4,
        readings_list_5,
        readings_list_6,
        readings_list_7,
        readings_list_8,
        readings_list_9,
        readings_list_10,
    )
    return all_chapter_lists

def print_year_of_readings():
    """Print daily readings in order for the entire year"""
    all_chapter_lists = build_readings()
    # Loop through readings:
    for i in range(0, 365):

        # Count the day number we are on:
        day = i + 1

        # Print the readings:
        print(
            day,
            all_chapter_lists[0][i % len(all_chapter_lists[0])],
            all_chapter_lists[1][i % len(all_chapter_lists[1])],
            all_chapter_lists[2][i % len(all_chapter_lists[2])],
            all_chapter_lists[3][i % len(all_chapter_lists[3])],
            all_chapter_lists[4][i % len(all_chapter_lists[4])],
            all_chapter_lists[5][i % len(all_chapter_lists[5])],
            all_chapter_lists[6][i % len(all_chapter_lists[6])],
            all_chapter_lists[7][i % len(all_chapter_lists[7])],
            all_chapter_lists[8][i % len(all_chapter_lists[8])],
            all_chapter_lists[9][i % len(all_chapter_lists[9])],
            sep=", ",
        )

def print_todays_readings(args):
    all_chapter_lists = build_readings()

    bookmark = JsonBookmark(args=args)

    day_index_number = bookmark.day_index_number

    readings = (all_chapter_lists[0][day_index_number % len(all_chapter_lists[0])],
                all_chapter_lists[1][day_index_number % len(all_chapter_lists[1])],
                all_chapter_lists[2][day_index_number % len(all_chapter_lists[2])],
                all_chapter_lists[3][day_index_number % len(all_chapter_lists[3])],
                all_chapter_lists[4][day_index_number % len(all_chapter_lists[4])],
                all_chapter_lists[5][day_index_number % len(all_chapter_lists[5])],
                all_chapter_lists[6][day_index_number % len(all_chapter_lists[6])],
                all_chapter_lists[7][day_index_number % len(all_chapter_lists[7])],
                all_chapter_lists[8][day_index_number % len(all_chapter_lists[8])],
                all_chapter_lists[9][day_index_number % len(all_chapter_lists[9])],)

    if args.translation != "" and args.translation != bookmark.translation:
        translation = args.translation
    else:
        translation = bookmark.translation

    print("Translation:", translation)
    print("TODAY", readings)
    for bible_chapter in readings:
        print(bible_chapter.get_url(translation=translation))


if __name__=="__main__":
    args = parse_args()
    if args.year:
        print_year_of_readings()
    elif args.daily:
        print_todays_readings(args=args)
    else:
        # Default to today's readings
        print_todays_readings(args=args)
