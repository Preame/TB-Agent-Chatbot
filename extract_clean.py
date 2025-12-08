import pandas as pd
from langchain_community.document_loaders import PyPDFLoader

# 1. 분석할 파일 3개 다 넣기
files = [
    "guidelines_for_integrated_management_for_tb.pdf",
    "national_Tuberculosis_control_guidelines.pdf",
    "korean_guidlines_for_tb.pdf.pdf"
]

# 2. 찾을 키워드 설정 (그물망)
# 약물 이름
drugs = ["이소니아지드", "리팜핀", "에탐부톨", "피라진아미드", "스트렙토마이신"]

# 부작용 관련 단어들 (이게 포함된 문장만 가져옴)
keywords = [
    "부작용", "독성", "이상반응", "위장장애", "간염", 
    "구역", "구토", "복통", "설사", "발진", "가려움", 
    "관절통", "시력", "청력", "저림", "쇼크"
]

def mine_sentences(file_list):
    all_results = []

    for file_path in file_list:
        print(f"\n📂 '{file_path}' 채굴 시작...")
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()
        except:
            print(f"❌ 파일을 못 찾았어요: {file_path}")
            continue
            
        count = 0
        for i, page in enumerate(pages):
            text = page.page_content
            # 문장 단위로 자르기 (점. 기준으로 나눔)
            sentences = text.split('.')
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10: continue # 너무 짧은 건 패스
                
                # 조건: 약물 이름이 있고 AND 부작용 키워드도 있어야 함
                has_drug = any(drug in sentence for drug in drugs)
                has_keyword = any(key in sentence for key in keywords)
                
                if has_drug and has_keyword:
                    # 어떤 약물에 대한 얘기인지 찾기
                    found_drugs = [d for d in drugs if d in sentence]
                    
                    all_results.append({
                        "파일": file_path,
                        "페이지": i + 1,
                        "관련약물": ", ".join(found_drugs),
                        "추출문장": sentence
                    })
                    count += 1
        
        print(f"👉 {count}개의 문장을 찾았습니다!")

    return all_results

# 실행
data = mine_sentences(files)

if data:
    df = pd.DataFrame(data)
    # 엑셀로 저장
    df.to_excel("mined_side_effects.xlsx", index=False)
    print("\n🎉 채굴 끝! 'mined_side_effects.xlsx' 파일을 열어보세요. (데이터가 많을 거예요!)")
else:
    print("\n⚠️ 아무것도 못 찾았어요. 키워드를 확인해보세요.")