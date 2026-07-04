# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time, random
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="AI硬科技股票打分系统", page_icon="🤖", layout="wide")

# ── 完整AI+硬科技股票池（80只）────────────────────────────────
FULL_STOCKS = {
    # ===== AI芯片/算力 =====
    '688256.SS': '寒武纪', '688041.SS': '海光信息', '603019.SS': '中科曙光',
    '000977.SZ': '浪潮信息', '300308.SZ': '中际旭创', '300394.SZ': '天孚通信',
    '300502.SZ': '新易盛', '688498.SS': '源杰科技', '300661.SZ': '圣邦股份',
    '688702.SS': '盛科通信',
    # ===== 半导体设计 =====
    '603501.SS': '韦尔股份', '300782.SZ': '卓胜微', '688008.SS': '澜起科技',
    '603986.SS': '兆易创新', '300223.SZ': '北京君正', '688521.SS': '芯原股份',
    '688052.SS': '纳芯微', '300672.SZ': '国科微', '688018.SS': '乐鑫科技',
    '688798.SS': '艾为电子',
    # ===== 半导体设备 =====
    '002371.SZ': '北方华创', '688012.SS': '中微公司', '688072.SS': '拓荆科技',
    '688037.SS': '芯源微', '688120.SS': '华海清科', '300604.SZ': '长川科技',
    '688200.SS': '华峰测控', '688409.SS': '富创精密', '688361.SS': '中科飞测',
    '688627.SS': '精智达',
    # ===== 半导体材料 =====
    '688019.SS': '安集科技', '300706.SZ': '阿石创', '300655.SZ': '晶瑞电材',
    '300576.SZ': '容大感光', '688596.SS': '正帆科技', '300054.SZ': '鼎龙股份',
    '688106.SS': '金宏气体', '688268.SS': '华特气体', '688378.SS': '奥来德',
    '688550.SS': '瑞联新材',
    # ===== 机器人/自动化 =====
    '300124.SZ': '汇川技术', '688169.SS': '石头科技', '002747.SZ': '埃斯顿',
    '300024.SZ': '机器人', '688017.SS': '绿的谐波', '002472.SZ': '双环传动',
    '688305.SS': '科德数控', '688165.SS': '埃夫特', '301029.SZ': '怡合达',
    '688697.SS': '纽威数控',
    # ===== 智能驾驶/汽车电子 =====
    '002920.SZ': '德赛西威', '002906.SZ': '华阳集团', '601689.SS': '拓普集团',
    '300496.SZ': '中科创达', '002405.SZ': '四维图新', '688326.SS': '经纬恒润',
    '300450.SZ': '先导智能', '688116.SS': '天奈科技',
    # ===== AI应用/大模型 =====
    '002230.SZ': '科大讯飞', '688111.SS': '金山办公', '300624.SZ': '万兴科技',
    '300418.SZ': '昆仑万维', '300454.SZ': '深信服', '688568.SS': '中科星图',
    '688031.SS': '星环科技', '300383.SZ': '光环新网',
    # ===== 信创/国产替代 =====
    '600536.SS': '中国软件', '688561.SS': '奇安信', '300188.SZ': '美亚柏科',
    '002439.SZ': '启明星辰', '300369.SZ': '绿盟科技', '688201.SS': '信安世纪',
    '300598.SZ': '诚迈科技', '688232.SS': '新点软件',
    # ===== 消费电子 =====
    '002475.SZ': '立讯精密', '601138.SS': '工业富联', '002241.SZ': '歌尔股份',
    '600745.SS': '闻泰科技', '002600.SZ': '领益智造', '002384.SZ': '东山精密',
    '603228.SS': '景旺电子', '002916.SZ': '深南电路',
}

custom_stocks = {}

