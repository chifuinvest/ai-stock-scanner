# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time, random
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="AI+硬科技选股系统", page_icon="🤖", layout="wide")

# ── 股票池 ────────────────────────────────────────────────
FULL_STOCKS = {
    '688256.SS': '寒武纪', '688041.SS': '海光信息', '603019.SS': '中科曙光',
    '000977.SZ': '浪潮信息', '300308.SZ': '中际旭创', '300394.SZ': '天孚通信',
    '300502.SZ': '新易盛', '688498.SS': '源杰科技', '300661.SZ': '圣邦股份',
    '603501.SS': '韦尔股份', '300782.SZ': '卓施微', '688008.SS': '澜起科技',
    '603986.SS': '兆易创新', '300223.SZ': '北京君正', '688521.SS': '芯原股份',
    '688052.SS': '纳芯微', '300672.SZ': '国科微', '002371.SZ': '北方华创',
    '688012.SS': '中微公司', '688072.SS': '拓荆科技', '688037.SS': '芯源微',
    '688120.SS': '华海清科', '300604.SZ': '长川科技', '688200.SS': '华峰测控',
    '300124.SZ': '汇川技术', '002747.SZ': '埃斯顿', '300024.SZ': '机器人',
    '688017.SS': '绿的谐波', '002472.SZ': '双环传动', '002920.SZ': '德赛西威',
    '300496.SZ': '中科创达', '002230.SZ': '科大讯飞', '688111.SS': '金山办公',
    '300624.SZ': '万兴科技', '002475.SZ': '立讯精密', '601138.SS': '工业富联',
    '002241.SZ': '歌尔股份', '600745.SS': '闻泰科技',
}

custom_stocks = {}

# ── 核心函数 ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_kline(code):
    try:
        df = yf.Ticker(code).history(
            start=(datetime.now()-timedelta(days=440)).strftime('%Y-%m-%d'),
            end=datetime.now().strftime('%Y-%m-%d'), auto_adjust=True)
        if df is None or len(df) < 260:
            return None
        df = df.rename(columns={'Close':'close','Open':'open','High':'high','Low':'low','Volume':'volume'})
        df.index = pd.to_datetime(df.index)
        return df
    except:
        return None

def calc_rsi(c, n=14):
    d = c.diff(); g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    rs = g/l; return (100-100/(1+rs)).iloc[-1]

def calc_macd_hist(c):
    e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean()
    dif=e12-e26; dea=dif.ewm(span=9,adjust=False).mean()
    return (dif-dea).iloc[-1]

def score_stock(df):
    c,v = df['close'],df['volume']
    rsi=calc_rsi(c)
    if pd.isna(rsi): sr=0
    elif 40<=rsi<=76: sr=2
    elif 33<=rsi<49: sr=1
    elif rsi>119 or rsi<14: sr=-2
    elif rsi>107: sr=-1
    else: sr=0
    mh=calc_macd_hist(c)
    if pd.isna(mh): sm=0
    elif mh>1.2: sm=2
    elif mh>0.3: sm=1
    elif mh<-1: sm=-1
    else: sm=0
    ma5=c.rolling(5).mean().iloc[-1]; ma20=c.rolling(20).mean().iloc[-1]
    ma60=c.rolling(60).mean().iloc[-1]; cur=c.iloc[-1]
    if pd.notna(ma60):
        if pd.notna(c.rolling(5).mean().iloc[-1]) and ma5>ma20>ma60 and cur>ma5: sma=3
        elif ma20>ma60: sma=2
        elif cur>ma20: sma=1
        elif cur<ma60: sma=-2
        else: sma=0
    else: sma=0
    if len(v)>27: vr=v.tail(5).mean()/v.tail(27).head(22).mean()
    else: vr=1
    sv=1 if 1.2<=vr<=2.0 else (-1 if vr>2.5 else 0)
    chg5=((c.iloc[-1]-c.iloc[-6])/c.iloc[-6])*100 if len(c)>6 else 0
    chgH=((c.iloc[-1]-c.iloc[-163])/c.iloc[-163])*100 if len(c)>168 else 0
    schg=(1 if 5<=chg5<=19 else -1 if chg5>41 else 0)+(1 if 20<=chgH<=114 else -1 if chgH>330 else 0)
    total=sr+sm+sma+sv+schg
    return total,sr,sm,sma,sv,schg,rsi

def get_signal(t):
    if t>=8: return '🔥🔥 强烈买入'
    elif t>=6: return '🔥 建议买入'
    elif t>=4: return '✅ 持有'
    elif t>=2: return '👀 观望'
    elif t>=0: return '🟢 小仓'
    elif t>=-2: return '⏳ 等待'
    else: return '🔵 回避'

def fmt_pct(v):
    if v>0: return f'+{v:.2f}%'
    elif v<0: return f'{v:.2f}%'
    return '0.00%'

