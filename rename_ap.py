import os

def batch_rename():
    # 1. 获取当前脚本所在的文件夹路径
    root_path = os.getcwd()
    
    # 支持的扩展名
    target_extensions = ('.jpg', '.jpeg', '.png')
    suffix = "_ap"
    count = 0

    print(f"--- 脚本启动 ---")
    print(f"正在扫描目录: {root_path}")
    print("----------------")
    
    for subdir, dirs, files in os.walk(root_path):
        for file in files:
            # 检查后缀名（忽略大小写）
            if file.lower().endswith(target_extensions):
                # 分离文件名和后缀
                name, ext = os.path.splitext(file)
                
                # 检查文件名是否已经以 _ap 结尾
                if not name.endswith(suffix):
                    old_path = os.path.join(subdir, file)
                    new_name = f"{name}{suffix}{ext}"
                    new_path = os.path.join(subdir, new_name)
                    
                    try:
                        os.rename(old_path, new_path)
                        print(f"[成功] {file} -> {new_name}")
                        count += 1
                    except Exception as e:
                        print(f"[错误] 无法重命名 {file}: {e}")

    print("----------------")
    print(f"处理完成！共修改了 {count} 个文件。")
    # 防止窗口直接关闭
    input("按回车键退出...")

if __name__ == "__main__":
    batch_rename()