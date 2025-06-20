import os
import re
from bs4 import BeautifulSoup

# 目标目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 遍历所有以tsunagaru_开头的html文件
target_files = [f for f in os.listdir(base_dir) if f.startswith('tsunagaru_') and f.endswith('.html')]

for html_file in target_files:
    html_path = os.path.join(base_dir, html_file)
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # 提取标题
    h2 = soup.find('h2', class_='c-sect__heading c-heading-b')
    title = h2.get_text(strip=True) if h2 else ''

    # 提取描述
    desc_p = soup.find('p', id=re.compile(r'.*_txt01$'))
    desc = desc_p.get_text(" ", strip=True).replace('\xa0', ' ') if desc_p else ''

    # 提取对话内容
    table_div = soup.find('div', class_='tabel-whole')
    chats = []
    if table_div:
        # 查找所有日文、发音、中文的句子
        jp_list = table_div.find_all('td',id=re.compile(r'^t005_scene_c01_script_lang1_txt_\d+$'))
        pr_list = table_div.find_all('td',id=re.compile(r'^t005_scene_c01_script_lang2_txt_\d+$'))
        zh_list = table_div.find_all('td',id=re.compile(r'^t005_scene_c01_script_lang3_txt_\d+$'))
        # 以最短的长度为准，保证一一对应
        min_len = min(len(jp_list), len(pr_list), len(zh_list))
        for i in range(min_len):
            jp = jp_list[i].get_text(strip=True)
            pr = pr_list[i].get_text(strip=True)
            zh = zh_list[i].get_text(strip=True)
            chats.append((jp, pr, zh))

    # 输出到txt
    txt_file = os.path.splitext(html_file)[0] + '.txt'
    txt_path = os.path.join(base_dir, txt_file)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f'标题: {title}\n')
        f.write(f'描述: {desc}\n')
        for jp, pr, zh in chats:
            f.write(f'[日文] {jp}\n')
            f.write(f'[发音] {pr}\n')
            f.write(f'[中文] {zh}\n')
            f.write('\n')

print('提取完成！') 