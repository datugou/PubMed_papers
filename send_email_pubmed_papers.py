import random, json, re, time, os
import xmltodict

import pandas as pd

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

import requests
from bs4 import BeautifulSoup as bs

term = '((AAV) OR (rAAV)) NOT (ANCA)' #设置文献检索词
reldate = 2 #设定只检索最近 7 天发表的文献

# 需要在 Settings → Secrets → Dependabot → New repository secret 设置邮箱服务器信息
try:
    mail_host = 'smtp.163.com'
    mail_user = os.environ.get('MAIL_USER')
    mail_pass = os.environ.get('MAIL_PASS')
    sender = os.environ.get('SEND_MAIL')
    receivers = [os.environ.get('RECEIVE_MAIL')]
    print(type(mail_user))
    print(mail_user == 'guominjunl')
    print(os.getenv('MAIL_PASS') == 'guominjunl')
    print(mail_user == os.getenv('MAIL_PASS'))
except:
    print('未设置邮箱信息')

def get_pmidl(term, reldate):
    '''根据检索词获取文献的 pmid，返回 n 个文献的 list'''
    term = term.replace(' ','+')
    url_ncbi_home = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    db = 'pubmed'
    
    retmax = 999999 #搜索结果返回的最大数

    # 获取检索结果的pmid list
    url = url_ncbi_home + '?db=%s&term=%s&reldate=%d&retmax=%d'%(db, term, reldate, retmax)
    resp = requests.get(url)    
    jsf = xmltodict.parse(resp.text)
    if jsf['eSearchResult']['Count'] != '0':
        idl = jsf['eSearchResult']['IdList']['Id']
    print('共', len(idl), '篇')
    return idl
  
def get_CiteScore(jnm):
    '''根据杂志名获取影响因子 cts 和 JCR 分区'''
    data = {
        'searchname': jnm,
        'view': 'search',
        'searchsort': 'relevance'
    }

    resp = requests.post('https://www.letpub.com.cn/index.php?page=journalapp&view=search',  data = data)
    soup = bs(resp.text)
    try:
        jnn = soup.find_all('tr')[4].find_all('td')[1].font.get_text()
        score = re.findall('CiteScore:([0-9\.]+)', soup.find_all('tr')[4].find_all('td')[3].get_text())[0]
        jcr = soup.find_all('tr')[4].find_all('td')[4].get_text()
    except:
        if soup.find_all('title')[0].get_text() == '您刷新页面的速度过快':
            print('您刷新页面的速度过快,等待。。。')
            time.sleep(30)
            return get_CiteScore(jnm)
    return jnn, score, jcr
  
def get_IF(jnm):
    '''根据杂志名获取影响因子 IF 和 CS 分区'''
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',}

    resp = requests.get('https://www.medsci.cn/sci/index.do?fullname='+jnm, headers= headers)
    try:
        sour = re.findall('影响指数：([0-9\.]+)',resp.text)[0]
    except:
        sour = re.findall('影响指数：([0-9\.暂无数据]+)',resp.text)[0]
    ti = re.findall('title="(.+)"',resp.text)[0]
    jid = re.findall('submit.do\?id=([a-zA-Z0-9]+)', resp.text)[0]
    u2 = 'https://www.medsci.cn/sci/journal.do?id=%s'%(jid)
    r2 = requests.get(u2, headers= headers)
    cts = re.findall('"citescore":(.+?)[,}]', r2.text)[0]
    return jnm, ti, sour, cts
  
