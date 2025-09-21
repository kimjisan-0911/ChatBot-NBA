from turtle import title
from flask import Flask, request, render_template, redirect, jsonify, send_from_directory, url_for
from nba_api.stats.endpoints import leaguedashplayerstats
from nba_api.stats.static import players
import pandas as pd
import requests
import json
import service.player_rank as player_rank
import service.search as search
import service.team_name as team_name
import service.teamrank as teamrank
from const.team_constant import TEAM_NAME
import service.players as players
import feedparser
import time
import threading
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("name.html")


all_players =  players.get_all_players()


@app.route("/player_list", methods=['GET', 'POST'])
def player_list():
    MAX_PAGE = 99  # 상수 선언은 함수 최상단으로

    # 기본 페이지 번호, GET/POST 상관없이 사용하기 위해 여기서 처리
    page = request.args.get('page', '1')
    try:
        current_page = int(page)
    except ValueError:
        current_page = 1

    if request.method == 'POST':
        user_input = request.form.get('keyword', '').strip()
        if user_input:
            info = players.get_players_by_name(user_input)
            # 검색 결과가 1명이라면 info는 dict, 여러명이라면 리스트 가정
            if isinstance(info, dict):
                return render_template("player_list.html", info=info, current_page=1, max_page=1)
            elif isinstance(info, list):
                # 여러명 검색 결과가 있다면 페이지네이션 없이 한 페이지에 다 보여주는 예시
                return render_template("player_list.html", player_lst=info, current_page=1, max_page=1)
            else:
                # 검색 결과 없을 때
                return render_template("player_list.html", player_lst=[], current_page=1, max_page=1)
        else:
            # 빈 검색어 처리 (전체 선수 목록 보여주기 등)
            pass  # 아래 GET 처리와 동일하게 처리하겠습니다

    # GET 요청 처리 및 POST에서 빈 검색어 넘어왔을 때도 여기서 처리
    player_lst = players.get_all_players(current_page)
    # players.get_all_players()가 페이지 단위로 선수 리스트 반환한다고 가정

    return render_template("player_list.html",
                           player_lst=player_lst,
                           current_page=current_page,
                           max_page=MAX_PAGE)



#팀 검색
@app.route("/team", methods=["POST"])
def search_team():
    json_data = request.get_json(force=True)
    print(json_data)
    user_request = json_data['userRequest']
    utterance = user_request['utterance']
    print(utterance)
    lst = utterance.split()
    name = lst[-1]
    print(name)
    teamname = team_name.get_team_info(name)
    info = teamname[0]
    print(info)
    imageUrl = teamname[1]
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": info['fullName'],
                        "description": (
                            f"약어: {info['abb']}\n"
                            f"도시: {info['city']} / 닉네임: {info['nickname']}\n"
                         ),
                        "thumbnail": {
                            "imageUrl": imageUrl
                        },
                        "buttons": [
                            {
                                "label": "NBA 프로필 보기",
                                "action": "webLink"
                            }
                        ]
                    }
                }
            ]
        }
        }
    return jsonify(response)

#선수 검색
@app.route("/player", methods=["POST"])
def search_player():
    try:
        json_data = request.get_json(force=True)
        print(json_data)
        user_request = json_data['userRequest']
        utterance = user_request['utterance']
        print(utterance)
        lst = utterance.split()
        name = lst[-1]
        print(name)
        full_name = search.get_full_name(name)
        a = search.name_to_info(full_name)
        info = a[1]
        imageUrl = a[2]
        response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": info[0] + " " + info[1],  # 성 + 이름
                        "description": (
                            f"생년월일: {info[2]}\n"
                            f"키: {info[3]} / 몸무게: {info[4]}\n"
                            f"등번호: {info[5]} | 포지션: {info[6]}\n"
                            f"팀: {info[7]}"
                         ),
                        "thumbnail": {
                            "imageUrl": imageUrl
                        },
                        "buttons": [
                            {
                                "label": "NBA 프로필 보기",
                                "action": "webLink"
                            }
                        ]
                    }
                }
            ]
        }
        }
        return jsonify(response)
    except Exception as e:
        print("exception")
        json_data = {}
    return jsonify({})

