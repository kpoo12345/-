import gradio as gr
import pandas as pd
import re

def load_data(file_path):
    return pd.read_excel(file_path)

def extract_courses(data, start_label, column_index):
    temp = data[data.iloc[:, column_index] == start_label].index[0]
    course_index = data[data.iloc[:, column_index] == start_label].index.tolist()
    if len(course_index) > 0:
        course_index = [index for index in course_index if index > temp]
        if course_index:
            course_index = course_index[-1]
        else:
            course_index = len(data)
    else:
        course_index = len(data)
    data_subset = data.iloc[temp + 2: course_index]
    filtered_data = data_subset[data_subset.iloc[:, 4] != 'F']
    return filtered_data.iloc[:, column_index].astype(str).tolist()

def check_courses(student_courses, required_courses):
    UnGradu_Major = []
    for major in required_courses:
        if not any(str(major) in str(my_courses) for my_courses in student_courses):
            UnGradu_Major.append(major)
    return UnGradu_Major

def calculate_major_credits(majors_data):
    Majors_data = [item for item in majors_data if isinstance(item, str) and ('전(선)' in item or '전필' in item)]
    Majors_numbers = [int(re.search(r'\d+', item).group()) for item in Majors_data if re.search(r'\d+', item)]
    return sum(Majors_numbers)

def get_value(df, row, col, dtype=int):
    value = df.iloc[row, col]
    if pd.isna(value):
        return 0 if dtype == int else 0.0
    return dtype(value)

def check_graduation_areas(data):
    temp = data[data.iloc[:, 1] == '공필/일선/교필/교선/교직'].index[0]
    Culture_choice_index = data[data.iloc[:, 1] == '공필/일선/교필/교선/교직'].index.tolist()
    if len(Culture_choice_index) > 0:
        Culture_choice_index = [index for index in Culture_choice_index if index > temp]
        if Culture_choice_index:
            Culture_choice_index = Culture_choice_index[-1]
        else:
            Culture_choice_index = len(data)
    else:
        Culture_choice_index = len(data)

    data_subset = data.iloc[temp + 2: Culture_choice_index]
    filtered_data = data_subset[data_subset.iloc[:, 4] != 'F']
    My_Culture_choice = filtered_data.iloc[:, 1].tolist()
    if '공필/일선/교필/교선/교직' in My_Culture_choice:
        My_Culture_choice.remove('공필/일선/교필/교선/교직')

    Culture_choice = {}
    for item in My_Culture_choice:
        if isinstance(item, str):
            if '창의와통섭' in item or '소통및윤리적행동' in item or '글로컬시민' in item or '자기개발과지식탐구' in item or '교선' in item:
                name, value = item.rsplit(maxsplit=1)
                Culture_choice[name.strip()] = int(value)

    chang_greater_than_2 = Culture_choice.get('창의와통섭', 0) >= 2
    sootong_greater_than_2 = Culture_choice.get('소통및윤리적행동', 0) >= 2
    glo_greater_than_2 = Culture_choice.get('글로컬시민', 0) >= 2
    jagi_greater_than_2 = Culture_choice.get('자기개발과지식탐구', 0) >= 2
    Gu_greater_than_19 = Culture_choice.get('교선', 0) >= 19

    return {
        '창의와 통섭': chang_greater_than_2,
        '소통 및 윤리적 행동': sootong_greater_than_2,
        '글로컬 시민': glo_greater_than_2,
        '자기개발과 지식 탐구': jagi_greater_than_2,
        '교양선택': Gu_greater_than_19
    }

