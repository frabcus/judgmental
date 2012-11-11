= TODO =

Arranged here, unlike on the Gh issues page, in vague order of priority.

There is a necessary balancing act between working on the website UI and
features to make it more attractive and useful to end-users, and working
on the behind-the-scenes processing workflow and text management to make
it easier to maintain and develop.

Obviously, everything wants done "as quickly as possible" :)

* Site Search (using Google) *enhancement*
* Analyse and interpret BAILII links *bug* *important*
    - Judgment reference: turn into one of our links
    - Legislation
    - Other (keep)
* Tabs for main sections on home page
* Duplicate citation errors *bug* *important*
    - Mostly done; see 301e71a21643
    - "we just need to create links to disambiguation pages as appropriate"
* Manage changing filenames *enhancement* *important*
* Accessibility audit
* Improve layout on smaller screens
* RSS feeds
* Make a sitemap.xml for Google *enhancement*
* Legal stuff:
    * Takedown links
    * Redaction & data protection policy
* Tagging judgments
* Install feedparser (needed by legislation.py)
* Structured data - judge name, date, court, party name
    * How to collect?
        * http://gate.ac.uk?
    * How to store?
        * Triplestore?
* Interface to the formatter - config file or web
* Generate valid HTML! *bug*
* Support citation capture (eg Zotero) *enhancement*
* Specify the open source license of the code
* Put something in robots.txt
* Investigate using annotateit.org for comments
* Add links to Civil Procedure Rules *enhancement*
* Browser toolbar to add judgments to judgmental *enhancement*
* Scrape HUDOC
* Register with Google Webmaster Tools *enhancement*
* Link to legislation.gov.uk *enhancement*
* Improve logging on failures
* Improve output page formats (make use of xrefs) *enhancement*
* Mark up ids of companies named in cases *enhancement*
* Judgments issued in Comic Sans - fix!
* Offer download of all the HTML of all the case law
* App - case updates
* Annotations on each judgment using Disqus *enhancement*
