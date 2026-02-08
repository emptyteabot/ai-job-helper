"""
投递记录管理服务
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

class ApplicationRecordService:
    """投递记录服务"""
    
    def __init__(self, data_file: str = "data/applications.json"):
        self.data_file = data_file
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """确保数据文件存在"""
        os.makedirs(os.path.dirname(self.data_file) if os.path.dirname(self.data_file) else "data", exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def add_record(self, record: Dict[str, Any]) -> bool:
        """添加投递记录"""
        try:
            records = self.get_all_records()
            record['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records.append(record)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"添加记录失败: {e}")
            return False
    
    def get_all_records(self) -> List[Dict[str, Any]]:
        """获取所有投递记录"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def get_records_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态筛选记录"""
        records = self.get_all_records()
        return [r for r in records if r.get('status') == status]
    
    def update_status(self, application_id: str, new_status: str) -> bool:
        """更新投递状态"""
        try:
            records = self.get_all_records()
            for record in records:
                if record.get('application_id') == application_id:
                    record['status'] = new_status
                    record['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"更新状态失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取投递统计"""
        records = self.get_all_records()
        
        status_count = {}
        for record in records:
            status = record.get('status', '未知')
            status_count[status] = status_count.get(status, 0) + 1
        
        return {
            "total": len(records),
            "status_breakdown": status_count,
            "recent_applications": records[-10:] if len(records) > 10 else records
        }

