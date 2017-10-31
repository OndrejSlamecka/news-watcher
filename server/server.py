# There are two threads,
# one watching the news, storing them and pushing to the clients,
# the other one responding to requests for news made by new clients

import time
import pusher
import urllib.request
import yaml
import json
import threading
import http.server
from collections import namedtuple
from heapq import heappush, heappop
from bs4 import BeautifulSoup as Soup

# There should be some logging when exceptions occur,
# we leave it as it is for now


# We store article with this simple object
Article = namedtuple('Article', 'timestamp href text')


# The set of news to show
class News:
    def __init__(self):
        self.news = []  # a heap sorted by timestamp from oldest to youngest
        self.hrefs = set()  # for filtering duplicates

    def get_all(self):
        return self.news

    def add(self, href, text):
        if href not in self.hrefs:
            heappush(self.news, Article(timestamp=time.time(),
                                        href=href, text=text))
            self.hrefs.add(href)

    def remove_old(self, age_limit):
        while self.news and self.news[0][0] < time.time() - age_limit:
            self.hrefs.remove(self.news[0][1])
            heappop(self.news)


# The scraper. Returns links containing the phrase (specified above)
# from the url (specified above)
def get_links(url, phrase):
    # Scan the BBC homepage
    with urllib.request.urlopen(url) as response:
        html = response.read()

    # Populate the candidates list with all the anchor tags in the HTML
    # which contain the phrase
    parser = Soup(html, 'html.parser')

    candidates = []
    for link in parser.find_all('a'):
        # This assignment is simplifying a lot, should be made more robust
        text = link.contents[0].strip()

        if phrase in text:
            candidates.append((link['href'], text))

    return candidates


# Regularly checks for the latest news and pushes them to clients
def watch_and_push(configuration, news, pusher):
    while True:
        # Get recent news
        new_links = get_links(configuration['url'], configuration['phrase'])

        # Add them to news repository
        # TODO: Should there be a lock on `news` or is it not needed due
        # to Python's GIL?
        for link in new_links:
            news.add(*link)

        news.remove_old(configuration['age_limit'])

        # Push!
        for href, text in new_links:
            pusher_client.trigger('my-channel', 'my-event',
                                  {'href': href, 'text': text})

        # Get some rest
        time.sleep(configuration['delay'])


# Server to send the current news to new clients
def serve_on_start(configuration, news):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # TODO: this should be cached
            json_articles = [json.dumps({'href': a.href, 'text': a.text})
                             for a in news.get_all()]
            serialized = '[' + ','.join(json_articles) + ']'

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(serialized.encode('utf-8'))

    with http.server.HTTPServer(('localhost', 8080), Handler) as server:
        server.serve_forever()


if __name__ == '__main__':
    with open('configuration.yaml', 'r') as config_file:
        configuration = yaml.load(config_file)

    pusher_client = pusher.Pusher(
        **(configuration['pusher']),
        ssl=True)

    news = News()

    threading.Thread(target=watch_and_push,
                     args=(configuration, news, pusher)).start()
    threading.Thread(target=serve_on_start,
                     args=(configuration, news)).start()
