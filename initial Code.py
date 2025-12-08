import os
from dotenv import load_dotenv

#TODO 문서 찾기
# 1. 도구 가져오기 (Gemini 전용)
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from operator import itemgetter
except ModuleNotFoundError as e:
    import sys
    print(f"❌ 모듈 누락: {e.name}")
    print("다음 명령어로 필요한 패키지를 설치하세요:")
    print('python -m pip install --upgrade pip')
    print('python -m pip install langchain langchain-community langchain-google-genai langchain-core chromadb python-dotenv')
    input("Press Enter to exit...")
    sys.exit(1)

# 환경변수(.env)에서 GOOGLE_API_KEY 불러오기
load_dotenv()

# ==========================================
# [설정]
# ==========================================
PDF_FILE_PATH = "my_medical_doc.pdf"  # 같은 폴더에 있는 PDF 파일 이름
CHROMA_DB_PATH = "./chroma_db"        # 저장소 폴더

def process_document():
    """PDF 읽어서 Gemini가 이해하는 숫자로 변환해 저장"""
    if not os.path.exists(PDF_FILE_PATH):
        print(f"❌ 오류: '{PDF_FILE_PATH}' 파일이 없습니다.")
        return None

    print("📄 문서 읽는 중... (잠시만 기다려주세요)")
    loader = PyPDFLoader(PDF_FILE_PATH)
    pages = loader.load()

    # 문서를 자르기
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(pages)
    
    # ⭐️ 중요: Gemini용 임베딩 모델 사용 (embedding-001)
    print("데이터를 벡터로 변환 중...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vector_db = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    print("✅ 문서 저장 완료!")
    return vector_db

def get_nurse_bot(vector_db):
    """Gemini 뇌를 장착한 간호사 만들기"""
    
    # [추론형 프롬프트] - 원하시던 그 로직 그대로!
    nurse_prompt_template = """
    당신은 결핵 환자를 상담하는 10년 차 베테랑 간호사입니다.
    아래 [참고 문서]를 바탕으로 환자의 [질문]에 대해 깊이 생각하고 답변하세요.

    [참고 문서]
    {context}

    [환자의 질문]
    {question}

    [답변 가이드라인]
    1. 환자의 질문에서 핵심 증상이나 상황을 파악하세요.
    2. 참고 문서에 해당 증상이 있는지 꼼꼼히 대조하세요.
    3. (추론) 문서에 있다면 그것이 약물 부작용인지, 일반적인 증상인지 판단하세요.
    4. 답변은 따뜻한 말투(~해요체)로 하되, 의학적 사실은 문서에 근거해서만 말하세요.
    5. 문서에 없는 내용이면 "제공된 정보에는 해당 내용이 없어서 정확한 답변이 어려워요."라고 솔직하게 말하세요.
    
    답변:
    """
    
    PROMPT = PromptTemplate(
        template=nurse_prompt_template, 
        input_variables=["context", "question"]
    )

    # ⭐️ 중요: Gemini 1.5 Flash 모델 사용 (빠르고 무료 티어 넉넉함)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        temperature=0
    )

    # 검색된 문서 3개만 참고(k=3)해서 답변 생성 (최신 방식)
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
    )
    
    return qa_chain

# ==========================================
# [실행]
# ==========================================
if __name__ == "__main__":
    # 임베딩 모델 설정 (불러올 때도 필요함)
    gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # DB 확인 및 로드
    if os.path.exists(CHROMA_DB_PATH):
        print("💾 기존 지식을 불러옵니다...")
        vector_db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=gemini_embeddings)
    else:
        vector_db = process_document()

    if vector_db:
        bot = get_nurse_bot(vector_db)
        print("\n👩‍⚕️ Gemini 간호사: 안녕하세요! 무엇이 궁금하신가요? (종료: exit)")
        
        while True:
            user_input = input("\n👤 환자: ")
            if user_input.lower() == "exit":
                break
            
            try:
                response = bot.invoke(user_input)
                print(f"👩‍⚕️ 간호사: {response.content}")
            except Exception as e:
                print(f"오류 발생: {e}")
        print("프로그램을 종료합니다.")
        input("Press Enter to exit...")