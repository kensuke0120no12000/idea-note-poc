import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

# APIキーが設定されているか確認 (Google)
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is not set in the environment variables.")

KNOWLEDGE_BASE_DIR = "data/knowledge_base"

class InferenceEngine:
    def __init__(self):
        print("Initializing Inference Engine with Gemini...")
        self.qa_chain = self._build_chain()
        print("Inference Engine initialized.")

    def _build_chain(self):
        # 1. ドキュメントの読み込み
        loader = DirectoryLoader(
            KNOWLEDGE_BASE_DIR,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        documents = loader.load()

        # 2. テキストの分割
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)

        # 3. ベクトルストアの構築 (Gemini)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(texts, embeddings)
        retriever = vectorstore.as_retriever()

        # 4. プロンプトの定義
        prompt_template = """
        あなたはシステムの状況を判断し、次の行動を提案するAIアシスタントです。
        提供された「コンテキスト情報」を元に、与えられた「イベント」について、取るべきアクションを具体的に提案してください。
        
        コンテキスト情報:
        {context}
        
        イベント:
        {question}
        
        提案するアクション:
        """
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # 5. LLMとチェーンの構築 (Gemini)
        llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        return qa_chain

    def ask(self, query: str):
        """
        与えられたクエリ（イベント情報）に対して推論を実行する。
        """
        # クエリを整形して、よりLLMが理解しやすい形にする
        formatted_query = f"以下のイベントが発生しました。内容を分析し、対応を提案してください。\\n\\n{query}"
        
        result = self.qa_chain({"query": formatted_query})
        return {
            "answer": result["result"],
            "source_documents": [doc.metadata['source'] for doc in result['source_documents']]
        }

# シングルトンインスタンス
inference_engine = InferenceEngine() 