def scan_stocks(stock_list):
    rows=[]
    for it in stock_list:
        code,name = (it['code'],it['name']) if isinstance(it,dict) else (it,FULL_STOCKS.get(it,it))
        df=get_kline(code)
        if df is None or len(df)<260:
            rows.append({'代码':code.split('.')[0],'名称':name,'最新价':'-','总分':'-',
                         '信号':'❌ 无数据','RSI':'-','24h':'-','7日':'-','30日':'-','12月':'-'})
            continue
        total,*_,rsi=score_stock(df)
        p=df['close'].iloc[-1]
        chg1=((p-df['close'].iloc[-2])/df['close'].iloc[-2])*100 if len(df)>1 else 0
        chg7=((p-df['close'].iloc[-6])/df['close'].iloc[-6])*100 if len(df)>5 else 0
        chg30=((p-df['close'].iloc[-22])/df['close'].iloc[-22])*100 if len(df)>21 else 0
        chg12=((p-df['close'].iloc[-252])/df['close'].iloc[-252])*100 if len(df)>250 else 0
        rows.append({'代码':code.split('.')[0],'名称':name,'最新价':f'¥{p:.2f}','总分':total,
                     '信号':get_signal(total),'RSI':f'{rsi:.1f}',
                     '24h':fmt_pct(chg1),'7日':fmt_pct(chg7),'30日':fmt_pct(chg30),'12月':fmt_pct(chg12)})
        time.sleep(0.08)
    dfr=pd.DataFrame(rows)
    if '总分' in dfr.columns:
        ok=dfr[dfr['总分']!='-'].copy(); ng=dfr[dfr['总分']=='-'].copy()
        if not ok.empty: ok=ok.sort_values('总分',ascending=False).reset_index(drop=True)
        dfr=pd.concat([ok,ng],ignore_index=True)
        dfr.index=dfr.index+1; dfr.index.name='排名'
    return dfr

def auto_select():
    scored=[]; failed=[]
    for code,name in FULL_STOCKS.items():
        df=get_kline(code)
        if df is None: failed.append(code); continue
        t,*_=score_stock(df); scored.append({'code':code,'name':name,'score':t})
        time.sleep(0.05)
    scored.sort(key=lambda x:x['score'],reverse=True)
    high=[s for s in scored if s['score']>=4]
    med=[s for s in scored if 0<=s['score']<4]
    low=[s for s in scored if s['score']<0]
    sel=high+med[:50-len(high)]
    if len(sel)<50:
        random.shuffle(low); sel+=low[:50-len(sel)]
    sel=sel[:50]
    for c,n in custom_stocks.items():
        if c not in [s['code'] for s in sel]: sel.append({'code':c,'name':n,'score':0})
    return sel

# ── UI ────────────────────────────────────────────────────────
st.title("🤖 AI+硬科技 选股系统")
st.caption(f"基础池 {len(FULL_STOCKS)}只 · 每日自动选50只 · yfinance数据 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")

c1,c2,c3 = st.columns([2,2,1])
with c1:
    add_code = st.text_input("添加股票代码（如 600519）", key="add_c")
    add_name = st.text_input("股票名称（如 贵州茅台）", key="add_n")
    if st.button("➕ 添加自定义股票", use_container_width=True):
        if add_code and add_name:
            suffix = '.SS' if add_code.startswith('6') or add_code.startswith('688') else '.SZ'
            custom_stocks[add_code+suffix] = add_name
            st.success(f"已添加 {add_name}({add_code+suffix})")
with c2:
    rm_code = st.text_input("移除自定义股票代码", key="rm_c")
    if st.button("➖ 移除自定义股票", use_container_width=True):
        suffix = '.SS' if rm_code.startswith('6') or rm_code.startswith('688') else '.SZ'
        custom_stocks.pop(rm_code+suffix, None)
        st.info(f"已尝试移除 {rm_code+suffix}")
with c3:
    st.write(""); run_btn = st.button("🚀 开始扫描 / 重新选股", use_container_width=True, type="primary")

if run_btn or 'df_result' not in st.session_state:
    with st.spinner("正在从 Yahoo Finance 获取数据，请稍候（约30秒）..."):
        sel = auto_select()
        st.session_state.df_result = scan_stocks(sel)
        st.session_state.sel_count = len(sel)

df = st.session_state.get('df_result', pd.DataFrame())

if not df.empty:
    valid = [x for x in df['总分'] if x!='-' and isinstance(x,(int,float))]
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("有效数据", len(valid))
    col2.metric("🔥 建议买入", sum(1 for x in valid if x>=6))
    col3.metric("✅ 可持有", sum(1 for x in valid if 4<=x<6))
    col4.metric("👀 观望", sum(1 for x in valid if 0<=x<4))
    col5.metric("🔵 回避", sum(1 for x in valid if x<0))

    # 格式化显示
    disp = df.copy()
    if '总分' in disp.columns:
        disp['总分'] = disp['总分'].apply(lambda x: x if x=='-' else int(x))
    st.dataframe(
        disp,
        use_container_width=True,
        hide_index=False,
        column_config={'最新价':st.column_config.Column(width='small'),
                       'RSI':st.column_config.Column(width='small'),
                       '24h':st.column_config.Column(width='small'),
                       '7日':st.column_config.Column(width='small'),
                       '30日':st.column_config.Column(width='small'),
                       '12月':st.column_config.Column(width='small')}
    )
else:
    st.info("点击「开始扫描」运行选股")
