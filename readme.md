This is a proof of concept of an application watching websites change,
scrape them for new information and if the data are deemed relevant
they are pushed to all listening clients using [Pusher](https://pusher.com/).

To move this closer to a useful application one would probably want to
add more phrases to be looked for, more pages to be searched, better
parsing of pages (currently the only content of the anchor tag the
application can process is text) and optimize the whole code base for
speed (I was quite happy to use a heap for the news sorted by time on
the server but maybe there's a better data structure for that too).

**Usage**. Download this repository, run `pip install` in `server`
directory, copy sample configuration to `configuration.yaml`, put in
your values, and finally `python server.py` (Python 3.6 needed). The
client is self-contained (thanks to CDNs), just open
`client/client.html`.