# 선수 랭킹
@app.route('/rank', methods=["POST","GET"])
def real_rank():
    ranking = player_rank.get_season_player_rankings("2024-25", top_n=10, stat="PTS")
    print(ranking)

    items = []
    for player in ranking:
        item = {
            "title": player["선수 이름"],
            "description": (
                f"팀: {player['팀']}\n"
                f"경기수: {player['경기수']}\n"
                f"PTS: {player['PTS']}"
            ),
            "imageUrl": player["image_url"],  # 여기서 바로 사용
            "link": {
                "web": "https://www.nba.com/players"  # 필요시 개별 링크로 확장 가능
            }
        }
        items.append(item)

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "listCard": {
                        "header": {
                            "title": f"PTS Top {len(ranking)} 선수 랭킹"
                        },
                        "items": items
                    }
                }
            ]
        }
    }
    return jsonify(response)

# 팀 랭킹
@app.route('/team_rank', methods=["POST","GET"])
def search_rank():
    t_ranking = teamrank.get_season_team_rankings(2024-25, top_n=10)
    items = [] 
    for team in t_ranking:
        image_url = teamrank.get_team_logo(team["팀 이름"])
        item = {
            "title": team["팀 이름"],
            "description": (
                f"승: {team['승']}\n"
                f"패: {team['패']}\n"
                f"승률: {team['승률']}"
            ),
            "imageUrl": image_url,  # 여기서 바로 사용
            "link": {
                "web": "https://www.nba.com/teams"  # 필요시 개별 링크로 확장 가능
            }
        }
        items.append(item)

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "listCard": {
                        "header": {
                            "title": f"Top {len(t_ranking)} 팀 랭킹"
                        },
                        "items": items
                    }
                }
            ]
        }
    }

    return jsonify(response)

NEWS_API_KEY = 'd5ef6f58589b459ead2200a67f4cd344'
# NBA 뉴스(사이트ver)
@app.route('/get_nba_news')
def get_nba_news():
    try:
        resp = requests.get('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/news')
        resp.raise_for_status()
        data = resp.json()

        # 뉴스 항목 추출 (예: headlines)
        articles = data.get('articles', []) or data.get('headlines', [])
        result = []
        for item in articles:
            result.append({
                "title": item.get("headline") or item.get("title"),
                "summary": item.get("description") or "",
                "url": item.get("links", {}).get("web", {}).get("href") or item.get("links", {}).get("mobile", {}).get("href")
            })
        return jsonify(result)

    except Exception as e:
        print("ESPN 뉴스 API 오류:", e)
        return jsonify([]), 500

def get_basketball_news():
    try:
        rss_url = "https://news.google.com/rss/search?q=NBA&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            return None

        top_news = feed.entries[0]  # 가장 최신 뉴스
        return {
            "title": top_news.title,
            "link": top_news.link,
            "image": top_news.media_thumbnail[0]['url'] if 'media_thumbnail' in top_news else None
        }
    except Exception as e:
        print(f"Error fetching NBA news: {e}")
        return None
