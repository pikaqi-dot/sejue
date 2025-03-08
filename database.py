import sqlite3
import os
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO

class Database:
    def __init__(self):
        self.db_file = "colorblind_test.db"
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            created_at TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def check_duplicate_answer(self, answer):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM questions WHERE correct_answer = ?", (answer,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0

    def add_question(self, image_path, correct_answer):
        # 检查是否存在重复答案
        if self.check_duplicate_answer(correct_answer):
            return False, "题库中已存在相同答案的题目"
            
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO questions (image_path, correct_answer, created_at) VALUES (?, ?, ?)",
            (image_path, correct_answer, datetime.now())
        )
        
        conn.commit()
        conn.close()
        return True, "保存成功"

    def get_all_questions(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM questions ORDER BY created_at DESC")
        questions = cursor.fetchall()
        
        conn.close()
        return questions

    def download_image(self, image_url):
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                # 验证是否为有效的图片
                img = Image.open(BytesIO(response.content))
                
                # 生成文件名和保存路径
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = '.jpg'  # 默认保存为jpg
                new_filename = f"test_{timestamp}{file_extension}"
                save_path = os.path.join("images", new_filename)
                
                # 保存图片
                img.save(save_path)
                return save_path, None
            return None, "无法下载图片"
        except Exception as e:
            return None, f"下载图片出错: {str(e)}"