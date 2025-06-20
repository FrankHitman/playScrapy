import os
import re
from bs4 import BeautifulSoup

# 目标目录
base_dir = os.path.dirname(os.path.abspath(__file__))
level_dirs = [os.path.join(base_dir, f'level{f:02d}') for f in range(0, 4)]

# 遍历所有以tsunagaru_开头的html文件
# target_files = [f for f in os.listdir(base_dir) if f.startswith('tsunagaru_') and f.endswith('.html')]

for level_dir in level_dirs:
    target_files = [f for f in os.listdir(level_dir) if f.startswith('tsunagaru_') and f.endswith('.html')]


    for html_file in target_files:
        html_path = os.path.join(level_dir, html_file)
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # 提取标题
        h2s = soup.find_all('h2', class_='c-sect__heading c-heading-b')
        titles = [h2.get_text(strip=True) if h2 else '' for h2 in h2s]

        # 提取描述
        descs = soup.find_all('p', id=re.compile(r'.*_txt01$'))
        descriptions = [desc.get_text(" ", strip=True).replace('\xa0', ' ') if desc else '' for desc in descs]

        # 提取对话内容
        table_divs = soup.find_all('div', class_='tabel-whole')
        sessions = []
        for table_div in table_divs:
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
            sessions.append(chats)

        # 输出到txt
        txt_file = os.path.splitext(html_file)[0] + '.txt'
        os.makedirs('txt', exist_ok=True)
        min_len = min(len(titles), len(descriptions), len(sessions))
        with open(f'txt/{txt_file}', 'w', encoding='utf-8') as f:
            for i in range(min_len):
                title = titles[i]
                description = descriptions[i]
                chats = sessions[i]
                f.write(f'标题: {title}\n')
                f.write(f'描述: {description}\n')
                for jp, pr, zh in chats:
                    f.write(f'[日文] {jp}\n')
                    f.write(f'[发音] {pr}\n')
                    f.write(f'[中文] {zh}\n')
                    f.write('\n')

print('提取完成！') 