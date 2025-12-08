import os
from langchain_community.document_loaders import PyPDFLoader

# 분석할 파일 목록
files = [
    "guidelines_for_integrated_management_for_tb.pdf",
    "national_Tuberculosis_control_guidelines.pdf",
    "korean_guidlines_for_tb.pdf.pdf"
]

# 찾고 싶은 핵심 키워드 (결핵 1차 약제 이름들)
target_drugs = ["이소니아지드", "리팜핀", "에탐부톨", "피라진아미드"]

def spy_on_pdf(file_path):
    print(f"\n===== 🕵️ 정찰 시작: {file_path} =====")
    if not os.path.exists(file_path):
        print("❌ 파일이 없어요!")
        return

    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    found_count = 0
    for i, page in enumerate(pages):
        text = page.page_content
        # '부작용'이라는 단어가 있고, 약물 이름 중 하나라도 포함된 페이지 찾기
        if "부작용" in text and any(drug in text for drug in target_drugs):
            print(f"\n[페이지 {i+1} 발견!] ------------------------")
            # 앞뒤 문맥 좀 잘라서 보여주기 (너무 길면 보기 힘드니까)
            lines = text.split('\n')
            for line in lines:
                if any(drug in line for drug in target_drugs):
                    print(f"👉 {line.strip()[:100]}...") # 100글자만 미리보기
            found_count += 1
            if found_count >= 3: # 파일당 3페이지만 보고 빠지기 (너무 많이 나오면 피곤함)
                break

for file in files:
    spy_on_pdf(file)