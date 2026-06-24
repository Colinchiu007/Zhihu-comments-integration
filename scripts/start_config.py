import subprocess
import sys
import webbrowser
import time

def main():
    print("启动知乎评论整合配置中心...")
    print("访问地址: http://localhost:8501")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    # 启动Streamlit
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务启动
        time.sleep(3)
        
        # 打开浏览器
        webbrowser.open("http://localhost:8501")
        
        # 等待用户中断
        process.wait()
        
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        process.terminate()
        process.wait()
        print("服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()