from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .config import config

agent_model = ChatOpenAI(model=config.APP_MODEL, streaming=True, name="main")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1024)
