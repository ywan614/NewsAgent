import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from langchain.chat_models import AzureChatOpenAI
from langchain.chains import create_extraction_chain
from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import BeautifulSoupTransformer
from pprint import pprint
from openai import AzureOpenAI
import requests
import json

client = AzureOpenAI(
    api_key="2c167bc108b048b0bcfa3996772ee6d2",  
    api_version="2023-09-01-preview",
    azure_endpoint="https://bmd.openai.azure.com/"
)

deployment_name = 'gpt-4-1106'

# Set the current date
today_date = datetime.now().strftime("%Y-%m-%d")

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
    Fetch the latest news from the https://www.vapingpost.com/.

    :param url: URL of the Vapepost website.
    :return: List of the latest news articles.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find('div', id='tdi_17', class_='td_block_inner')
    
    extracted_content = extract(schema=schema, content=news_items)
    result = []

    for item in extracted_content:
        news_title = item['news_article_title']
        news_link = item['news_article_link']

        article_response = requests.get(news_link)
        article_soup = BeautifulSoup(article_response.content, 'html.parser')
        time_tag = article_soup.find('time')
        desc = article_soup.find('p', class_='td-post-sub-title')

        if time_tag and 'datetime' in time_tag.attrs:
            datetime_value = datetime.fromisoformat(time_tag['datetime']).strftime("%Y-%m-%d")
            if datetime_value == today_date:
                result.append({"news_title": news_title + ' ; 【description】 ' + desc.text, "news_link": news_link})

    pprint(result)
    return result

def get_latest_news_vapouround(url):
    """
    Fetch the latest news from the https://www.vapouround.co.uk/.

    :param url: URL of the Vapouround website.
    :return: List of the latest news articles.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    blocks = soup.find_all('article')
    result = []

    for block in blocks:
        extracted_content = extract(schema=schema_with_date, content=block)
        datetime_value = re.sub(r'(st|nd|rd|th)', '', extracted_content[0]['datetime'])
        datetime_value = datetime.strptime(datetime_value, "%d %B %Y").strftime("%Y-%m-%d")

        if datetime_value == today_date:
            result.append({"news_title": extracted_content[0]['news_article_title'], "news_link": extracted_content[0]['news_article_link']})
        else:
            break

    pprint(result)
    return result

def get_latest_news_vapeast(url):
    """
    Fetch the latest news from the https://vapeast.com/news/

    :param url: URL of the Vapouround website.
    :return: List of the latest news articles.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    blocks = soup.find_all('div',class_ = 'td-block-span4')
    result = []
    for block in blocks:
        extracted_content = extract(schema=schema_with_date, content=block)
        # Convert to datetime object
        datetime_obj = datetime.strptime(extracted_content[0]['datetime'], "%B %d, %Y")
        datetime_value = datetime_obj.strftime("%Y-%m-%d")
        if datetime_value == today_date:
            result.append({"news_title": extracted_content[0]['news_article_title'], "news_link": extracted_content[0]['news_article_link']})
        else:
            break

    pprint(result)
    return result

# Summarize the news
def gpt_summarize(combied,deployment_name):
    
  # Send a completion call to generate an answer
  response = client.chat.completions.create(
      model=deployment_name,
      messages=[{"role": "user", "content": f'''
                  [NEWS]: {combied}
  Use chinese to write a prompt to summarize [NEWS] related to vaping, ecig news and politics, 
  do not include any information related to elfbar,lostmary, funky republic, quaq, and try to avoid advertisement and other topics.
  divide topic into countries, following such order US>UK>GERMAN>Europe countries > Asia countries etc, if country name is mentioned, use coountry name,

  use following markdown format, if no news, do not write anything:

  -美国：
    > - 一些总结。[→](links)
    > - 一些总结  [→](links)

  -英国：
    > - 一些总结。[→](links)

  -法国:
    > - 一些总结。[→](links)
  -
  '''}]
  )
  print(response.choices[0].message.content)
  return response.choices[0].message.content

# Send message to dingding
def dingmessage(content):
    # Set the current date
  today_date = datetime.now().strftime("%Y-%m-%d")
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
  # 请求的URL，WebHook地址
  #webhook = f"https://oapi.dingtalk.com/robot/send?access_token=dfa6f4e4e393de72e64b3ee15a19a7a02962009f614964a1e6ac007c61381b11"
  #测试群
  webhook = f"https://oapi.dingtalk.com/robot/send?access_token=7dcc32614ae0fbeb72377cfc2860940c37b8d67c7d35e5b2288a177b34d27c0e"
  # 构建请求头部
  header = {"Content-Type": "application/json", "Charset": "UTF-8"}

  # 循环生成器并发送消息
  message = {
    "msgtype": "markdown",
    "markdown": {
        "title":"12月26日电子烟新闻",
        "text": f'''
    # <b> {today_date} 电子烟新闻 

    {content}

    ###### 爱奇迹洞察与数据项目组
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
  info = requests.post(url=webhook, data=message_json, headers=header, verify=False)  # 打印返回的结果
  print(info.text)


#write main function
def main():
    # Scrape data from specified URLs
    two_first_news = get_latest_news_twofirst(f"https://www.2firsts.cn/report/detail?date={today_date}")
    vape_post_news = get_latest_news_vapepost('https://www.vapingpost.com/')
    vapouround_news = get_latest_news_vapouround('https://www.vapouround.co.uk/news/')
    vape_post_vapeast = get_latest_news_vapeast('https://vapeast.com/news/')
    #combine all news
    combied = two_first_news + vape_post_news + vapouround_news + vape_post_vapeast
    sources = {
        'two_first_news':len(two_first_news),
        'vape_post_news':len(vape_post_news),
        'vapouround_news':len(vapouround_news),
        'vape_post_vapeast':len(vape_post_vapeast)
    }
    pprint(sources)
    #summarize the news
    summarized = gpt_summarize(combied,deployment_name)
    dingmessage(summarized)

    #save sources and summarized to md file
    with open(f'/Users/yuewang/Documents/coding/langchain/news scrap agent/output/{today_date}.md','w') as f:
        f.write(summarized)
        f.write('\n')
        f.write('sources:\n')
        f.write(str(sources))

# run main function
if __name__ == "__main__":
    main()



