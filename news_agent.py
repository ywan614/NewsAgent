# %%
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import create_extraction_chain
from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import BeautifulSoupTransformer
from pprint import pprint
from openai import AzureOpenAI
import requests
import json

client = AzureOpenAI(
    api_key="openai-key",  
    api_version="2023-09-01-preview",
    azure_endpoint="endpoint"
)

deployment_name = 'gpt-4-1106'
PAST_DAY = 1 #时间间隔，日更时为1

# Set the current date
#两个至上网站的新闻时间间隔
today_date = datetime.now().strftime("%Y-%m-%d")

#set past x date
#其他网站的新闻时间间隔
past_x_date = (datetime.now() - timedelta(days=PAST_DAY)).strftime("%Y-%m-%d")


# Initialize Azure Chat OpenAI
llm = AzureChatOpenAI(
    openai_api_version='2023-09-01-preview',
    deployment_name='gpt-35',
    azure_endpoint="https://bmd.openai.azure.com/",
    api_key='2c167bc108b048b0bcfa3996772ee6d2',
)

# Define schemas for extraction
schema = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_article_link": {"type": "string"},
    },
    "required": ["news_article_title", 'news_article_link'],
}

schema_with_date = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_article_link": {"type": "string"},
        "datetime": {"type": "string"},
    },
    "required": ["news_article_title", 'news_article_link', 'datetime'],
}

def extract(content: str, schema: dict):
    """
    Extract content based on the provided schema.

    :param content: HTML content to extract data from.
    :param schema: Schema definition for extraction.
    :return: Extracted data.
    """
    return create_extraction_chain(schema=schema, llm=llm).run(content)

def get_latest_news_twofirst(urls):
    """
    Scrape content from provided URLs using Playwright.

    :param urls: List of URLs to scrape.
    :param schema: Schema definition for extraction.
    :return: Extracted content.
    """

    print(f"Scraping {urls} URLs...")
    loader = AsyncHtmlLoader(urls)
    docs = loader.load()
    soup = BeautifulSoup(docs[0].page_content, 'html.parser')
    report_elements = soup.find_all(class_="report")
    extracted_content = extract(schema=schema, content=report_elements)
    pprint(extracted_content)
    return extracted_content


# Additional functions for scraping various websites

