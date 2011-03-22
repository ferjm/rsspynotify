#! /usr/bin/env python

import feedparser, pynotify
from xml.sax.saxutils import escape

pynotify.init("RSSPyNotify")

feeds = []

class Feed:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.seen = set()
        self.etag = None
        self.modified = None

    def parse(self, feed):
        if feed.has_key("etag"):
            self.etag = feed.etag
        if feed.has_key("modified"):
            self.modified = feed.modified

        previous = self.seen.copy()
        items = []

        for entry in feed.entries:
            if entry.id in previous:
                previous.remove(entry.id)
            else:
                self.seen.add(entry.id)
                if len(items) < 5:
                    items.append("&#8226; <a href='%s'>%s</a>" % (entry.link, escape(entry.title)))

        if items:
            n = pynotify.Notification(self.title, "\n".join(items), "stock_news")
            # 5 seconds per item
            n.set_timeout(len(items) * 5 * 1000)
            n.set_category("email.arrived")
            n.set_urgency(pynotify.URGENCY_LOW)
            n.show()

        self.seen = self.seen - previous

    def run(self):
        feed = feedparser.parse(self.url, etag=self.etag, modified=self.modified)
        # Local feeds don't have a status
        if not feed.has_key("status"):
            self.parse(feed)
        # If there is a status field, handle it
        elif feed.status >= 200 and feed.status < 400:
            # Success and Redirection
            if feed.status == 304:
                # Not Modified, no-op
                pass
            elif feed.status == 301:
                # Moved Permanently
                self.url = feed.url
                self.parse(feed)
            else:
                # Everything else
                self.parse(feed)
        elif feed.status == 410:
            # Gone
            feeds.remove(feed)


if __name__ == "__main__":
    import sys, time

    if sys.argv[1:]:
        for url in sys.argv[1:]:
            feeds.append(Feed("Test", url))
    else:
        feeds.append(Feed("CNN", "http://rss.cnn.com/rss/cnn_world.rss"))

    while True:
        [feed.run() for feed in feeds]
        time.sleep(5 * 60)
