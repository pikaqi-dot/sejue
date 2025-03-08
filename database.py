import sqlite3
import os
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.db_file = "colorblind_test.db"
        self._connection = None
        self.init_database()

    @property
    def connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_file)
        return self._connection

    @contextmanager
    def get_cursor(self):
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def init_database(self):
        with self.get_cursor() as cursor:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                created_at TIMESTAMP
            )
            ''')

    def check_duplicate_answer(self, answer):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM questions WHERE correct_answer = ?", (answer,))
            return cursor.fetchone()[0] > 0

    def add_question(self, image_path, correct_answer):
        if self.check_duplicate_answer(correct_answer):
            return False, "题库中已存在相同答案的题目"
            
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO questions (image_path, correct_answer, created_at) VALUES (?, ?, ?)",
                (image_path, correct_answer, datetime.now())
            )
            return True, "保存成功"

    def get_all_questions(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM questions ORDER BY id ASC")
            return cursor.fetchall()

    def get_all_image_paths(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT image_path FROM questions")
            return [row[0] for row in cursor.fetchall()]

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

    def delete_question(self, question_id):
        with self.get_cursor() as cursor:
            # 先获取图片路径
            cursor.execute("SELECT image_path FROM questions WHERE id = ?", (question_id,))
            result = cursor.fetchone()
            if result:
                image_path = result[0]
                # 删除数据库记录
                cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                return image_path
            return None