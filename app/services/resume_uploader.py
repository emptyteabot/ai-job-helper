"""
用户上传简历功能 - 支持PDF、Word、文本格式
"""

import os
from typing import Optional
import PyPDF2
import docx

class ResumeUploader:
    """简历上传器 - 解析各种格式的简历"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt']
    
    def upload_resume(self, file_path: str) -> Optional[str]:
        """
        上传并解析简历
        
        Args:
            file_path: 简历文件路径
        
        Returns:
            简历文本内容，如果失败返回None
        """
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.supported_formats:
            print(f"❌ 不支持的文件格式: {file_ext}")
            print(f"支持的格式: {', '.join(self.supported_formats)}")
            return None
        
        try:
            if file_ext == '.pdf':
                return self._parse_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif file_ext == '.txt':
                return self._parse_txt(file_path)
        except Exception as e:
            print(f"❌ 解析文件失败: {str(e)}")
            return None
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text.strip()
    
    def _parse_docx(self, file_path: str) -> str:
        """解析Word文件"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    
    def _parse_txt(self, file_path: str) -> str:
        """解析文本文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    
    def save_resume(self, content: str, output_path: str = "my_resume.txt"):
        """保存简历到文本文件"""
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"✅ 简历已保存到: {output_path}")


# 快速测试
if __name__ == "__main__":
    uploader = ResumeUploader()
    
    # 创建示例简历
    sample_resume = """
姓名：张三
学历：本科 - 计算机科学
工作经验：3年Python开发
技能：Python, Django, MySQL, Redis
求职意向：后端开发工程师
"""
    
    uploader.save_resume(sample_resume, "示例简历.txt")
    
    # 测试上传
    content = uploader.upload_resume("示例简历.txt")
    if content:
        print("\n✅ 简历上传成功！")
        print(content[:200])