# ── 核心函数 ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_kline(code):
    try:
        df = yf.Ticker(code).history(
            start=(datetime.now()-timedelta(days=470)).strftime('%Y-%m-%d'),
            end=datetime.now().strftime('%Y-%m-%d'), auto_adjust=True)
        if df is None or len(df) < 278:
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
    elif 40<=rsi<=77: sr=2
    elif 34<=rsi<48: sr=1
    elif rsi>125 or rsi<12: sr=-2
    elif rsi>113: sr=-1
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
    chgH=((c.iloc[-1]-c.iloc[-171])/c.iloc[-171])*100 if len(c)>177 else 0
    schg=(1 if 5<=chg5<=19 else -1 if chg5>47 else 0)+(1 if 20<=chgH<=121 else -1 if chgH>355 else 0)
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
        if df is None or len(df)<278:
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
        time.sleep(0.05)
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
        time.sleep(0.02)
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
st.title("🤖 AI硬科技股票打分系统")
st.caption(f"基础池 {len(FULL_STOCKS)}只AI+硬科技股票 · 每日自动选50只 · 多因子技术分析 · yfinance数据")

# 信息栏
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
col_info1.metric("📊 基础股票池", f"{len(FULL_STOCKS)}只")
col_info2.metric("🎯 每日精选", "50只")
col_info3.metric("⚡ 数据源", "Yahoo Finance")
col_info4.metric("🕐 更新时间", datetime.now().strftime('%m/%d %H:%M'))

# ── 手动添加自定义股票（折叠式）──────────────────────────────
with st.expander("✏️ 手动添加/移除自定义股票（高级功能）"):
    st.caption("如果你想在系统自动筛选的50只之外，额外关注某些特定股票，可以使用此功能。")
    c1,c2,c3 = st.columns([2,2,1])
    with c1:
        add_code = st.text_input("添加股票代码（如 600519）", key="add_c")
        add_name = st.text_input("股票名称（如 贵州茅台）", key="add_n")
        if st.button("➕ 添加", use_container_width=True):
            if add_code and add_name:
                suffix = '.SS' if add_code.startswith('6') or add_code.startswith('688') else '.SZ'
                custom_stocks[add_code+suffix] = add_name
                st.success(f"已添加 {add_name}({add_code+suffix})")
    with c2:
        rm_code = st.text_input("移除自定义股票代码", key="rm_c")
        if st.button("➖ 移除", use_container_width=True):
            suffix = '.SS' if rm_code.startswith('6') or rm_code.startswith('688') else '.SZ'
            custom_stocks.pop(rm_code+suffix, None)
            st.info(f"已尝试移除 {rm_code+suffix}")
    with c3:
        st.write("")
        st.write("")
        if custom_stocks:
            st.info(f"当前已添加 {len(custom_stocks)} 只自定义股票")
            if st.button("🗑️ 清空全部", use_container_width=True):
                custom_stocks.clear()
                st.warning("已清空所有自定义股票")

# ── 扫描按钮 ────────────────────────────────────────────────
run_btn = st.button("🚀 开始扫描 / 重新选股", use_container_width=True, type="primary")

# ── 扫描逻辑 ────────────────────────────────────────────────
if run_btn or 'df_result' not in st.session_state:
    with st.spinner("正在从 Yahoo Finance 获取数据，请稍候（约30~50秒）..."):
        sel = auto_select()
        st.session_state.df_result = scan_stocks(sel)
        st.session_state.sel_count = len(sel)
        st.session_state.custom_count = len(custom_stocks)

df = st.session_state.get('df_result', pd.DataFrame())

if not df.empty:
    st.markdown("---")
    st.subheader("📊 扫描结果")
    
    valid = [x for x in df['总分'] if x!='-' and isinstance(x,(int,float))]
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("有效数据", len(valid))
    col2.metric("🔥 建议买入", sum(1 for x in valid if x>=6))
    col3.metric("✅ 可持有", sum(1 for x in valid if 4<=x<6))
    col4.metric("👀 观望", sum(1 for x in valid if 0<=x<4))
    col5.metric("🔵 回避", sum(1 for x in valid if x<0))

    # 显示表格
    disp = df.copy()
    if '总分' in disp.columns:
        disp['总分'] = disp['总分'].apply(lambda x: x if x=='-' else int(x))
    st.dataframe(
        disp,
        use_container_width=True,
        hide_index=False,
        column_config={
            '最新价': st.column_config.Column(width='small'),
            'RSI': st.column_config.Column(width='small'),
            '24h': st.column_config.Column(width='small'),
            '7日': st.column_config.Column(width='small'),
            '30日': st.column_config.Column(width='small'),
            '12月': st.column_config.Column(width='small'),
        }
    )

