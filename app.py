from flask import Flask, render_template, request, session, redirect
from flask_paginate import Pagination, get_page_args
from flask_session import Session
from datetime import datetime
import pandas as pd
import os
from sqlalchemy import create_engine
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(24)
Session(app)

engine = create_engine('mysql+mysqldb://ict1:ict1@192.168.0.46:3306/ict1', encoding='utf-8') # table 명 : mlv2_20220929

filter_list = ['범위_전체','범위_수요기업','범위_공급기업','정렬_정확도순','정렬_최신순','정렬_마감기간순','지역_전체','지역_서울','지역_부산', '지역_인천', '지역_대구',
    '지역_대전','지역_광주','지역_울산','지역_세종', '지역_경기', '지역_강원','지역_충북','지역_충남','지역_전북','지역_전남', '지역_경북', '지역_경남','지역_제주',
    '지원분야_전체','지원분야_금융','지원분야_기술','지원분야_인력','지원분야_수출','지원분야_내수','지원분야_창업','지원분야_경영','지원분야_기타','접수현황_전체',
    '접수현황_접수대기','접수현황_접수중','접수현황_접수마감']
base_query_dict = {
    '정렬' : 'None',
    '범위' : 'None',
    '지역' : 'None',
    '지원분야' : 'None',
    '접수현황': 'None',
    '기간' : 'None'
    }

# 키워드 분기
def keyword_process(keyword):
    # 1) 해시태그 중 하나가 키워드로 들어온 경우
    if keyword == "_4차산업":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_keyword = '4차산업';"
    elif keyword == "_친환경":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_keyword = '친환경';"
    elif keyword == "_bio_health":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_keyword = 'bio&health';"
    elif keyword == "_중소기업":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_keyword = '중소기업';"
    elif keyword == "_연구개발":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '연구개발';"
    elif keyword == "_사회적기업":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '사회적기업';"
    elif keyword == "_자금지원":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '자금지원';"
    elif keyword == "_박람회":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '박람회';"
    elif keyword == "_해외수출":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '해외수출';"
    elif keyword == "_창업":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '창업';"
    elif keyword == "_일자리":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '일자리';"
    elif keyword == "_소상공인":
        query = "select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM searching_20220929 where cluster_kmeans = '소상공인';"                      
    # 2) 사용자가 입력한 검색어가 키워드인 경우     
    else:
        keyword_list = keyword.split()
        query = query_main(keyword, keyword_list)
    return query

#메인쿼리 작성하는 함수
def query_main(keyword, keyword_list):
    if len(keyword_list) == 0:
        query_main = f"select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자 FROM mlv2_20220929 ORDER BY 등록일자 Desc;"
    else:
        score_query = ""
        cond_query = ""
        for i in keyword_list:
            score_query += f"(공고명 like '%%{i}%%')  + "
            score_query += f"(관리기관 like '%%{i}%%')+ "
            score_query += f"(attm_text like '%%{i}%%')*0.5 +"
            cond_query += f"(공고명 like '%%{i}%%') OR"

        score_query = score_query[:-2] + "AS Score"
        cond_query = cond_query[:-3]
        query_main = f"select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL, 등록일자, {score_query} FROM mlv2_20220929 \
                    WHERE {cond_query}  \
                    ORDER BY case when 공고명 = '{keyword}' then 1 else 2 end , Score Desc, 등록일자 Desc;"
    return query_main

# 페이징 함수
def paginate(query_result):
    page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp")
    result = query_result[offset:(offset + per_page)]
    total = len(query_result)
    pagination = Pagination(
        p=page,
        pp=per_page,
        total=total,
        record_name="검색결과",
        format_total=True,
        format_number=True,
        page_parameter="p",
        per_page_parameter="pp",
    )
    return (result, total, pagination)

# 필터 딕셔너리 업데이트
def sf_dict_update(sf_dict,raw_lst):
    key = raw_lst[0]
    value = raw_lst[1]
    if value =='전체':
        value = 'None'
    lst = {key:value}
    sf_dict.update(lst)
    return sf_dict

