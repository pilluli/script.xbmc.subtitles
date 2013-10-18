# -*- coding: utf-8 -*-

import os, sys, re, xbmc, xbmcgui, string, urllib, urllib2, socket
from utilities import log, languageTranslate
from BeautifulSoup import BeautifulSoup


_ = sys.modules[ "__main__" ].__language__

self_host = "http://www.addic7ed.com"
self_release_pattern = re.compile(" \nVersion (.+), ([0-9]+).([0-9])+ MBs")
verbose = True

def compare_columns(b,a):
    return cmp( a["sync"], b["sync"] ) or cmp( b["language_name"], a["language_name"] )
    
def get_url(url):
    #req_headers = { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US)','Referer': 'http://www.addic7ed.com/'}
    #request = urllib2.Request(url, headers=req_headers)
    #opener = urllib2.build_opener()
    #response = opener.open(request)
    #contents = response.read()

    cmd = 'wget --referer=http://www.addic7ed.com -O /tmp/xbmc_subtitles.txt ' + url
    if verbose:
        print 'ADDIC7ED: executing |' + cmd + '|'
    os.system(cmd)
    fid = open('/tmp/xbmc_subtitles.txt','r')
    contents = fid.read()
    fid.close()
    os.remove('/tmp/xbmc_subtitles.txt')

    return contents    

def query_TvShow(name, season, episode, file_original_path, langs):
    sublinks = []
    name = name.lower().replace(" ", "_").replace("$#*!","shit").replace("'","") # need this for $#*! My Dad Says and That 70s show
    searchurl = "%s/serie/%s/%s/%s/addic7ed" %(self_host, name, season, episode)
    if verbose:
        print 'ADDIC7ED: searchurl = |' + searchurl + '|'
    socket.setdefaulttimeout(5)
    page = urllib2.urlopen(searchurl)
    content = page.read()

    if verbose:
        text_file = open("/tmp/addicted_page.html", "w")
        text_file.write(content)
        text_file.close()

    content = content.replace('\n','')

    tables = content.split('<div id="container95m">')[1:-1]
    if verbose:
        print 'ADDIC7ED: tables len = ' + str(len(tables))

    for t in tables:

        # Get NewsTitle
        try:
            subteams = re.search('<td colspan="3" align="center" class="NewsTitle"><img src="/images/folder_page.png" width="16" height="16" />.*Version (.+?), ([0-9]+).([0-9])+ MB.*',t,re.M).groups()[0]
        except:
            if verbose:
                print 'ADDIC7ED: No subteams found, do nothing else'
            subteams = ''
            break
        if verbose:
            print 'ADDIC7ED: subteams = ' + subteams

        # Get NewsDate
        try:
            info_html = re.search(r'<td class="newsDate" colspan="3">(.*?)<img.*',t,re.M).groups()[0].replace('\t','').replace('\n','').strip()
        except:
            info_html = ''
      
        if verbose:
            print 'ADDIC7ED: info = ' + info_html

        # Parse all languages
        for l in t.split('<td width="21%"')[1:]:
      
            wrong = False

            try:
                fullLanguage = re.search('class="language">(.+?)<a',l,re.M).groups()[0].replace('\n','')
            except:
                fullLanguage = ''
                wrong = True

            if verbose:
                print 'ADDIC7ED: fullLanguange = ' + fullLanguage

            try:
                lang = languageTranslate(fullLanguage,0,2)
            except:
                lang = ""

            # if subteams is in the filename hash it!
            file_name = os.path.basename(file_original_path).lower()
            hstr = subteams + '-' + info_html
            hashed = False
            try:
                for ss in hstr.replace('.','-').split('-'):
                    if ss.find('720p') == -1:
                        if ss.find('1080') == -1:
                            if file_name.find(str(ss)) > -1:
                                hashed = True
            except:
                pass

            if verbose:
                if hashed:
                    print 'ADDIC7ED: hasdhed = TRUE'
                else:
                    print 'ADDIC7ED: hasdhed = FALSE'


            # Get status
            try:
                status = re.search('<td width="19%"><b>(.+?)</b>',l).groups()[0].strip()
            except:
                status = ''
      
            if verbose:
                print 'ADDIC7ED: status = |' + str(status) + '|' 

            # Get Hearing Impaired
            if l.find('Hearing Impaired') > -1:
                hi = '(HI)'
            else:
                hi = ''

            # Get link (try most updated first)
            try:
                if re.search('</strong></a>.*<a class="buttonDownload" href="(.+?)"><strong>most updated',l,re.M):
                    link = re.search('</strong></a>.*<a class="buttonDownload" href="(.+?)"><strong>most updated',l,re.M).groups()[0]
                else:
                    link = re.search('<a class="buttonDownload" href="(.+?)"><strong>',l,re.M).groups()[0]
                    
                link = "%s%s"%(self_host,link)
            except:
                link = ''
                wrong = True

            if verbose:
                print 'ADDIC7ED: link = |' + str(link) + '|' 
            

            # Submit subtitle to script
            if not wrong and status.find("Completed") > -1 and (lang in langs):
                sublinks.append({'filename':"%s %s %s" % ( subteams,hi,info_html ),'link':link,'language_name':fullLanguage,'language_id':lang,'language_flag':"flags/%s.gif" % (lang,),'movie':"movie","ID":"subtitle_id","rating":"0","format":"srt","sync":hashed})

    return sublinks
 
