# pip install pywin32
# pip install pyinstaller
# pip install psutil

import psutil
import time
import os
import sys
import win32event
import win32api
import winerror

# 全局互斥锁，确保只有一个实例运行
MUTEX_NAME = "SGuardMonitorMutex"

target_list = []
handled_list = {}

def is_already_running():
    try:
        mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return True
        return False
    except Exception as e:
        print(f"检查互斥锁时出错: {e}")
        return False


def set_process_priority_and_affinity(pid):
    try:
        process = psutil.Process(pid)
        process.nice(psutil.IDLE_PRIORITY_CLASS)
        print(f"已设置进程 {pid} 优先级为最低（IDLE）")

        cpu_count = os.cpu_count() or 1
        last_cpu = cpu_count - 1
        process.cpu_affinity([last_cpu])
        print(f"已绑定进程 {pid} 到最后一个CPU核心（核心 {last_cpu}）")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"处理进程 {pid} 时出错: {e}")


def monitor_sguard():
    print("开始监控 SGuard64.exe 进程...")
    print("按 Ctrl+C 停止监控")

    try:
        while True:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    target = proc.info['name'].lower()
                    if target in target_list:
                        if target not in handled_list or handled_list[target] != proc.pid:
                            print(f"发现 SGuard64.exe 进程 (PID: {proc.info['pid']})")
                            handled_list[target] = proc.pid
                            set_process_priority_and_affinity(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n监控已停止")


if __name__ == "__main__":
    if not sys.platform.startswith('win'):
        print("此脚本仅适用于Windows系统")
        sys.exit(1)

    if is_already_running():
        print("程序已经在运行，请勿重复启动！")
        sys.exit(0)

    with open("list.txt", "r", encoding="utf-8") as file:
        for line in file:
            target_list.append(line.strip())
    try:
        psutil.process_iter()
    except Exception as e:
        print("请以管理员身份运行此脚本")
        sys.exit(1)

    monitor_sguard()
