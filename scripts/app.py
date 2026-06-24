import streamlit as st
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from scraper.proxy_manager import ProxyManager

st.set_page_config(
    page_title="知乎评论整合 - 配置中心",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ 知乎评论整合 - 配置中心")

# 侧边栏导航
page = st.sidebar.selectbox(
    "导航",
    ["📊 总览", "🔧 代理配置", "⚙️ 抓取设置", "🎯 测试抓取"]
)

def load_config():
    config_path = Path("config/settings.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    config_path = Path("config/settings.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

if page == "📊 总览":
    st.header("项目概览")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("抓取模块", "✅ 正常")
    with col2:
        st.metric("分析模块", "✅ 正常")
    with col3:
        st.metric("生成模块", "✅ 正常")
    
    st.info("使用左侧导航进行配置")
    
    # 快速开始
    st.subheader("快速开始")
    st.code("""
# 1. 配置代理（推荐）
python main.py --url "https://example.com" --validate-proxy

# 2. 测试抓取
python main.py --url "https://zhuanlan.zhihu.com/p/123456789" --max-comments 10

# 3. 完整抓取
python main.py --url "https://zhuanlan.zhihu.com/p/123456789" --output result.md
    """)

elif page == "🔧 代理配置":
    st.header("🔧 代理配置")
    
    config = load_config()
    proxy_config = config.get("proxy", {})
    ja_config = config.get("ja_proxy", {})
    
    # 代理来源选择
    proxy_source = st.radio(
        "代理来源",
        ["极安代理（推荐）", "免费代理API", "自定义代理列表"],
        index=0
    )
    
    if proxy_source == "极安代理（推荐）":
        st.info("极安代理：稳定可靠的付费代理服务")
        ja_enabled = True
        ja_key = st.text_input(
            "极安代理 Key",
            value=ja_config.get("key", ""),
            type="password",
            placeholder="请输入你的极安代理key"
        )
        ja_num = st.number_input("每次提取数量", value=ja_config.get("num", 5), min_value=1, max_value=20)
        
        if ja_key:
            st.success("已配置极安代理")
        else:
            st.warning("请先到 https://www.ja.cn 购买代理并获取key")
        
        use_free_api = False
        proxy_list = []
        
    elif proxy_source == "免费代理API":
        st.info("免费代理API：不稳定，适合测试")
        ja_enabled = False
        use_free_api = True
        proxy_list = []
        ja_key = ""
        ja_num = 5
        
    else:
        st.info("自定义代理列表：手动输入代理地址")
        ja_enabled = False
        use_free_api = False
        proxy_list = st.text_area(
            "代理列表（每行一个）",
            value="\n".join(proxy_config.get("proxy_list", [])),
            height=150,
            placeholder="http://123.123.123.123:8080\nhttp://456.456.456.456:3128"
        )
        proxy_list = [p.strip() for p in proxy_list.split("\n") if p.strip()]
        ja_key = ""
        ja_num = 5
    
    # 高级设置
    with st.expander("高级设置"):
        col1, col2 = st.columns(2)
        with col1:
            timeout = st.number_input("代理超时（秒）", value=proxy_config.get("proxy_timeout", 10), min_value=5, max_value=60)
            rotate_interval = st.number_input("轮换间隔（请求数）", value=proxy_config.get("rotate_interval", 5), min_value=1, max_value=20)
        with col2:
            refresh_hours = st.number_input("刷新间隔（小时）", value=proxy_config.get("refresh_interval_hours", 6), min_value=1, max_value=24)
    
    # 保存配置
    if st.button("保存代理配置", type="primary"):
        config["proxy"] = {
            "enabled": True,
            "use_free_api": use_free_api,
            "proxy_list": proxy_list,
            "rotate_interval": rotate_interval,
            "proxy_timeout": timeout,
            "refresh_interval_hours": refresh_hours
        }
        config["ja_proxy"] = {
            "enabled": ja_enabled,
            "key": ja_key,
            "num": ja_num
        }
        save_config(config)
        st.success("代理配置已保存！")
    
    # 验证代理
    st.divider()
    st.subheader("代理验证")
    
    if st.button("验证代理可用性"):
        with st.spinner("正在验证代理..."):
            try:
                proxy_manager = ProxyManager()
                proxy_manager.config["proxy"]["enabled"] = True
                proxy_manager.config["proxy"]["use_free_api"] = use_free_api
                proxy_manager.config["ja_proxy"] = {
                    "enabled": ja_enabled,
                    "key": ja_key,
                    "num": ja_num
                }
                if proxy_source == "自定义代理列表":
                    proxy_manager.config["proxy"]["proxy_list"] = proxy_list
                
                proxy = proxy_manager.get_random_proxy()
                if proxy:
                    st.success(f"找到可用代理: {proxy.get('server', '未知')}")
                else:
                    st.warning("未找到可用代理，请检查配置")
            except Exception as e:
                st.error(f"验证失败: {e}")

elif page == "⚙️ 抓取设置":
    st.header("⚙️ 抓取设置")
    
    config = load_config()
    scraper_config = config.get("scraper", {})
    limits_config = config.get("limits", {})
    detection_config = config.get("detection", {})
    
    # 基本设置
    st.subheader("基本设置")
    col1, col2 = st.columns(2)
    
    with col1:
        headless = st.checkbox("无头模式（后台运行）", value=scraper_config.get("headless", False))
        max_comments = st.number_input("最大评论数", value=limits_config.get("max_comments", 500), min_value=10, max_value=2000)
    
    with col2:
        page_timeout = st.number_input("页面加载超时（秒）", value=scraper_config.get("page_load_timeout", 30000) // 1000, min_value=10, max_value=60) * 1000
        daily_limit = st.number_input("每日请求限制", value=limits_config.get("daily_limit", 1000), min_value=100, max_value=5000)
    
    # 延迟设置
    st.subheader("延迟设置")
    col1, col2 = st.columns(2)
    
    with col1:
        min_delay = st.slider("最小延迟（秒）", 1.0, 10.0, scraper_config.get("request_delay", [2, 5])[0], 0.5)
    with col2:
        max_delay = st.slider("最大延迟（秒）", 2.0, 15.0, scraper_config.get("request_delay", [2, 5])[1], 0.5)
    
    # 反检测设置
    st.subheader("反检测设置")
    col1, col2 = st.columns(2)
    
    with col1:
        enable_stealth = st.checkbox("启用隐身模式", value=detection_config.get("enable_stealth", True))
        humanize = st.checkbox("人性化行为模拟", value=detection_config.get("humanize_behavior", True))
    
    with col2:
        enable_verification = st.checkbox("启用验证码检测", value=detection_config.get("enable_verification_check", True))
        max_retries = st.number_input("最大重试次数", value=limits_config.get("max_retries", 3), min_value=1, max_value=10)
    
    # 保存配置
    if st.button("保存抓取设置", type="primary"):
        config["scraper"] = {
            "headless": headless,
            "request_delay": [min_delay, max_delay],
            "page_load_timeout": page_timeout,
            "max_scrolls": scraper_config.get("max_scrolls", 15),
            "scroll_delay": scraper_config.get("scroll_delay", [1, 3]),
            "user_agents": scraper_config.get("user_agents", []),
            "viewport": scraper_config.get("viewport", {"width": 1920, "height": 1080}),
            "disable_images": scraper_config.get("disable_images", False),
            "disable_css": scraper_config.get("disable_css", False)
        }
        
        config["limits"] = {
            "max_comments": max_comments,
            "daily_limit": daily_limit,
            "cooldown_minutes": limits_config.get("cooldown_minutes", 30),
            "max_retries": max_retries,
            "retry_delay": limits_config.get("retry_delay", [30, 60])
        }
        
        config["detection"] = {
            "enable_stealth": enable_stealth,
            "enable_verification_check": enable_verification,
            "verification_wait_time": detection_config.get("verification_wait_time", 30),
            "humanize_behavior": humanize
        }
        
        save_config(config)
        st.success("抓取设置已保存！")

elif page == "🎯 测试抓取":
    st.header("🎯 测试抓取")
    
    url = st.text_input("知乎文章链接", placeholder="https://zhuanlan.zhihu.com/p/123456789")
    
    col1, col2 = st.columns(2)
    with col1:
        test_comments = st.number_input("测试评论数", value=10, min_value=1, max_value=50)
    with col2:
        output_file = st.text_input("输出文件", value="test_output.md")
    
    if st.button("开始测试", type="primary"):
        if not url:
            st.error("请输入知乎文章链接")
        else:
            with st.spinner("正在测试抓取..."):
                try:
                    # 这里可以调用实际的抓取函数
                    # 为了演示，先显示配置信息
                    config = load_config()
                    
                    st.success("测试配置已准备好！")
                    st.json({
                        "url": url,
                        "max_comments": test_comments,
                        "output": output_file,
                        "proxy_enabled": config.get("proxy", {}).get("enabled", False)
                    })
                    
                    st.info("请在终端运行以下命令进行实际测试：")
                    st.code(f"python main.py --url \"{url}\" --max-comments {test_comments} --output {output_file}")
                    
                except Exception as e:
                    st.error(f"测试失败: {e}")
    
    # 显示最近日志
    st.divider()
    st.subheader("最近日志")
    
    log_file = Path("scraper.log")
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()[-20:]  # 显示最近20行
            st.code("".join(logs), language="text")
    else:
        st.info("暂无日志文件")

# 页脚
st.divider()
st.caption("知乎评论整合工具 v1.0 | 配置中心")