# ── 使用说明 ────────────────────────────────────────────────
st.markdown("---")
st.subheader("📖 使用说明")

with st.expander("点击展开详细使用说明"):
    st.markdown("""
### 🎯 系统功能
本系统从 **80只AI+硬科技股票** 中，每日自动选出评分最高的 **50只**，并进行多因子技术分析。

### 📊 评分因子说明
| 因子 | 权重 | 说明 |
|------|------|------|
| RSI | 0~2分 | 相对强弱指标，40~72为健康区间 |
| MACD | 0~2分 | 趋势动能，正值且放大为佳 |
| 均线 | 0~3分 | 短期均线在长期均线上方为多头排列 |
| 量比 | 0~1分 | 成交量温和放量为佳 |
| 涨跌幅 | 0~2分 | 短期温和上涨、中期稳步上涨为佳 |

### 🏷️ 信号解读
| 信号 | 总分 | 含义 |
|------|------|------|
| 🔥🔥 强烈买入 | ≥8分 | 多项指标共振，强势信号 |
| 🔥 建议买入 | 6~7分 | 多数指标向好 |
| ✅ 持有 | 4~5分 | 趋势尚可，可继续持有 |
| 👀 观望 | 2~3分 | 中性偏弱，等待机会 |
| 🟢 小仓 | 0~1分 | 可少量试探 |
| ⏳ 等待 | -1~-2分 | 趋势偏弱，耐心等待 |
| 🔵 回避 | ≤-3分 | 多项指标走弱，建议回避 |

### 📝 操作指南
1. **点击「开始扫描」**：系统自动从80只中选出最优50只并打分
2. **添加自定义股票**：展开「手动添加」区域，输入代码和名称
3. **移除自定义股票**：在「手动添加」区域输入代码即可移除
4. **刷新页面**：重新获取最新数据

### ⚠️ 注意事项
- 数据来源为 **Yahoo Finance**，可能有延迟
- 首次加载需 **30~50秒**，属于正常现象
- 手动添加的股票**刷新页面后会消失**，需重新添加
- 建议**每天早上9:30开盘后**运行一次
    """)

# ── 免责声明 ────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="background:#fff3e0;border:1px solid #ffe0b2;border-radius:10px;padding:16px 20px;margin:16px 0;">
<h4 style="color:#e65100;margin:0 0 8px 0;">⚠️ 免责声明</h4>
<p style="color:#555;font-size:13px;line-height:1.6;margin:0;">
本系统仅供<b>学习研究和技术交流</b>目的使用，不构成任何投资建议、买卖建议或投资决策依据。<br><br>
本系统基于公开市场数据进行技术分析，数据可能存在延迟、不准确或不完整的情况。作者不对数据的准确性、完整性或及时性作出任何保证。<br><br>
股票投资具有高风险性，可能导致本金损失。用户在使用本系统时应自行判断，并对自己的投资决策负全部责任。<br><br>
作者明确声明：对于任何人因使用本系统或其提供的信息而导致的任何直接或间接损失，不承担任何法律责任。<br><br>
使用本系统即表示您已阅读、理解并同意本免责声明的全部内容。
</p>
</div>
""", unsafe_allow_html=True)

# 底部
st.markdown("""
<div style="text-align:center;padding:12px 0;font-size:12px;color:#90a4ae;">
    🤖 AI硬科技股票打分系统 · 仅供学习研究 · 不构成投资建议
    <br>
    © 2025 · Powered by Streamlit & Yahoo Finance
</div>
""", unsafe_allow_html=True)
