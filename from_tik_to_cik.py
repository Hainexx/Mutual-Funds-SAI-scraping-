from bs4 import BeautifulSoup
import re
import numpy as np
from requests import get
import pandas as pd

class Thickers:

        def __init__(self, ticker):
                self.ticker = ticker
                 
                

        def get_cik(self):
                ticks = self.ticker
                url = r"https://www.sec.gov/cgi-bin/series"
                headers = {'user-agent': 'University of Milan Gaspare.Mattarella@studenti.unimi.it', 'Accept-Encoding':'gzip, deflate','Host': 'www.sec.gov'}        
                for tix in ticks:
                        params = {'ticker': tix}
                        content = get(url, headers = headers, params = params).content
                        content = BeautifulSoup(content, features="lxml")
                        try:
                                cik_c = re.search(r"(?:/cgi-bin/browse-edgar\?CIK=(C.*.)&amp;action=getcompany&amp)", str(content)).group(1)

                                yield cik_c

                        except:
                                yield 'Na'


tickers_list = []

path_to_csv = input('Please enter the file path of the tikers list: ')

tik_s = pd.read_csv(path_to_csv)
tik_s = np.array(tik_s)
tik_s = tik_s.tolist()
full_cik_list = list()

for x in tik_s:
        full_cik_list.append(x[0])

num = int(input('Please enter the number of maxium tickers to extrapolate: '))

tix_pt2 = Thickers(full_cik_list[:num])
cik_cs = tix_pt2.get_cik()

cik_list = []
for cik in cik_cs:
  cik_list.append(cik)

#tickers_list = np.array(pd.read_csv('/Users/hainex/projects/MutualFunds/full_tickers_list.csv')).tolist()
#full_tickers = []
#for ci in tickers_list:
#        full_tickers.append(ci[0])

index_list=[]
for i, value, in enumerate(cik_list):
        index_list.append(i)

na_index = [i for i, value in enumerate(cik_list) if value == 'Na']

for i, n in enumerate(full_cik_list[:num]):
        if i in na_index:
                full_cik_list[:num].pop(i)

na_tickers = [value for i, value in enumerate(full_cik_list) if i in na_index]

new_tik_list = cik_list.copy()
try:
        while 1:
                new_tik_list.remove('Na')
except ValueError:
        pass


ls = pd.DataFrame(new_tik_list)
ls.to_csv('clean_cik_list.csv', index=False)
print('Great, a clean_cik_list.csv file has been produced in the current folder')