def query_Film(name, file_original_path,year, langs):
    sublinks = []
    name = urllib.quote(name.replace(" ", "_"))
    searchurl = "%s/film/%s_(%s)-Download" %(self_host,name, str(year))
    socket.setdefaulttimeout(5)
    page = urllib2.urlopen(searchurl)
    content = page.read()
    content = content.replace("The safer, easier way", "The safer, easier way \" />")
    soup = BeautifulSoup(content)
    for subs in soup("td", {"class":"NewsTitle", "colspan" : "3"}):
      try:
        langs_html = subs.findNext("td", {"class" : "language"})
        fullLanguage = str(langs_html).split('class="language">')[1].split('&nbsp;<a')[0].replace("\n","")
        subteams = self_release_pattern.match(str(subs.contents[1])).groups()[0].lower()
        file_name = os.path.basename(file_original_path).lower()
        if (file_name.find(str(subteams))) > -1:
          hashed = True
        else:
          hashed = False  
        try:
          lang = languageTranslate(fullLanguage,0,2)
        except:
          lang = ""
        if verbose:
          print 'ADDIC7ED: fullLang = |' + str(fullLanguage) + '|' 
          print 'ADDIC7ED: lang = |' + str(lang) + '|' 
        statusTD = langs_html.findNext("td")
        status = statusTD.find("strong").string.strip()
        link = "%s%s"%(self_host,statusTD.findNext("td").find("a")["href"])
        if status == "Completed" and (lang in langs) :
            sublinks.append({'filename':"%s-%s" %(name.replace("_", ".").title(),subteams ),'link':link,'language_name':fullLanguage,'language_id':lang,'language_flag':"flags/%s.gif" % (lang,),'movie':"movie","ID":"subtitle_id","rating":"0","format":"srt","sync":hashed})
      except:
        pass
    return sublinks    


def search_subtitles( file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack ): #standard input
    subtitles_list = []
    langs = []
    langs.append(languageTranslate(lang1,0,2))
    if lang1 != lang2:
      langs.append(languageTranslate(lang2,0,2))
    if lang3 != lang1 and lang3 != lang2:
      langs.append(languageTranslate(lang3,0,2))
    msg = ""
    log( __name__ ,"Title = %s" %  title)
    if len(tvshow) == 0: # TV Shows
        subtitles_list = query_Film(title, file_original_path,year, langs)
    else:
        subtitles_list = query_TvShow(tvshow, str(season), str(episode),file_original_path, langs)
        if( len ( subtitles_list ) > 0 ):
            subtitles_list = sorted(subtitles_list, compare_columns)
    return subtitles_list, "", msg #standard output


def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id): #standard input
    url = subtitles_list[pos][ "link" ]
    file = os.path.join(tmp_sub_dir, "adic7ed.srt")

    if verbose:
        print 'ADDIC7ED: Downloading url = |' + str(url) + '|'
    f = get_url(url)

    local_file_handle = open(file, "w" + "b")
    local_file_handle.write(f)
    local_file_handle.close() 
   
    language = subtitles_list[pos][ "language_name" ]
    return False, language, file #standard output
