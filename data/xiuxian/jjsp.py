import os
import json
# 用来给所有json文件的rank字段加减对应数字以适配新加的境界
def update_rank(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        update_value(data, 'rank', 3) # 数字改这里
                        f.seek(0)
                        json.dump(data, f, indent=4, ensure_ascii=False) 
                        f.truncate()
                except Exception as e:
                    print("处理 {} 出错: {}".format(file_path, e))

def update_value(d, target_key, increment):
    for k, v in d.items():
        if k == target_key and isinstance(v, int) and v != -5: # -5不加
            d[k] = v + increment # 加减调这里
        elif isinstance(v, dict):
            update_value(v, target_key, increment)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    update_value(item, target_key, increment)

if __name__ == "__main__":
    root_directory = os.path.dirname(os.path.abspath(__file__))
    update_rank(root_directory)
