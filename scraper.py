import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'research_match':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))

from lxml import html
import _config
import _connections
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions, CategoriesOptions, ConceptsOptions
import unicodedata
import json
from random import randint
from time import sleep
#from selenium.common.exceptions import ElementNotVisibleException, StaleElementReferenceException
from progress_bar import progress
#from selenium.webdriver.common.keys import Keys

nlu = NaturalLanguageUnderstandingV1(version=_config.nlu_credentials["version"], username=_config.nlu_credentials["username"],
                                        password=_config.nlu_credentials["password"])
nlu.set_default_headers({'x-watson-learning-opt-out' : "true"})


def strip_non_unicode(text):
    return(unicodedata.normalize("NFKD", text.replace("'", '')).encode('ascii','ignore').decode())
    
def process_scraped(data, exp_length = 1, min_len = False):
    if min_len:
        if len(data) < min_len:
            raise ValueError('Data not in expected format.')
        return([strip_non_unicode(i).strip() for i in data])
    else:
        if len(data) != exp_length:
            raise ValueError('Data not in expected format.')
        return(strip_non_unicode(data[0]).strip())
 
def store_abstracts(link, webbrowser, db):
#    link, webbrowser, db = p_link, browser, DB
#    link, webbrowser, db = prev_progress['error_link'], browser, DB
    
    webbrowser.get('https://www.researchgate.net/'+link)
    sleep(randint(10,100)/10)
    article_tree = html.fromstring(webbrowser.page_source)

    publication_data = {'url_tag': link}
    
    published = {}
    try:
        published['page'] = 'https://www.researchgate.net/' + process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/a/@href'))
        published['name'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/a/text()'))
        published['reference'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')[:1])
        publication_data['publisher'] = published
        publication_data['date'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')[1:2]).replace('• ', '')
    except:
        try:
            publication_data['date'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/span/text()')).replace('• ', '')
        except:
            pass

    try:
        publication_data['views'] = int(process_scraped([i for i in article_tree.xpath('//div[@class="publication-meta"]/div/text()') if 'read' in i.lower()]).split(' ')[0])
    except:
        pass
                   
    try:
        publication_data['doi'] = process_scraped(article_tree.xpath('//div[@class="publication-meta"]/div/a/text()'))
    except:
        pass
    
    page_authors = []
    pub_authors = article_tree.xpath('//*[@class="publication-details__section"]/ul/li/div/div/div/div/div[2]/div/div/div/div')
    for auth in pub_authors:
        author = {}
        author['name'] = process_scraped(auth.xpath('div/a/text()'))
        try:
            author['page'] = process_scraped(auth.xpath('ul/li[1]/span/a/@href'))
        except ValueError:
            pass
        institution = {}
        try:
            institution['name'] = process_scraped(auth.xpath('ul/li[2]/span/a/text()'))
        except ValueError:
            pass
        try:
            institution['page'] = 'https://www.researchgate.net/' + process_scraped(auth.xpath('ul/li[2]/span/a/@href'))
        except ValueError:
            pass
        if len(institution) > 0:
            author['institution'] = institution
        page_authors.append(author)
    publication_data['authors'] = page_authors

        
    pub_abstract = False
    for i in range(2,5):
        try:
            pub_abstract = process_scraped(article_tree.xpath('//*[@class="publication-details__section"]/div[%i]/div[2]/div/text()' % (i)))
            publication_data['abstract'] = {'text': pub_abstract}
            try: 
                nlu_output = nlu.analyze(text=pub_abstract, features = Features(keywords= KeywordsOptions(), categories=CategoriesOptions(), concepts = ConceptsOptions())).result
                abs_categories = nlu_output["categories"]
                abs_concepts = nlu_output["concepts"]
                abs_keywords = nlu_output["keywords"]
                publication_data['abstract']['nlu'] = {'categories':abs_categories, 'concepts': abs_concepts, 'keywords': abs_keywords}
            except:
                print('NLU Error')
                pass
            break
        except:
            pass
    
    if 'abstract' in publication_data.keys() and publication_data['abstract']['text']:
        refs = add_references(webbrowser, db)
        publication_data['references'] = refs
        
    db.client.insert_one(publication_data)

    return(webbrowser, db)
    
    
def next_page(web_url):
    return(web_url.split('&page=')[0] + '&page=' + str(int(web_url.split('&page=')[-1]) + 1))
    
    
def scrape():
    DB = _connections.db_connection('mongo')
    
    
    with open(os.path.join(cur_path, 'last_error.json')) as f:
        prev_progress = json.load(f)    
    
    url = prev_progress['last_page']
#    url = 'https://www.researchgate.net/search/publications?q=marine%2Bscience&page=1'
    
    browser = _connections.sel_scraper(headless = False)
    
    while True:
        
        try:
            browser.get(url)#, headers=head)
            sleep(randint(10,100)/10)
            tree = html.fromstring(browser.page_source)
            
            paper_links = tree.xpath('//div[@class="react-container"]/div/div[2]/div[2]/div/div[2]/div/div[1]/div/div/div/div/div/div/div/div/div/div/a/@href')
            paper_links = [i.split('?')[0] for i in paper_links]
            
            if len(paper_links) == 0:
                DB.disconnect()
                browser.close()
                raise ValueError()
                
        except:
            with open(os.path.join(cur_path, 'last_error.json'), 'w') as fp:
                json.dump({'last_page':url}, fp) 
            DB.disconnect()
            browser.close()
            raise IndexError()
                                
        for p_link in paper_links:
#            dfas
            try:
                len(DB.client.find_one({'url_tag': p_link}))
                print('Article already archived, skipping')
            except:
                if 'book_review' in p_link.lower():
                    continue
                print(p_link)
                try:
                    browser, DB = store_abstracts(p_link, browser, DB)
                except:
                    print(p_link)
                    
                    with open(os.path.join(cur_path, 'last_error.json'), 'w') as fp:
                        json.dump({'error_link': p_link, 'last_page':url}, fp)                
                    DB.disconnect()
                    browser.close()
                    raise ValueError()
        url = next_page(url)


def add_references(_webbrowser, _db):
        article_tree = html.fromstring(_webbrowser.page_source)
#        if len(article_tree.xpath('//div[@class="temporarily-blocked"]')) > 0:
#            DB.disconnect()
#            _webbrowser.close()
#            DB = None
#            _webbrowser = None
#            raise ValueError('Login Error')
##            login(browser, url)
            
        if len(article_tree.xpath('//div[@class="captcha-container js-widgetContainer"]')) > 0:
            _db.disconnect()
            _webbrowser.close()
            _db = None
            _webbrowser = None
            print('Captcha Activated')
#            return(False)
            raise ValueError('Captcha Activated')

        article_tree = html.fromstring(_webbrowser.page_source)

        if True:
            sleep(1) 
            if len(_webbrowser.find_elements_by_xpath('//div[@class="nova-c-nav__wrapper"]/div[@class="nova-c-nav__items"]/button')) == 0:
#                continue
                raise Exception('No References')
            article_tree = html.fromstring(_webbrowser.page_source)    
            
            ref_tabs = article_tree.xpath('//div[@class="nova-c-nav__wrapper"]/div[@class="nova-c-nav__items"]/button/span/div/text()')
            ref_tab = [i for i in ref_tabs if 'references' in i.lower()][0]
            
            sel_refs = True
            if len(article_tree.xpath('//button[@class="nova-c-nav__item is-selected references js-lite-click" and ./span/div="%s"]' % (ref_tab))) > 0:
                sel_refs = False
            if len(article_tree.xpath('//button[@class="nova-c-nav__item references js-lite-click is-selected" and ./span/div="%s"]' % (ref_tab))) > 0:
                sel_refs = False
            ref_button = _webbrowser.find_elements_by_xpath('//button[./span/div="%s"]' % (ref_tab))
            _webbrowser.execute_script("window.scrollTo(0, %i);" % (ref_button[0].location['y'] - 100))

                
            if sel_refs:
                article_tree = html.fromstring(_webbrowser.page_source)    
                if len(article_tree.xpath('//button[@class="nova-c-nav__item is-selected references js-lite-click" and ./span/div="%s"]' % (ref_tab))) > 0:
                    sel_refs = False
                elif len(article_tree.xpath('//button[@class="nova-c-nav__item references js-lite-click is-selected" and ./span/div="%s"]' % (ref_tab))) > 0:
                    sel_refs = False
                else:
                        ref_button = _webbrowser.find_elements_by_xpath('//button[./span/div="%s"]' % (ref_tab))
                        _webbrowser.execute_script("window.scrollTo(0, %i);" % (ref_button[-1].location['y'] - 100))
                        ref_button[-1].click()
                        sel_refs = False

            article_tree = html.fromstring(_webbrowser.page_source)
            init_see_more = len(article_tree.xpath('//button[./span="Show more"]'))
            see_more = len(article_tree.xpath('//button[./span="Show more"]'))
            num_fails = 0
            while see_more == init_see_more:
                if see_more == 0:
                    break
                sleep(1)  
                load_fail = _load_more(_webbrowser)
                if load_fail:
                    num_fails += 1
                if num_fails > 20:
                    _db.disconnect()
                    _webbrowser.close()
                    _db = None
                    _webbrowser = None
                    print('Ref Error')
        #            return(False)
                    raise IndexError('Ref Error')                   

                article_tree = html.fromstring(_webbrowser.page_source)
                see_more = len(article_tree.xpath('//button[./span="Show more"]'))
                
        article_tree = html.fromstring(_webbrowser.page_source)
                
        references = article_tree.xpath('//div[@class="nova-v-publication-item__stack-item"]/div/a/@href')
        references = [i.split('?_sg')[0] for i in references]
        return(references)
        

def login(_browser, _url):
#    _browser, _url = browser, url
    
    link = _browser.find_element_by_link_text('Log in')
    link.click()

    username = _browser.find_element_by_name("login")
    password = _browser.find_element_by_name("password")
      
    try:
        username.send_keys(_config.research_gate_user)
    except:
        pass

    password.send_keys(_config.DB_PW)
    
    
    _browser.find_elements_by_xpath('//button[@class="nova-c-button nova-c-button--align-center nova-c-button--radius-m nova-c-button--size-m nova-c-button--color-blue nova-c-button--theme-solid nova-c-button--width-full action-submit"]')[-1].click()  
    _browser.get(_url) 
    
    return(_browser)
            

def _load_more(_browser):
    try:
        try:
            _load_button = _browser.find_elements_by_xpath('//button[./span="Show more"]')[0]
            _browser.execute_script("window.scrollTo(0, %i);" % (_load_button.location['y'] - 100))
            _load_button.click()
            return(False)
        except:
            _load_button = _browser.find_elements_by_xpath('//button[./span="Show more"]')[-1]
            _browser.execute_script("window.scrollTo(0, %i);" % (_load_button.location['y'] - 100))
            _load_button.click()
            return(False)
    except:
        return(True) 
                
                
def add_refs():
    DB = _connections.db_connection('mongo')
    browser = _connections.sel_scraper(headless = False)

#    total = DB.client.find({'references': {'$exists': False}, 'abstract': {'$exists': True}}).count()
    total = DB.client.find({'references': [], 'abstract': {'$exists': True}}).count()
    
    print('%i Documents need updating' % (total))
#    for doc_num, (doc) in enumerate(DB.client.find({'references': {'$exists': False}, 'abstract': {'$exists': True}})):
    for doc_num, (doc) in enumerate(DB.client.find({'references': [], 'abstract': {'$exists': True}})):
#        if doc_num < 7:
#            continue
#        sdafaf
#        print(doc['url_tag'])
        url = 'https://www.researchgate.net/'+doc['url_tag']
        sleep(randint(10,100)/25)

        browser.get(url) 
        article_tree = html.fromstring(browser.page_source)
        if len(article_tree.xpath('//div[@class="temporarily-blocked"]')) > 0:
            DB.disconnect()
            browser.close()
            DB = None
            browser = None
            raise ValueError('Login Error')
#            login(browser, url)
            
        if len(article_tree.xpath('//div[@class="captcha-container js-widgetContainer"]')) > 0:
            DB.disconnect()
            browser.close()
            DB = None
            browser = None
            print('Captcha Activated')
#            return(False)
            raise ValueError('Captcha Activated')
            
        article_tree = html.fromstring(browser.page_source)
        if True:
            sleep(1) 
            if len(browser.find_elements_by_xpath('//div[@class="nova-c-nav__wrapper"]/div[@class="nova-c-nav__items"]/button')) == 0:
                continue
                raise Exception('No References')
            article_tree = html.fromstring(browser.page_source)    
            
            ref_tabs = article_tree.xpath('//div[@class="nova-c-nav__wrapper"]/div[@class="nova-c-nav__items"]/button/span/div/text()')
            ref_tab = [i for i in ref_tabs if 'references' in i.lower()][0]
            
            sel_refs = True
            if len(article_tree.xpath('//button[@class="nova-c-nav__item is-selected references js-lite-click" and ./span/div="%s"]' % (ref_tab))) > 0:
                sel_refs = False
            if len(article_tree.xpath('//button[@class="nova-c-nav__item references js-lite-click is-selected" and ./span/div="%s"]' % (ref_tab))) > 0:
                sel_refs = False
            ref_button = browser.find_elements_by_xpath('//button[./span/div="%s"]' % (ref_tab))
            browser.execute_script("window.scrollTo(0, %i);" % (ref_button[0].location['y'] - 100))

                
            if sel_refs:
                article_tree = html.fromstring(browser.page_source)    
                if len(article_tree.xpath('//button[@class="nova-c-nav__item is-selected references js-lite-click" and ./span/div="%s"]' % (ref_tab))) > 0:
                    sel_refs = False
                elif len(article_tree.xpath('//button[@class="nova-c-nav__item references js-lite-click is-selected" and ./span/div="%s"]' % (ref_tab))) > 0:
                    sel_refs = False
                else:
                        ref_button = browser.find_elements_by_xpath('//button[./span/div="%s"]' % (ref_tab))
                        browser.execute_script("window.scrollTo(0, %i);" % (ref_button[-1].location['y'] - 100))
                        ref_button[-1].click()
                        sel_refs = False

            article_tree = html.fromstring(browser.page_source)
            init_see_more = len(article_tree.xpath('//button[./span="Show more"]'))
            see_more = len(article_tree.xpath('//button[./span="Show more"]'))
            num_fails = 0
            while see_more == init_see_more:
                if see_more == 0:
                    break
                sleep(1)  
                load_fail = _load_more(browser)
                if load_fail:
                    num_fails += 1
                if num_fails > 20:
                    DB.disconnect()
                    browser.close()
                    DB = None
                    browser = None
                    print('Ref Error')
        #            return(False)
                    raise IndexError('Ref Error')                   

                article_tree = html.fromstring(browser.page_source)
                see_more = len(article_tree.xpath('//button[./span="Show more"]'))
                
        article_tree = html.fromstring(browser.page_source)
                
#        article_tree = html.fromstring(browser.page_source) 
        references = article_tree.xpath('//div[@class="nova-v-publication-item__stack-item"]/div/a/@href')
        references = [i.split('?_sg')[0] for i in references]
        
#        references = article_tree.xpath('//div[@itemprop="citation"]/div/div/div/div/a/@href')    
        DB.client.update_one({'_id': doc['_id']}, {'$set': {'references': references}})
        progress(doc_num+1, total, status = '%i' % (doc_num+1))
    

if __name__ == '__main__':
    try:                                            # if running in CLI
        os.path.abspath(__file__)
        CLI = True
    except NameError:                               # if running in IDE
        CLI = False
    
    if CLI:
        scrape()
#        while True:
#            try:
#                add_refs()
#            except IndexError:
#                pass