def get_paper_info_by_pmidL(idl):
    '''根据 pmid 的列表，抓取文献的详细信息，返回一个 list'''
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&rettype=abstract'%(','.join(idl[:-1]))
    resp = requests.get(url)    
    jsf = xmltodict.parse(resp.text)
    
    
    table = []
    progress = 0
    for i in jsf['PubmedArticleSet']['PubmedArticle']:
        progress+=1
        if progress%10 == 0:
            print(progress)
        pmid = i['MedlineCitation']['PMID']['#text']
    #     print(i['MedlineCitation'].keys())

        doi = ''
        doil = i['PubmedData']['ArticleIdList']['ArticleId']
        if type(doil) == type([]):
            for j in doil:
                if j['@IdType'] == 'doi':
                    doi = j['#text']
        else:
            j = doil
            if j['@IdType'] == 'doi':
                doi = j['#text']
        TI = i['MedlineCitation']['Article']['ArticleTitle']
        if type(TI) == type('str'):
            TIt = TI
        elif type(TI) == type([]):
            TIt = ' '.join([ttt['@Label'] + ': ' + ttt['#text'] for ttt in TI])
        elif isinstance(TI, dict):
            TIt = TI['#text']
        else:
            TIt = str(TI)

        DATE = i['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].values()
        if len(DATE)==1:
            if isinstance(DATE, dict):
                Y = DATE.values()[0]
            else:
                Y = DATE
                M = '?'
        elif len(DATE)==2:
            Y,M = DATE 
        else:
            Y,M,D = DATE

        # author
        authors = []

        if type(i['MedlineCitation']['Article']['AuthorList']['Author']) == type([]):
            for j in i['MedlineCitation']['Article']['AuthorList']['Author']:
                if 'LastName' in j.keys():
                    author = j['LastName']+' '+j['ForeName']

                    aff = []
                    if 'AffiliationInfo' in j.keys():
                        if type(j['AffiliationInfo']) == type([]):
                            for k in j['AffiliationInfo']:
                                aff.append(k['Affiliation'])
                        else:
                            aff.append(j['AffiliationInfo']['Affiliation'])
                else:
                    author = '?'
                    aff = []
                authors.append([author, aff])
        else:
            j = i['MedlineCitation']['Article']['AuthorList']['Author']
            author = j['LastName']+' '+j['ForeName']
            aff = []
            if 'AffiliationInfo' in j.keys():
                if type(j['AffiliationInfo']) == type([]):
                    for k in j['AffiliationInfo']:
                        aff.append(k['Affiliation'])
                else:
                    aff.append(j['AffiliationInfo']['Affiliation'])
            authors.append([author, aff])

        # 摘要
        if 'Abstract' in i['MedlineCitation']['Article'].keys():
            AB = i['MedlineCitation']['Article']['Abstract']['AbstractText']
            tags = ''
            if type(AB) == type('str'):
                ABt = AB
            elif type(AB) == type([]):
                ABt = ' '.join([ttt['@Label'] + ': ' + ttt['#text'] for ttt in AB])
            elif isinstance(AB, dict):
                ABt = AB['#text']
                if 'i' in AB.keys():
                    if type(AB['i']) == type([]):
                        try:
                            tags = '|'.join([r if type(r)==type('str') else r['#text'] for r in AB['i']])
                        except:
                            tags = AB['i']
                    else:
                        tags = AB['i']
            else:
                ABt = str(AB)
        else:
            tags = ''
            ABt = ''

        # 杂志+影响因子
        jnm = i['MedlineCitation']['Article']['Journal']['Title']
        jnms = i['MedlineCitation']['Article']['Journal']['ISOAbbreviation']
        try:
            jnm,jnmu,IF,cts = (get_IF(jnm))
        except:
            try:
                jnm,jnmu,IF,cts = (get_IF(jnms))
            except:
                jnm,jnmu,IF,cts = jnm, jnm, 'eeee','eeee'

        try:
            _,CS,JCR = (get_CiteScore(jnm))
        except:
            try:
                _,CS,JCR = (get_CiteScore(jnms))
            except:
                _,CS,JCR = jnm, 'EEEE', 'EEEE'

        # 文章类型
        tps = i['MedlineCitation']['Article']['PublicationTypeList']['PublicationType']
        if type(tps) == type([]):
            for j in tps:
                tpid = j['@UI']
                tp = j['#text']
        else:
            j = tps
            tpid = j['@UI']
            tp = j['#text']

        table.append([pmid, doi, Y, M, tpid, tp, TIt, ABt, jnm, jnms, IF, CS,cts, JCR, tags, authors])
        
    return table

def send_email(file_name):
    #设置eamil信息
    #添加一个MIMEmultipart类，处理正文及附件
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receivers[0]
    message['Subject'] = 'pubmed 文献推送'

    #添加一个txt文本附件
    with open(file_name,'rb')as h:
        content2 = h.read()


    #设置txt参数
    part2 = MIMEText(content2,'plain','utf-8')
    #附件设置内容类型，方便起见，设置为二进制流
    part2['Content-Type'] = 'application/octet-stream'
    #设置附件头，添加文件名
    part2['Content-Disposition'] = 'attachment;filename="%s"'%(file_name.split('\\')[-1])

    message.attach(part2)

    #登录并发送
    print(mail_user, mail_pass)
    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host,25)
        smtpObj.login(mail_user,mail_pass)
        smtpObj.sendmail(
            sender,receivers,message.as_string())
        print('success')
        smtpObj.quit()
    except smtplib.SMTPException as e:
        print('error',e)

        
def main():
    idl = get_pmidl(term, reldate)
    table = get_paper_info_by_pmidL(idl)
    print('文献列表已获取')
    df_if = pd.DataFrame(table, columns = ['PMID', 'DOI', 'Y', 'M', 'TYPE_ID', 'TYPE', 'TI', 'AB', 'J', 'J_abb', 'IF', 'CS', 'cts', 'JCR', 'tags', 'authors'])
    tds = time.strftime('%Y-%m-%d')
    df_if.to_csv('pubmed_papers.%s.csv'%(tds), encoding='u8')
    send_email('pubmed_papers.%s.csv'%(tds))
    print('邮件已发送')
main()
