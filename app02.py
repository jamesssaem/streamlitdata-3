#
# 주식 데이터를 받아서 시각화 해주는 앱을 만들어 본다.
#

# 먼저 커맨드라인에서 다음과 같이 라이브러리 설치 필요.
# pip install finance-datareader
# pip install mplfinance
# pip install bs4
# pip install streamlit-lottie

# 캔들 차트 관련해서는 다음 사이트를 참고해 본다.
# https://github.com/matplotlib/mplfinance/

# 필요한 라이브러리를 불러온다.
import streamlit as st
import FinanceDataReader as fdr
import mplfinance as mpf
import json
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from streamlit_lottie import st_lottie
from datetime import datetime, timedelta

# 트레이딩 시그널을 제공하는 볼린저 밴드를 그려주는 함수.
def addBollingerBand(data, ax):
    # 추가적인 그래프 출력에 유리한 형태로 데이터프레임 변환.
    df = data.reset_index(drop=True)
    df['MA20'] = df['Close'].rolling(window=20).mean()  # 20일 이동평균.
    df['StDev'] = df['Close'].rolling(window=20).std()  # 20일 이동표준편차.
    df['Upper'] = df['MA20'] + (df['StDev'] * 2)        # 밴드의 상한.
    df['Lower'] = df['MA20'] - (df['StDev'] * 2)        # 밴드의 하한.
    df = df[19:]                                        # 시작일 20 이후만 가능. 
    ax.plot(df.index, df['Upper'], color = 'red', linestyle ='--', linewidth=1.5, label = 'Upper')       
    ax.plot(df.index, df['MA20'], color='aqua', linestyle = ':', linewidth = 2, label = 'MA20')
    ax.plot(df.index, df['Lower'], color='blue', linestyle= '--', linewidth=1.5, label = 'Lower')
    ax.fill_between(df.index, df['Upper'], df['Lower'], color='grey', alpha=0.3) 
    ax.legend(loc='best')

# JSON을 읽어 들이는 함수.
def loadJSON(path):
    f = open(path, 'r')
    res = json.load(f)
    f.close()
    return res

# 로고 Lotti와 타이틀 출력.
col1, col2 = st.columns([1,2])
with col1:
    lottie = loadJSON('lottie-stock-candle-loading.json')
    st_lottie(lottie, speed=1, loop=True, width=150, height=150)
with col2:
    ''
    ''
    st.title('트레이딩 시그널')

# 시장 데이터를 읽어오는 함수들을 정의한다.
@st.cache_data
def getData(code, datestart, dateend):
    df = fdr.DataReader(code,datestart, dateend ).drop(columns='Change')  # 불필요한 'Change' 컬럼은 버린다.
    return df

@st.cache_data
def getSymbols(market='KOSPI', sort='Marcap'):
    df = fdr.StockListing(market)
    ascending = False if sort == 'Marcap' else True
    df.sort_values(by=[sort], ascending= ascending, inplace=True)
    return df[ ['Code', 'Name', 'Market'] ]

# 세션 상태를 초기화 한다.
if 'ndays' not in st.session_state:
    st.session_state['ndays'] = 100                 #

if 'code_index' not in st.session_state:
    st.session_state['code_index'] = 0

if 'chart_style' not in st.session_state:
    st.session_state['chart_style'] = 'default'

if 'volume' not in st.session_state:
    st.session_state['volume'] = True

# 사이드바에서 폼을 통해서 차트 인자를 설정한다.
with st.sidebar.form(key="chartsetting", clear_on_submit=True):
    st.header('차트 설정')
    ''
    ''
    symbols = getSymbols()
    choices = zip( symbols.Code , symbols.Name , symbols.Market )
    choices = [ ' : '.join( x ) for x in choices ]  # Code, Name, Market을 한개의 문자열로.
    choice = st.selectbox( label='종목:', options = choices, index=st.session_state['code_index'] )
    code_index = choices.index(choice)
    code = choice.split()[0]                        # 실제 code 부분만 떼어 가져온다.
    ''
    ''
    ndays = st.slider(
        label='기간 (days):', 
        min_value= 50,                      # 기존의 5일 => 50일로 키움.
        max_value= 365, 
        value=st.session_state['ndays'],
        step = 1)
    ''
    ''
    chart_styles = ['default', 'binance', 'blueskies', 'brasil', 'charles', 'checkers', 'classic', 'yahoo','mike', 'nightclouds', 'sas', 'starsandstripes']
    chart_style = st.selectbox(label='차트 스타일:',options=chart_styles,index = chart_styles.index(st.session_state['chart_style']))
    ''
    ''
    volume = st.checkbox('거래량', value=st.session_state['volume'])
    ''
    ''
    if st.form_submit_button(label="OK"):
        st.session_state['ndays'] = ndays
        st.session_state['code_index'] = code_index
        st.session_state['chart_style'] = chart_style
        st.session_state['volume'] = volume
        st.experimental_rerun()

# 캔들 차트 + 지표를 출력해 주는 함수.
def plotChartV2(data):
    chart_style = st.session_state['chart_style']
    marketcolors = mpf.make_marketcolors(up='red', down='blue')
    mpf_style = mpf.make_mpf_style(base_mpf_style= chart_style, marketcolors=marketcolors)
    # 바탕이 되는 캔들차트.
    # 이동편균선은 더이상 그리지 않음.
    fig, ax = mpf.plot(
        data,
        volume=st.session_state['volume'],
        type='candle',
        style=mpf_style,
        figsize=(10,7),
        fontscale=1.1,
        returnfig=True                  # Figure 객체 반환.
    )
    addBollingerBand(data, ax[0])       # Bollinger Band를 axis에 추가.
    st.pyplot(fig)

# 데이터를 불러오고 최종적으로 차트를 출력해 준다.
# 주의: datetime.today()에는 항상 변하는 "시:분:초"가 들에있어서 cache가 작동하지 않는다.
#       "시:분:초"를 떼어 버리고 날짜만 남도록 date()를 호출하는 것이 중요하다!

date_start = (datetime.today()-timedelta(days=st.session_state['ndays'])).date()
df = getData(code, date_start, datetime.today().date())     
chart_title = choices[st.session_state['code_index'] ]
st.markdown(f'<h3 style="text-align: center; color: red;">{chart_title}</h3>', unsafe_allow_html=True)
plotChartV2(df)