def get_latest_news_vapepost(url):
    """
    Fetch the latest news from the Vapepost website.

    :param url: URL of the Vapepost website.
    :return: List of the latest news articles.
    """

    print(f"Scraping {url} URL...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find('div', id='tdi_17', class_='td_block_inner')
    
    extracted_content = extract(schema=schema, content=news_items)
    result = []

    print(f"Extracting {len(extracted_content)} news articles...")
    for item in extracted_content:
        news_title = item['news_article_title']
        news_link = item['news_article_link']
        print (news_link,news_title)

        article_response = requests.get(news_link)
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        time_tag = article_soup.find('time')
        desc = article_soup.find('p', class_='td-post-sub-title')

        if time_tag and 'datetime' in time_tag.attrs:
            datetime_value = datetime.fromisoformat(time_tag['datetime']).strftime("%Y-%m-%d")
            if datetime_value >= past_x_date:
                print('add news:')
                print( news_title + ' ; 【description】 ' + desc.text, time_tag['datetime'])
                result.append({"news_title": news_title + ' ; 【description】 ' + desc.text, "news_link": news_link})
            else:
                print('out of date:')
                print( news_title + ' ; 【description】 ' + desc.text, time_tag['datetime'])

    pprint(result)
    return result

def get_latest_news_vapouround(url):
    """
    Fetch the latest news from the Vapouround website.

    :param url: URL of the Vapouround website.
    :return: List of the latest news articles.
    """
    print( f"Scraping {url} URL...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    blocks = soup.find_all('article')
    result = []
    print(f"Extracting {len(blocks)} news articles...")
    for block in blocks:
        extracted_content = extract(schema=schema_with_date, content=block)
        datetime_value = re.sub(r'(st|nd|rd|th)', '', extracted_content[0]['datetime'])
        datetime_value = datetime.strptime(datetime_value, "%d %B %Y").strftime("%Y-%m-%d")

        if datetime_value >= past_x_date:
            print('add news:')
            print( extracted_content[0]['news_article_title'] , extracted_content[0]['datetime'])
            result.append({"news_title": extracted_content[0]['news_article_title'], "news_link": extracted_content[0]['news_article_link']})
        else:
            print('out of date:')
            print( extracted_content[0]['news_article_title'] , extracted_content[0]['datetime'])
            break

    pprint(result)
    return result

def get_latest_news_vapeast(url):
    """
    Fetch the latest news from the https://vapeast.com/news/

    :param url: URL of the Vapouround website.
    :return: List of the latest news articles.
    """
    print( f"Scraping {url} URL...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    blocks = soup.find_all('div',class_ = 'td-block-span4')
    result = []
    print(f"Extracting {len(blocks)} news articles...")
    for block in blocks:
        extracted_content = extract(schema=schema_with_date, content=block)
        # Convert to datetime object
        datetime_obj = datetime.strptime(extracted_content[0]['datetime'], "%B %d, %Y")
        datetime_value = datetime_obj.strftime("%Y-%m-%d")
        if datetime_value >= past_x_date:
            print('add news:')
            print( extracted_content[0]['news_article_title'] , extracted_content[0]['datetime'])
            result.append({"news_title": extracted_content[0]['news_article_title'], "news_link": extracted_content[0]['news_article_link']})
        else:
            print('out of date:')
            print( extracted_content[0]['news_article_title'] , extracted_content[0]['datetime'])
            break

    pprint(result)
    return result

def get_latest_news_vape360(url):
    """
    Fetch the latest news from https://vaping360.com/vape-news/.

    :param url: URL of the Vapepost website.
    :return: List of the latest news articles.
    """

    print(f"Scraping {url} URL...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find('div', class_='category-block')
    
    extracted_content = extract(schema=schema, content=news_items)
    result = []

    print(f"Extracting {len(extracted_content)} news articles...")
    for item in extracted_content:
        news_title = item['news_article_title']
        news_link = item['news_article_link']
        print (news_link,news_title)

        article_response = requests.get(news_link)
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        article_header = article_soup.find('div', class_='general-header')
        article_content = extract(schema=schema_with_date, content=article_header)
        
        date_str = article_content[0]['datetime']
        date_obj = datetime.strptime(date_str, "%B %d, %Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        if formatted_date >= past_x_date:
            print('add news:')
            print( article_content[0]['news_article_title'] , article_content[0]['datetime'])
            result.append({"news_title": news_title, "news_link": news_link})
        else:
            print('out of date:')
            print( article_content[0]['news_article_title'] , article_content[0]['datetime'])
    pprint(result)
    return result


def get_latest_news_tobacco_reporter(url):
    """
    Fetch the latest news from the https://tobaccoreporter.com/

    :param url: URL of the Vapouround website.
    :return: List of the latest news articles.
    """
    print( f"Scraping {url} URL...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    blocks = soup.find_all('div',class_ = 'post-block-item style3')
    result = []
    extracted_content = extract(schema=schema_with_date, content=blocks)
    print(f"Extracting {len(extracted_content)} news articles...")
    for content in extracted_content:
    # Convert to datetime object
        datetime_obj = datetime.strptime(content['datetime'], "%B %d, %Y")
        datetime_value = datetime_obj.strftime("%Y-%m-%d")
        if datetime_value >= past_x_date:
            print('add news:')
            print( content['news_article_title'] , content['datetime'])
            result.append({"news_title": content['news_article_title'], "news_link": content['news_article_link']})
        else:
            print('out of date:')
            print( content['news_article_title'] , content['datetime'])

    pprint(result)
    return result

# Summarize the news
def gpt_summarize(combied,deployment_name):
  print(f"Summarizing using {deployment_name}...")
  # Send a completion call to generate an answer
  response = client.chat.completions.create(
      model=deployment_name,
      messages=[{"role": "user", "content": f'''
                  [NEWS]: {combied}
  You are a news reporter, Use chinese to summarize [NEWS] related to vaping, ecig news and politics, 
  and follow the rules below:
  
  - use as much as possible different sources.
  - try to avoid advertisement and other topics.
  - divide topic into countries, following such order US>UK>GERMAN>etc, if country name is mentioned, use country name.
  - Notice that China is the exporter of vape products, so any news which mentioned China and other countries, should be put into the other country's category.
  - try to conclude similar topics.
  - do not include any news related to specific brands: elfbar,lostmary.
  - do not include your explaination. 

  finally, use following markdown format, if no news, do not write anything:

美国：
> - 一些总结。[→](links)
> - 一些总结  [→](links)

-英国：
> - 一些总结。[→](links)

-法国:
> - 一些总结。[→](links)
  
  '''}]
  )
  print(response.choices[0].message.content)
  return response.choices[0].message.content

print(f'past date: {past_x_date}')
print(f'today{today_date}')

# %%

# Scrape data from specified URLs
two_first_news = get_latest_news_twofirst(f"https://www.2firsts.cn/report/detail?date={today_date}")
vape_post_news = get_latest_news_vapepost('https://www.vapingpost.com/')
vapouround_news = get_latest_news_vapouround('https://www.vapouround.co.uk/news/')
vape_post_vapeast = get_latest_news_vapeast('https://vapeast.com/news/')
vape_360_news = get_latest_news_vape360('https://vaping360.com/vape-news/')
tobacco_reporter_news = get_latest_news_tobacco_reporter('https://tobaccoreporter.com/')
vape_voice_news = get_latest_news_tobacco_reporter('https://vaporvoice.net/')


# %%
# Get Result
combied = two_first_news + vape_post_news + vapouround_news + vape_post_vapeast + vape_360_news \
+ tobacco_reporter_news + vape_voice_news
sources = {
    'two_first_news':len(two_first_news),
    'vape_post_news':len(vape_post_news),
    'vapouround_news':len(vapouround_news),
    'vape_post_vapeast':len(vape_post_vapeast),
    'vape_360_news':len(vape_360_news),
    'tobacco_reporter_news':len(tobacco_reporter_news),
    'vape_voice_news':len(vape_voice_news)
}
pprint(sources)



# %%

# summarized = gpt_summarize(combied,deployment_name)
summarized = gpt_summarize(combied,deployment_name)
#save sources and summarized to md file
with open(f'./output/{today_date}.md','w') as f:
    f.write(summarized)
    f.write('\n')
    f.write('sources:\n')
    f.write(str(sources))



# %%
from datetime import datetime

# Send message to dingding
def dingmessage(content):
    # Set the current date
    today_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 构建请求头部
    header = {"Content-Type": "application/json", "Charset": "UTF-8"}

    # 循环生成器并发送消息
    message = {
    "msgtype": "markdown",
    "markdown": {
        "title":f"{today_date}电子烟新闻",
        "text": f'''
# <b> {today_date} 电子烟新闻 
{content}
###### 爱奇迹洞察与数据BI组
###### {current_time}发布 
            '''
        },
        "at": {
            "atMobiles": [
                "150XXXXXXXX"
            ],
            "atUserIds": [
                "user123"
            ],
            "isAtAll": False
        }
    }


    message_json = json.dumps(message)

    # 请求的URL，WebHook地址
    #I&I 小群
    ii_webhook = f"https://oapi.dingtalk.com/robot/send?access_token=c1fafba29851c42474583b1f405dd242a6c91a94933e083e9ca1a9ef10aec305"
    #BMD 大群
    bmd_webhook = f"https://oapi.dingtalk.com/robot/send?access_token=459f14525095eab35ad2e6e610e7bddae9229539928c9f28c38186c1debe9ac0"
    #公关群
    pr_webhook = "https://oapi.dingtalk.com/robot/send?access_token=4d516b6bca6e47a3925025b15c5ce850ec1a13ff0b7f2ea36f2d61d3c21d36f7"

    #测试群
    test_webhook = f"https://oapi.dingtalk.com/robot/send?access_token=4882d356078def127f660c9e497fbc6096fbb3784fca3de816077b94475abd7b"

    #产品小群
    product_webhook = 'https://oapi.dingtalk.com/robot/send?access_token=2150a04d503fb54ffab49c4c8028472c772cd05bcdd688f8683cbd94004b36cf'

    #新兴大区群
    new_area_webhook = 'https://oapi.dingtalk.com/robot/send?access_token=d4a6960503dccbf2744aceb594be9c93d630f9fa9a828ac271ba3951366a798e'

    #MKT 总部群
    mkt_base_webhook = 'https://oapi.dingtalk.com/robot/send?access_token=a61b603a9508ae5e996272277b110f01563d52a95138e57129cbc056e3502dc5'

    hooklist = [ii_webhook,
                bmd_webhook,
                pr_webhook,
                test_webhook,
                product_webhook,
                new_area_webhook,
                mkt_base_webhook
                ]
    #single sent
    # info = requests.post(url=mkt_base_webhook, data=message_json, headers=header, verify=False)  # 打印返回的结果
    # print(info.text)

    #loop sent
    for webhook in hooklist:
        info = requests.post(url=webhook, data=message_json, headers=header, verify=False)  # 打印返回的结果
        print(info.text)

#read md file and send to dingding
# Set the current date
today_date = datetime.now().strftime("%Y-%m-%d")

with open(f'./output/{today_date}.md','r') as f:
# with open(f'./output/2024-01-08.md','r') as f:
    summarized = f.read()

#delete lines starts with sources and below
summarized = summarized.split('sources:')[0]
print(summarized)

# dingmessage(summarized)

# %%



