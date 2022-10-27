'''building the .csv'''
import re
from bs4 import BeautifulSoup
from requests import get
import pandas as pd
import unicodedata
from sys import getrecursionlimit
from sys import setrecursionlimit
import pandas as pd

recursionlimit = getrecursionlimit()
setrecursionlimit(recursionlimit**2)

def restore_windows_1252_characters(restore_string):
    def to_windows_1252(match):

        try:
                return bytes([ord(match.group(0))]).decode('windows-1252')
        
        except UnicodeDecodeError:
                return ''

    return re.sub(r'[\u0080-\u0099]', to_windows_1252, restore_string)


def search_for_centered_headers(tag):

    # easy way to end early is check if the 'align' keet is in attributes.
    if 'align' not in tag.attrs:
        return

    # define the criteria.
    criteria1 = tag.name == 'p'                # I want the tag to be name of 'p'
    criteria2 = tag.parent.name != 'td'        # I want the parent tag NOT to be named 'td'
    criteria3 = tag['align'] == 'center'       # I want the 'align' attribute to be labeled 'center'.


    # if it matches all the criteria then return the text.
    if criteria1 and criteria2 and criteria3:
        if re.match("(?i)Statement of Additional Information", tag.get_text(strip = True)) or re.match("(?i)SAI", tag.get_text(strip = True)):
            return tag.get_text(strip = True)
        

def get_txt_gen(cik, fil_type = '485'):
    '''it takes as input the cik of the company of interest and the type of filings we want to look for'''

    url = r"https://www.sec.gov/cgi-bin/browse-edgar"
    headers = {
    'user-agent': 'University of Milan Gaspare.Mattarella@studenti.unimi.it',
    'Accept-Encoding':'gzip, deflate',
    'Host': 'www.sec.gov'
    } # needed to avoid being blocked by the SEC

    params = {'action': 'getcompany', 'CIK': cik, 'type': fil_type} # params of the link
    url_request = get(url, headers = headers, params = params) # make the request
    html = url_request.content # extract content
    try:
        content_div = BeautifulSoup(html, features="lxml") # decode it
        content_div = content_div.body.find('div', attrs = {'id':'contentDiv'}) # limit the research to the content part of the html page
        content_div = content_div.find('div', attrs={'id':'seriesDiv'}) # we just need to go step by step
        content_div = content_div.table
        content_div = content_div.find_all('tr', attrs={'class':'blueRow'}) # those rows contains what we want

        for filex in content_div:
            if re.search("id=\"interactiveDataBtn\">", str(filex)): # those ones are duplicate in other formats
                pass
            else:
                str_mat = re.search(r'\/Archives(.*)htm', str(filex)).group() # we need the link
                comp = str_mat.split('/') # now we extract every component of the link between "/"
                url = r"https://www.sec.gov/Archives/edgar/data/" + comp[4] + '/' + comp[5] + '/index.json' # Here we can finally build the link to the page where all the files are stored
                dec = get(url, headers = headers).json()
                for doc in dec['directory']['item']:

                #here are contained all the links for the filings of that particualr company for every available year
                    if re.search("txt+$", doc['name']):
                        final_file = doc['name']
                        final_txt_url = r"https://www.sec.gov/Archives/edgar/data/" + comp[4] + '/' + comp[5] + '/' + final_file
                        yield final_txt_url # we finaly build a generator to list every document for a company
    except AttributeError:
        pass