# NBA 뉴스(카카오ver)
@app.route("/news", methods=["POST"])
def news():
    try:
        user_request = request.get_json()
        utterance = user_request['userRequest']['utterance'].strip()

        if "뉴스" in utterance:  # "뉴스"라는 단어가 포함된 경우에만 뉴스 제공
            news = get_basketball_news()


            if news:
                response = {
                    "version": "2.0",
                    "template": {
                        "outputs": [
                            {
                                "listCard": {
                                    "header": {
                                        "title": news["title"]
                                    },
                                    "items": [
                                        {
                                            "title": news["title"],
                                            "imageUrl": news["image"] if news["image"] else "",  # Image URL
                                            "link": {
                                                "web": news["link"]
                                            }
                                        }
                                    ],
                                    "buttons": [
                                        {
                                            "action": "webLink",
                                            "label": "본문 보기",
                                            "webLinkUrl": news["link"]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }

                return jsonify(response)
            else:
                return jsonify({
                    "version": "2.0",
                    "template": {
                        "outputs": [
                            {
                                "simpleText": {
                                    "text": "NBA 뉴스를 찾을 수 없습니다."
                                }
                            }
                        ]
                    }
                })
        else:
            return jsonify({
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleText": {
                                "text": "NBA 뉴스와 관련된 요청이 없습니다."
                            }
                        }
                    ]
                }
            })

    except Exception as e:
        print(f"Error handling request: {e}")
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "요청을 처리하는 중 오류가 발생했습니다."
                        }
                    }
                ]
            }
        })
    

community_posts = []

@app.route('/community')
def community():
    return render_template('community.html', posts=community_posts)

@app.route('/community/write', methods=['GET', 'POST'])
def write_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post = {
            "title": title,
            "content": content
        }
        community_posts.append(post)
        return redirect(url_for('community'))
    return render_template('write_post.html')






@app.route('/play', methods = ['GET'])
def what():
    return render_template("player.html")

@app.route('/find_info', methods = ['GET', 'POST'])
def find_info():
    if request.method == 'GET':
        return render_template('player.html')
    elif request.method == 'POST':
        name = request.form['name'] #받은 form데이터에서 name이 name인 녀석을 가져온다.
        print(name)
        headers, rowSet, imageUrl = search.name_to_info(name=name)
        return render_template('player.html', headers = headers, rowSet = rowSet, imageUrl = imageUrl) #응답

@app.route('/login', methods = ['GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')


@app.route('/abc', methods=['GET', 'POST'])
def welcome():

    try:
        json_data = request.get_json(force=True)
        print(json_data)
    except Exception as e:
        json_data = {}

    # 'utterance'만 뽑아서 출력
    utterance = None
    if json_data:
        
        utterance = json_data.get('userRequest', {}).get('utterance')

    playername, teams = utterance[5:]
    print(playername, teams)
    fullname = search.get_full_name(playername, teams)
    print(fullname)
    temp, info, image_url, player_id = search.name_to_info(fullname)
    print(info)
        
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "basicCard": {
                        "title": info[0] + " " + info[1],  # 성 + 이름
                        "description": (
                            f"생년월일: {info[2]}\n"
                            f"키: {info[3]} / 몸무게: {info[4]}\n"
                            f"등번호: {info[5]} | 포지션: {info[6]}\n"
                            f"팀: {info[7]}"
                        ),
                        "thumbnail": {
                            "imageUrl": image_url
                        },
                        "buttons": [
                            {
                                "label": "NBA 프로필 보기",
                                "action": "webLink",
                                "webLinkUrl": f"https://www.nba.com/player/{player_id}"
                            }
                        ]
                    }
                }
            ]
        }
    }


    return jsonify(response)