# 딕셔너리를 쿼리로 바꿔주는 함수
def sort_filter(sf_dict,df):
    local_list = {
        '서울':'서울특별시',
        '부산':'부산광역시',
        '인천':'인천광역시',
        '대구':'대구광역시',
        '대전':'대전광역시',
        '광주':'광주광역시',
        '울산':'울산광역시',
        '세종':'세종특별자치시',
        '경기':'경기도',
        '강원':'강원도',
        '충북':'충청북도',
        '충남':'충청남도',
        '전북':'전라북도',
        '전남':'전라남도',
        '경북':'경상북도',
        '경남':'경상남도',
        '제주':'제주특별자치도'
    }
    for key, value in sf_dict.items():
        if value == 'None':
            pass
        else:
            if key == '정렬':
                if value == '최신순':
                    df = df.sort_values(by='등록일자', ascending=False)
                else:
                    df = df.sort_values(by='신청종료일자', ascending=False)
            elif key == '범위':
                if value == '공급기업':
                    df = df[df['공고명'].str.contains('공급기업|공급기관|공급 기업|공급 기관')]
                else:
                    df = df[df['공고명'].str.contains('수요기업|수요기관|수요 기업|수요 기관|수혜기업|수혜기관|수혜 기업|수혜 기관|수진기업|수진기관|수진 기업|수진 기관')]
            elif key == '지역':
                df = df[(df['관리기관']==local_list[value]) | (df['공고명'].str.contains(f'^\W{value}'))|(df['관리기관'].str.contains(value)) |(df['공고명'].str.contains(value))]

            elif key == '지원분야':
                df = df[df['지원분야']==value]
            elif key == '접수현황':
                if value == '접수대기':
                    df = df.loc[(df["신청시작일자"] > datetime.now().date())]
                elif value == '접수중':
                    df = df.loc[(df["신청시작일자"] <= datetime.now().date()) & (df["신청종료일자"] >= datetime.now().date())]
                else:
                    df = df.loc[(df["신청종료일자"] < datetime.now().date())]
            else:
                date1 = value.split(' ~ ')[0]
                date2 = value.split(' ~ ')[1]
                df = df[(df['신청종료일자'].between(pd.to_datetime(date1), pd.to_datetime(date2)))]
    return df
    

@app.route('/')
def index():
    session.clear()
    return render_template("index.html")


@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST': # 1. POST의 경우 - 필터 & 정렬 setting만 조정함
        if 'base_df' in session: # 1.1) 세션 존재시
            print(session['current_df'])
            # filters
            query_dict = session['query_dict']
            # date-range related filter
            filter_query = request.form['filter']
            if filter_query not in filter_list:
                filter_query = 'date_' + filter_query
            query_key = filter_query.split('_')[0]
            query_value = filter_query.split('_')[1]
            raw_lst = [query_key, query_value]
            print(raw_lst)

            session['query_dict'] = sf_dict_update(query_dict, raw_lst)
            session['current_df'] = sort_filter(session['query_dict'], session['base_df'])

            return redirect("/search?keyword=" + session["keyword"] + "&p=1")

        else: # 1.2) 세션 안 존재시
            return render_template('search.html')
    else: # 2. GET 의 경우
        # keyword라는 key를 우선적으로 session에 넣습니다
        if "keyword" not in session:
            session["keyword"] = ""
        if session["keyword"] == request.values['keyword']:
            # current df 없는경우 (e.g. 초기화면에서 키워드 없이 검색만 누르는 경우 처리)
            if 'current_df' not in session:
                with engine.connect() as conn:
                    query = f"select 관리기관, 지원분야, 공고명, 신청시작일자, 신청종료일자, 공고상세URL,등록일자 FROM mlv2_20220929 ORDER BY 등록일자 Desc;"
                    cursor = conn.execute(query)
                    query_result = cursor.fetchall()
                    result, total, pagination = paginate(query_result)
                    session['base_df'] = pd.DataFrame(query_result)
                    session['current_df'] = pd.DataFrame(query_result)
                    session['query_dict'] = base_query_dict
                    session['keyword'] = ''
            else:
                df = session['current_df'].itertuples(index=False, name=None)
                result, total, pagination = paginate(list(df))
            return render_template("db_result.html", result=result, pagination=pagination, total=total, keyword=session['keyword'], query_dict=session['query_dict'])
        # 초기 검색 시
        else:
            session.clear()
            with engine.connect() as conn:
                keyword = request.values['keyword']
                query = keyword_process(keyword)
                cursor = conn.execute(query)
                query_result = cursor.fetchall()
                result, total, pagination = paginate(query_result)
                session['base_df'] = pd.DataFrame(query_result)
                session['current_df'] = pd.DataFrame(query_result)
                session['query_dict'] = base_query_dict
                session['keyword'] = keyword
            return render_template("db_result.html", result=result, pagination=pagination, total=total, keyword=session['keyword'], query_dict=session['query_dict'])


if __name__ == '__main__':
    app.run(debug=True)


