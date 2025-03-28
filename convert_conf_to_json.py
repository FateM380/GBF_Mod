import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

def normalize_pattern(pattern: str) -> str:
    """标准化模式，将 'prd-game-a[0-9]?-gbf' 统一替换"""
    return pattern.replace("prd-game-a[0-9]?-gbf", "prd-game-a[0-9]?-granbluefantasy")

def extract_resource_info(pattern: str, target_url: str) -> Tuple[str, str, str]:
    """从原始URL或目标URL中提取资源类型、目录名和子目录名"""
    # 优先从目标URL（GitHub URL）中提取资源类型
    match = re.search(
        r'/(summon|leader|npc)/([^/]+)/([^/]+)/', 
        target_url
    )
    if match:
        return match.group(1), match.group(2), match.group(3)
    
    match = re.search(
        r'/(summon|leader|npc)/([^/]+)/', 
        target_url
    )
    if match:
        return match.group(1), match.group(2), ""

    # 如果目标URL中没有，再尝试从原始URL中提取
    match = re.search(
        r'/(?:assets/img/sp/)?assets/(summon|leader|npc)/([^/]+)/([^/]+)/', 
        pattern
    )
    if match:
        return match.group(1), match.group(2), match.group(3)
    
    match = re.search(
        r'/(?:assets/img/sp/)?assets/(summon|leader|npc)/([^/]+)/', 
        pattern
    )
    if match:
        return match.group(1), match.group(2), ""

    # 其他资源类型
    path_parts = [p for p in target_url.split('/') if p]
    if len(path_parts) >= 2:
        return "other", path_parts[-2], ""
    
    return "other", Path(target_url.split('/')[-1].split('?')[0]).stem, ""

def convert_conf_to_json(conf_path: str, output_json_path: Optional[str] = None) -> List[Dict]:
    """转换 .conf 文件到 .json 并实时显示详细日志"""
    conf_path = Path(conf_path)
    if not conf_path.exists():
        print(f"❌ 错误：输入文件 '{conf_path}' 不存在！")
        return []

    print(f"\n📂 正在读取文件: {conf_path}")

    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print(f"❌ 文件 '{conf_path}' 不是有效的UTF-8编码！")
        return []

    print(f"📌 读取完成，共 {len(lines)} 行数据。\n")

    rules = []
    current_group = "GBF_mod-Unknown"
    character_name = ""

    print("🚀 开始解析规则...\n")

    for index, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 跳过纯粹的注释行（以 # 开头但不包含 url 302）
        if line.startswith('#') and ' url 302 ' not in line:
            # 处理角色名标记
            if line.startswith('#start '):
                character_name = line.split('#start ')[1].split('#')[0].strip()
                print(f"📍 发现角色: {character_name}\n")
            continue

        # 解析规则行（可能以 #!#、#! 开头或没有前缀）
        original_line = line
        is_enabled = True
        
        # 处理禁用的规则
        if line.startswith('#!#'):
            is_enabled = False
            line = line[3:].strip()  # 移除 #!#
        elif line.startswith('#!'):
            is_enabled = False
            line = line[2:].strip()  # 移除 #!
        elif line.startswith('#'):
            # 其他 # 开头的行（如 #!/）但包含 url 302 的，也跳过
            continue

        # 确保是有效的规则行
        if ' url 302 ' not in line:
            continue

        # 分割规则
        parts = line.split(' url 302 ')
        if len(parts) != 2:
            print(f"⚠️ 警告：跳过格式不正确的行: {original_line}")
            continue

        original_pattern = parts[0].strip()
        target_url = parts[1].strip()

        # 标准化 pattern
        pattern = normalize_pattern(original_pattern)

        # 提取资源信息
        resource_type, dir_name, sub_dir = extract_resource_info(original_pattern, target_url)

        # 生成 name 和 group
        if resource_type == "summon":
            final_name = f"summon-{character_name}-{sub_dir if sub_dir else dir_name}"
            current_group = f"GBF_mod-Summon-{character_name.replace(' ', '_')}"
        elif resource_type == "leader":
            final_name = f"leader-{character_name}-{sub_dir if sub_dir else dir_name}"
            current_group = f"GBF_mod-leader-{character_name.replace(' ', '_')}"
        elif resource_type == "npc":
            final_name = f"NPC-{character_name}-{sub_dir if sub_dir else dir_name}"
            current_group = f"GBF_mod-NPC-{character_name.replace(' ', '_')}"
        else:
            final_name = f"{character_name}-{dir_name}" if character_name else dir_name
            current_group = f"GBF_mod-{character_name.replace(' ', '_')}" if character_name else "GBF_mod-Unknown"

        # 确保名称中不包含反斜杠和空格
        final_name = final_name.replace('\\', '').replace(' ', '_')

        # 输出详细解析信息
        print("=" * 60)
        print(f"🔍 规则 {index + 1}:")
        print(f"📌 原始行    : {original_line}")
        print(f"📌 处理后行  : {line}")
        print(f"📌 原始 URL  : {original_pattern}")
        print(f"➡️  目标 URL  : {target_url}")
        print(f"🔘 是否启用  : {'✅ 启用' if is_enabled else '❌ 禁用'}")
        print(f"📁 资源类型  : {resource_type}")
        print(f"📂 目录名    : {dir_name}")
        print(f"📂 子目录    : {sub_dir if sub_dir else '无'}")
        print(f"🏷️  生成 Name: {final_name}")
        print(f"🗂  归属 Group: {current_group}")
        print("=" * 60 + "\n")

        # 处理名称冲突
        base_name = final_name
        counter = 1
        while any(r['name'] == final_name for r in rules):
            final_name = f"{base_name}_{counter}"
            counter += 1
            if counter > 100:
                raise ValueError(f"无法为规则生成唯一名称: {pattern}")

        # 构建规则对象
        rules.append({
            "enable": is_enabled,
            "name": final_name,
            "ruleType": "redirect",
            "matchType": "regexp",
            "pattern": pattern,
            "exclude": "",
            "group": current_group,
            "isFunction": False,
            "action": "redirect",
            "to": target_url
        })

    # 确定输出路径
    output_json_path = Path(output_json_path) if output_json_path else conf_path.with_suffix('.json')

    # 写入 JSON
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        print(f"✅ 规则转换完成！共转换 {len(rules)} 条规则。")
        print(f"📄 输出 JSON 文件: {output_json_path}")
    except IOError as e:
        print(f"❌ 无法写入 JSON 文件 '{output_json_path}': {str(e)}")

    return rules

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="将 Surge/Quantumult X 的 .conf 规则转换为 JSON 格式",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-i', '--input', 
        required=True, 
        help="输入的 .conf 文件路径"
    )
    parser.add_argument(
        '-o', '--output', 
        help="输出的 .json 文件路径（可选）"
    )
    
    try:
        args = parser.parse_args()
        convert_conf_to_json(args.input, args.output)
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        exit(1)