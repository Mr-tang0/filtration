import csv
import random
import re
import time

import requests
import os
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# 创建result文件夹
result_dir = '../element'
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

target = []
for num in range(1, 93):
    element_num = f'{num:02d}'
    flag = os.path.exists(f"element/{element_num}.csv")
    if not flag:
        target.append(element_num)

errNum = []
# 批量处理元素01到92
for num in target:
    slp_t = random.randint(1, 5)
    print(f"等待 {slp_t} 秒...")
    time.sleep(random.randint(1, 5))

    # 格式化数字，不足两位补0
    element_num = f"{num}"
    url = f"https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z{element_num}.html"

    print(f"正在处理元素 {element_num}...")

    session = requests.Session()

    # 添加重试策略 - 设置3秒超时，最多重试3次
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    session.headers.update(headers)

    try:
        # 设置3秒超时时间
        response = session.get(url, timeout=(1, 3))  # 连接超时3秒，读取超时30秒
        response.encoding = 'utf-8'
    except requests.exceptions.RequestException as e:
        print(f"请求元素 {element_num} 失败: {e}")
        errNum.append(element_num)
        session.close()
        continue

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找包含ASCII格式数据的pre标签
    pre_tags = soup.find_all('pre')

    found_data = False
    for pre in pre_tags:
        pre_text = pre.get_text()
        # 检查是否包含表格数据（通过查找特定的表头）
        if 'Energy' in pre_text and 'μ/ρ' in pre_text:
            found_data = True
            print(f"找到元素 {element_num} 的ASCII格式表格数据", pre_text)

            # 解析数据
            lines = pre_text.strip().split('\n')
            # 过滤掉分隔线和空行
            data_lines = [line for line in lines if
                          line.strip() and not line.startswith('___') and 'Energy' not in line and '(MeV)' not in line]

            # 解析数值数据
            parsed_data = []
            for line in data_lines:
                if line.strip():
                    # 使用正则表达式分割数据
                    values = re.split(r'\s+', line.strip())
                    if len(values) == 3:
                        parsed_data.append({
                            'Energy': values[0],
                            'MAC': values[1],
                            'Coherent-Corrected MAC': values[2]
                        })
                    elif len(values) == 4:
                        parsed_data.append({
                            'Energy': values[1],
                            'MAC': values[2],
                            'Coherent-Corrected MAC': values[3]
                        })
                    else:
                        print(f"元素 {element_num} 的数据格式不正确: {line}")
                        continue

            # 保存为CSV文件
            csv_filename = os.path.join(result_dir, f'{element_num}.csv')
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Energy', 'MAC', 'Coherent-Corrected MAC']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # 写入表头
                writer.writeheader()

                # 写入数据行
                for data in parsed_data:
                    writer.writerow(data)

            print(f"元素 {element_num} 数据已保存到 {csv_filename}")
            break

    if not found_data:
        print(f"元素 {element_num} 未找到有效数据")

    # 关闭会话
    session.close()

print("所有元素数据处理完成！")
print("错误元素：", errNum)
