import os
import sys
import signal
import subprocess
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
SERVER_DIR = BASE_DIR / "server"
WEB_DIR = BASE_DIR / "web"
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"

SERVER_PORT = "0220"
WEB_PORT = "5180"
BACKEND_URL = f"http://localhost:{SERVER_PORT}"
FRONTEND_URL = f"http://localhost:{WEB_PORT}"

processes: list[subprocess.Popen] = []


def print_banner():
    print("=" * 50)
    print("  EasyBX - 智能发票报销管理助手")
    print("=" * 50)
    print()


def print_info(message: str):
    print(f"[信息] {message}")


def print_success(message: str):
    print(f"[成功] {message}")


def print_warning(message: str):
    print(f"[警告] {message}")


def print_error(message: str):
    print(f"[错误] {message}")


def check_env():
    if not ENV_FILE.exists():
        print_warning(".env 文件不存在，正在从 .env.example 复制...")
        if ENV_EXAMPLE.exists():
            import shutil
            shutil.copy2(ENV_EXAMPLE, ENV_FILE)
            print_info("请编辑 .env 文件配置后重新启动")
            sys.exit(1)
        else:
            print_error(".env.example 文件也不存在，无法创建 .env 文件")
            sys.exit(1)
    print_success(".env 文件已找到")


def start_backend():
    print_info("启动后端服务...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", SERVER_PORT, "--reload"],
        cwd=str(SERVER_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(proc)
    return proc


def start_frontend():
    print_info("启动前端开发服务器...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(WEB_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(proc)
    return proc


def read_output(proc: subprocess.Popen, name: str, stop_flag):
    try:
        for line in proc.stdout:
            if stop_flag and stop_flag():
                break
            print(f"[{name}] {line}", end="")
    except ValueError:
        pass


def cleanup(signum=None, frame=None):
    print()
    print_info("正在停止所有服务...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print_success("所有服务已停止")
    sys.exit(0)


def main():
    print_banner()
    check_env()

    stop_flag = False
    def should_stop():
        return stop_flag

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    import threading

    backend_proc = start_backend()
    time.sleep(2)

    frontend_proc = start_frontend()

    t1 = threading.Thread(target=read_output, args=(backend_proc, "后端", should_stop), daemon=True)
    t2 = threading.Thread(target=read_output, args=(frontend_proc, "前端", should_stop), daemon=True)
    t1.start()
    t2.start()

    time.sleep(3)
    print()
    print("=" * 50)
    print("  EasyBX 启动完成!")
    print(f"  后端:     {BACKEND_URL}")
    print(f"  API文档:  {BACKEND_URL}/docs")
    print(f"  前端:     {FRONTEND_URL}")
    print("=" * 50)
    print()
    print_info("按 Ctrl+C 停止所有服务")
    print()

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print_error("后端服务意外退出")
                cleanup()
            if frontend_proc.poll() is not None:
                print_error("前端服务意外退出")
                cleanup()
    except KeyboardInterrupt:
        stop_flag = True
        cleanup()


if __name__ == "__main__":
    main()