def get_season_scoring_leaders(season: str, top_n: int = 10):
    """
    주어진 시즌의 득점 상위 선수들을 반환하는 함수입니다.
    """
    try:
        stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season)
        df = stats.get_data_frames()[0]

        top_scorers = df.sort_values(by='PTS', ascending=False).head(top_n)
        result = top_scorers[["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "PTS", "PLAYER_POSITION"]]
        result = result.reset_index(drop=True)
        return result

    except Exception as e:
        return pd.DataFrame() 
    
@app.route("/callback")
def callback():
    code = request.args.get('code') #주소창에 있는 code의 값을 뽑아내기
    url = "https://kauth.kakao.com/oauth/token"

    headers={
        "Content-Type":"application/x-www-form-urlencoded;charset=utf-8"
    }
    body={
        "grant_type":"authorization_code",
        "client_id":"4727b876fbf37e21bd488df5bc9f62d9",
        "redirect_uri":"http://127.0.0.1:5000/callback",
        "code": code,
        "client_secret":"aQAUnGe0e6P0uPrT06otJN4YwBcZCts5"

    }
    try:
        response = requests.post(url=url,data=body,headers=headers)
        response = response.json()
        access_token = response['access_token']
        print(access_token)
    except Exception as e:
        print("some issues..")
        print(e)
    try:
        bearer_token = "Bearer "+ access_token
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": bearer_token,
            "Content-Type":"application/x-www-form-urlencoded;charset=utf-8"
        }
        response = requests.get(url=url, headers=headers)
        print(response.status_code)
        print(response.text)
    except Exception as e:
        print("some issues..")
        print(e)
    response = response.json()
    nickname = response['kakao_account']['profile']['nickname']
    print(nickname)

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    bearer_token = "Bearer "+ access_token
    headers = {
        "Authorization": bearer_token,
        "Content-Type":"application/x-www-form-urlencoded;charset=utf-8"
    }
    #사용자가 관심 팀을 저장하면 팀의 소식을 보내주는..~

    template_object={
    "object_type": "feed",
    "content": {
        "title": "NBA 프로농구 봇",
        "description": "NBA 마지막 결승전 시작!",
        "image_url": "https://dimg.donga.com/wps/NEWS/IMAGE/2021/09/22/109353831.1.jpg",
        "image_width": 640,
        "image_height": 640,
        "link": {
        "web_url": "http://www.daum.net",
        "mobile_web_url": "http://m.daum.net",
        "android_execution_params": "contentId=100",
        "ios_execution_params": "contentId=100"
        }
    },
    "item_content": {
        "profile_text": "NBA",
        "profile_image_url": "https://w7.pngwing.com/pngs/384/886/png-transparent-nba-logo.png",
        "title_image_url": "https://w-s-c.co.kr/web/product/big/202310/a5b3015c0a902e4f4d179d3d5a821b7e.jpg",
        "title_image_text": "르브론 제임스",
        "title_image_category": "농구선수",
    },
    "social": {
        "like_count": 9999,
        "comment_count": 1483,
        "shared_count": 1879,
        "view_count": 12140,
        "subscriber_count": 1214005
    },
    "buttons": [
        {
        "title": "웹으로 이동",
        "link": {
            "web_url": "http://www.daum.net",
            "mobile_web_url": "http://m.daum.net"
        }
        },
        {
        "title": "앱으로 이동",
        "link": {
            "android_execution_params": "contentId=100",
            "ios_execution_params": "contentId=100"
        }
        }
    ]
    }

    template_string = json.dumps(template_object, ensure_ascii=False)
    template_string = "template_object="+template_string
    response = requests.post(url=url, headers=headers, data=template_string)
    print(response.status_code)
    print(response.text)
    
    return render_template("name.html")

latest_news = {}

def update_news():
    """하루마다 실행할 뉴스 업데이트 함수"""
    global latest_news
    try:
        rss_url = "https://news.google.com/rss/search?q=NBA&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        if feed.entries:
            top_news = feed.entries[0]
            latest_news = {
                "title": top_news.title,
                "link": top_news.link,
                "image": top_news.media_thumbnail[0]['url'] if 'media_thumbnail' in top_news else None
            }
            print("[뉴스 업데이트 완료] ", latest_news["title"])
        else:
            print("[뉴스 업데이트 실패] 뉴스 항목이 없습니다.")
    except Exception as e:
        print("[뉴스 업데이트 오류]", e)

def periodic_task():
    while True:
        update_news()
        time.sleep(86400)  # 86400초 = 24시간

def start_periodic_task():
    thread = threading.Thread(target=periodic_task)
    thread.daemon = True
    thread.start()

@app.route("/news_latest")
def news_latest():
    """저장된 최신 뉴스 반환"""
    if latest_news:
        return jsonify(latest_news)
    else:
        return jsonify({"message": "뉴스가 아직 업데이트되지 않았습니다."})

if __name__ == "__main__":
    start_periodic_task()

    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'), debug=False)


#병신
#지랄