def process_excel(file):
    data = load_data(file.name)

    # 전공 과목 추출
    My_Majors = extract_courses(data, '전필/전공(이수필/선택이수)', 6)
    Majors = ['기독교사회복지론', '전공탐색과 진로설계Ⅰ']
    UnGradu_Major = check_courses(My_Majors, Majors)

    # 전공 학점 계산
    total_major_credits = calculate_major_credits(My_Majors)

    # 교양 과목 추출
    My_Culture = extract_courses(data, '공필/일선/교필/교선/교직', 1)
    Culture = ['구약의세계와인성', '신약의세계와섬김', '창의와비판적사고', '개혁주의신앙윤리', '토론·발표와글쓰기', '글쓰기Ⅰ', 'Global EnglishⅠ', 'Global EnglishⅡ', 'NCS직업기초능력']
    UnGradu_Culture = check_courses(My_Culture, Culture)

    # '토론·발표와글쓰기'와 '글쓰기Ⅰ' 조건 처리
    if '토론·발표와글쓰기' not in UnGradu_Culture:
        if '글쓰기Ⅰ' in UnGradu_Culture:
            UnGradu_Culture.remove('글쓰기Ⅰ')
    elif '글쓰기Ⅰ' not in UnGradu_Culture:
        if '토론·발표와글쓰기' in UnGradu_Culture:
            UnGradu_Culture.remove('토론·발표와글쓰기')

    # 공통 영역 과목 추출
    My_Gongtong = extract_courses(data, '공필/일선/교필/교선/교직', 1)
    Gongtong = ['실천I', '실천Ⅱ', '실천Ⅲ', '실천Ⅳ', '실천Ⅴ', '실천Ⅵ', '실천Ⅶ', '실천Ⅷ', '기독교인성과 섬김의리더I', '기독교인성과 섬김의리더Ⅱ']
    UnGradu_Gongtong = check_courses(My_Gongtong, Gongtong)

    # 창의와 통섭, 소통 및 윤리적 행동, 글로컬 시민, 자기개발과 지식 탐구 영역 학점 체크
    graduation_areas_check = check_graduation_areas(data)

    # 기본 영역 체크
    total_credits = get_value(data, 3, 5)
    total_credits_check = total_credits >= 130
    total_credits_diff = 130 - total_credits
    gpa = get_value(data, 3, 9, dtype=float)
    gpa_check = gpa >= 2.0

    # 결과 출력
    result = ""
    result += "----- 기본 영역을 만족하였는지 확인합니다. -----\n"
    if total_credits_check:
        result += "축하합니다. 총 학점이 130학점 이상입니다.\n"
    else:
        result += f"아쉽습니다. 총 학점을 130학점 이상 채우지 못하였습니다. {total_credits_diff} 학점 이상을 더 채우셔야 합니다.\n"

    if gpa_check:
        result += "축하합니다. 총 평점이 2.0 이상입니다.\n"
    else:
        result += "아쉽습니다. 총 평점이 2.0 이상이 아닙니다.\n"

    result += "\n----- 제 1전공 영역을 만족하였는지 확인합니다. -----\n"
    result += f"듣지 않은 전공 필수 과목 : {UnGradu_Major}\n"
    if not UnGradu_Major:
        result += "축하합니다. 전공필수 과목을 모두 이수하셨습니다.\n"
    else:
        result += "아쉽습니다. 위 항목의 전공필수 과목을 더 이수하셔야 합니다.\n"

    if total_major_credits >= 36:
        result += "축하합니다. 전공 학점이 36 이상입니다.\n"
    else:
        result += f"아쉽습니다. 전공 학점을 36학점 이상 채우지 못하였습니다. {36 - total_major_credits} 학점 이상을 더 채우셔야 합니다.\n"

    result += "\n----- 교양 영역을 만족하였는지 확인합니다. -----\n"
    result += f"듣지 않은 교양필수 과목 : {UnGradu_Culture}\n"
    if not UnGradu_Culture:
        result += "축하합니다. 교양필수 과목을 모두 이수하셨습니다.\n"
    else:
        result += "아쉽습니다. 위 항목의 교양필수 과목을 더 이수하셔야 합니다.\n"

    for area, satisfied in graduation_areas_check.items():
        if area == '교양선택':
            result += f"{area} 영역(19학점 이상)을 만족하였는가? {satisfied}\n"
        else:
            result += f"{area} 영역(2학점 이상)을 만족하였는가? {satisfied}\n"

    result += "\n----- 공통 영역을 만족하였는지 확인합니다. -----\n"
    result += f"채워야 하는 공통 영역: {UnGradu_Gongtong}\n"
    if not UnGradu_Gongtong:
        result += "축하합니다. 공통 영역 과목을 모두 이수하셨습니다.\n"
    else:
        result += "아쉽습니다. 위 항목의 공통 영역 과목을 더 이수하셔야 합니다.\n"

    return result

iface = gr.Interface(
    fn=process_excel,
    inputs=gr.File(label="성적표(엑셀) 파일을 업로드하세요."),
    outputs="text",
    title="총신대 사회복지학과 졸업 요건 확인(17~24학번)",
    description="파일을 업로드하여 졸업 요건을 확인하세요."
)

iface.launch(share=True)