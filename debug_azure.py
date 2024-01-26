from langchain.document_loaders import AsyncHtmlLoader
from langchain.chat_models import ChatOpenAI,AzureChatOpenAI
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Get the current date in the format YYYY-MM-DD
today_date = datetime.now().strftime("%Y-%m-%d")

# os.environ['OPENAI_API_KEY'] = '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'

# os.environ["OPENAI_API_TYPE"] = "azure"
# os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"
# os.environ["AZURE_OPENAI_ENDPOINT"] = "https://bmd.openai.azure.com/"
# os.environ["OPENAI_API_KEY"] = "2c167bc108b048b0bcfa3996772ee6d2"

# llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")
llm = AzureChatOpenAI(
    openai_api_version = '2023-09-01-preview',
    azure_deployment= 'gpt-4',
    azure_endpoint='"https://bmd.openai.azure.com/"',
    api_key='2c167bc108b048b0bcfa3996772ee6d2',

)
from langchain.chains import create_extraction_chain

schema = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_ariticle link": {"type": "string"},
    },
    "required": ["news_article_title",'news_ariticle link'],
}

schema_with_date = {
    "properties": {
        "news_article_title": {"type": "string"},
        "news_ariticle link": {"type": "string"},
    },
    "required": ["news_article_title",'news_ariticle link'],
}



def extract(content: str, schema: dict):
    return create_extraction_chain(schema=schema, llm=llm).run(content)

from langchain.schema import HumanMessage
message = HumanMessage(
    content="Translate this sentence from English to French. I love programming."
)
llm([message])