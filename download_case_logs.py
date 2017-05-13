import requests
import sys
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs, ParseResult
from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.link = []
    self.td = False
    self.a = False

  def handle_starttag(self, tag, attrs):
    attr_dict = dict(attrs)
    if tag == 'td':
      self.td = True
    elif tag == 'a' and self.td and 'viewdetail.asp' in attr_dict.get('href'):
      self.link.append(attr_dict.get('href'))
      self.a = True
    elif tag == 'img' and self.td and 'CLINICAL NOTES' in attr_dict.get('onmouseover', ''):
      download_pdf(self.link)

  def handle_endtag(self, tag):
    if tag == 'td':
      self.td = False
      self.link = []
    elif tag == 'a':
      self.a = False

  def handle_data(self, data):
    if self.a:
      self.link.append(data)

def download_pdf(links):
  summary_link, case = links
  query = {'myurl': summary_link, 'myname': 'viewdetails-1721-20170302', 'mydb': 'patu'}
  export_url = "https://www6.typhongroup.net/pdfoutput-past.asp?%s" % urlencode(query)
  headers = {'Referer': summary_link}

  print 'Downloading %s' % case + '.pdf'
  r = requests.get(export_url, headers=headers)

  with open(case + '.pdf', 'wb') as out:
    out.write(r.content)

if __name__ == '__main__':
  with open(sys.argv[1]) as f:
    parser = MyHTMLParser()
    parser.feed(f.read())
 
