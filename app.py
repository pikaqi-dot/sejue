import streamlit as st
import os
from database import Database
from datetime import datetime
import shutil
import requests
from PIL import Image
from io import BytesIO

# 初始化数据库
db = Database()

# 创建图片存储目录
if not os.path.exists("images"):
    os.makedirs("images")

def save_uploaded_file(uploaded_file):
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(uploaded_file.name)[1]
    new_filename = f"test_{timestamp}{file_extension}"
    
    # 保存文件
    save_path = os.path.join("images", new_filename)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path

def main():
    st.title("色盲测试题库管理系统")
    
    tab1, tab2 = st.tabs(["上传新题目", "查看题库"])
    
    with tab1:
        st.header("上传新的测试题目")
        
        # 添加图片上传选项
        upload_method = st.radio("选择上传方式", ["本地上传", "网址上传"])
        
        if upload_method == "本地上传":
            uploaded_file = st.file_uploader("选择色盲测试图片", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                st.image(uploaded_file, caption="预览图片")
                image_path = save_uploaded_file(uploaded_file) if uploaded_file else None
        else:
            image_url = st.text_input("输入图片网址")
            if image_url:
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        st.image(image, caption="预览图片")
                        image_path, error = db.download_image(image_url)
                        if error:
                            st.error(error)
                except Exception as e:
                    st.error(f"无法加载图片: {str(e)}")
                    image_path = None
        
        correct_answer = st.text_input("输入正确答案")
        
        if st.button("保存题目"):
            if ((upload_method == "本地上传" and uploaded_file) or 
                (upload_method == "网址上传" and image_url)) and correct_answer:
                if upload_method == "本地上传":
                    image_path = save_uploaded_file(uploaded_file)
                
                if image_path:
                    success, message = db.add_question(image_path, correct_answer)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                        # 如果保存失败，删除已上传的图片
                        if os.path.exists(image_path):
                            os.remove(image_path)
            else:
                st.error("请上传图片并输入正确答案！")
    
    # 查看题库标签页
    with tab2:
        st.header("题库列表")
        
        # 添加清理按钮
        if st.button("清理未使用的图片"):
            # 获取数据库中的所有图片路径
            db_image_paths = set(db.get_all_image_paths())
            
            # 获取images文件夹中的所有文件
            image_files = [os.path.join("images", f) for f in os.listdir("images")]
            
            # 找出不在数据库中的文件
            unused_images = [f for f in image_files if f not in db_image_paths]
            
            # 删除未使用的图片
            for img_path in unused_images:
                try:
                    os.remove(img_path)
                except Exception as e:
                    st.error(f"删除文件 {img_path} 失败: {str(e)}")
            
            if unused_images:
                st.success(f"成功清理 {len(unused_images)} 个未使用的图片文件")
            else:
                st.info("没有发现未使用的图片文件")
    
        questions = db.get_all_questions()
        
        for question in questions:
            with st.expander(f"题目 #{question[0]}"):
                if os.path.exists(question[1]):
                    st.image(question[1])      
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"显示答案 #{question[0]}", key=f"answer_btn_{question[0]}"):
                            st.write(f"正确答案: {question[2]}")
                        st.write(f"创建时间: {question[3]}")
                    
                    with col2:
                        if st.button("删除题目", key=f"delete_btn_{question[0]}"):
                            # 删除数据库记录并获取图片路径
                            image_path = db.delete_question(question[0])
                            # 删除图片文件
                            if image_path and os.path.exists(image_path):
                                try:
                                    os.remove(image_path)
                                    st.success("题目已删除")
                                    st.rerun()  # 使用新的 rerun 方法
                                except Exception as e:
                                    st.error(f"删除图片文件失败: {str(e)}")
                            else:
                                st.success("题目已删除")
                                st.rerun()  # 使用新的 rerun 方法
                else:
                    st.error("图片文件不存在")
if __name__ == "__main__":
    main()