def extract_info_2(url, dictx):
    try:
        headers = {'user-agent': 'University of Milan Gaspare.Mattarella@studenti.unimi.it', 'Accept-Encoding':'gzip, deflate','Host': 'www.sec.gov'}
        res = get(url, headers = headers)
        soup = BeautifulSoup(res.content, 'lxml')
        # define a dictionary that will house all filings.
        comp = url.split('/')
        # let's use the accession number as the key. This
        accession_number = comp[-1].split('.')[0]
        # add a new level to our master_filing_dict, this will also be a dictionary.
        master_filings_dict = dictx
        master_filings_dict[accession_number] = {}
        # this dictionary will contain two keys, the sec header content, and a documents key.
        master_filings_dict[accession_number]['sec_header_content'] = {}
        # grab the sec-header tag, so we can store it in the master filing dictionary.
        sec_header_tag = soup.find('sec-header')
        # store the tag in the dictionary just as is.
        master_filings_dict[accession_number]['sec_header_content']['sec_header_code'] = sec_header_tag

        for filing_document in soup.find_all('document'):
          document_id = filing_document.type.find(text=True, recursive=False).strip()
          if document_id not in ['485APOS','485BPOS']:
            pass
          else:
            filing_doc_text = filing_document.find('text')
            doc_soup = BeautifulSoup(str(filing_doc_text),features="html5lib")
            #doc_soup_text = str(doc_soup)
            centered_headers_found = doc_soup.find_all(search_for_centered_headers)

            if len(centered_headers_found) > 0:
                os = str(centered_headers_found[0])
                sai = str(filing_doc_text).split(os)
                doc_soup = BeautifulSoup(sai[1],features="html5lib")
                doc_text = doc_soup.html.body.get_text(' ', strip = True)
                page_text_norm = restore_windows_1252_characters(unicodedata.normalize('NFKD', doc_text))
                doc_text_norm = page_text_norm.replace('  ', ' ').replace('\n',' ')
                master_filings_dict[accession_number][document_id]= {}
                master_filings_dict[accession_number][document_id]['SAI'] = doc_text_norm
                print('-'*80)
                print('Document {} from file {} correctly stored'.format(document_id, accession_number))
            else:
                del master_filings_dict[accession_number]
    except:
        recursionlimit = getrecursionlimit()
        setrecursionlimit(2*recursionlimit)
            

def extract_tuple(dict_elem):
    for doc_id in dict_elem[1]:
        try:
            date_ = re.search("(?:FILED AS OF DATE:\t\t(.*.)\nDATE AS OF CHANGE)", str(dict_elem[1][doc_id]['sec_header_content']['sec_header_code'])).group(1)
            date_x = pd.to_datetime(date_).date()
            date_x = date_x.isoformat()
        except AttributeError:
            pass
        try:    
            sai = dict_elem[1][doc_id]['485BPOS']['SAI']
            tuplex = {'CIK': dict_elem[0], 'Date':date_x, 'Doc Number':doc_id,'Filing Type':'485BPOS','SAI': sai}
            yield tuplex
        except KeyError:
            pass
        try:
            sai = dict_elem[1][doc_id]['485APOS']['SAI']
            tuplex = {'CIK': dict_elem[0], 'Date':date_x, 'Doc Number':doc_id,'Filing Type':'485APOS','SAI': sai}
            yield tuplex
        except KeyError:
            pass
    
#import the list of tickers 

path_to_csv = input('Please enter the file path of the clean cik list: ')

tik = pd.read_csv(path_to_csv).to_numpy() 
#tik = pd.read_csv('/Users/hainex/projects/MutualFunds/clean_tickers_list.csv').to_numpy() 

tik = [x for cik in tik for x in cik]

master_filings_dict = {}
final_dict = []


for cik in tik:
    txt_generatorx = get_txt_gen(cik)
    for link in txt_generatorx:
        try:
            extract_info_2(link, master_filings_dict)
        except RuntimeError:
            pass
    final_dict.append((cik, master_filings_dict))
    print('-'*80)
    print('All the documents from {} Mutual Fund have been stored'.format(cik))

    

df = pd.DataFrame()

for elem in final_dict:
    gen = extract_tuple(elem)
    for x in gen:
        df = df.append(x, ignore_index=True)
        

df.to_csv('SAI_filings.csv', index=False)
print('ok, done!')
setrecursionlimit(recursionlimit)
