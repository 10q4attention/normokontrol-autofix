import os, glob
from datetime import datetime
from typing import Optional, Dict, List
from docx import Document


class StudentFolder:
    def __init__(self, path: str):
        self.path = path
        self.folder_name = os.path.basename(path)
        self.student_name = self._extract_name()
        self.latest_doc = self._find_latest()

    def _extract_name(self) -> str:
        if '_' in self.folder_name:
            return self.folder_name.split('_')[0]
        return self.folder_name

    def _find_latest(self) -> Optional[str]:
        docs = []
        for pat in ('*.docx', '*.doc'):
            docs.extend(glob.glob(os.path.join(self.path, pat)))
        if not docs:
            return None
        docs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return docs[0]

    def get_metadata(self) -> Dict:
        if not self.latest_doc:
            return {'exists': False, 'student_name': self.student_name, 'folder_path': self.path}
        st = os.stat(self.latest_doc)
        meta = {
            'exists': True,
            'student_name': self.student_name,
            'folder_path': self.path,
            'file_path': self.latest_doc,
            'file_name': os.path.basename(self.latest_doc),
            'file_size': st.st_size,
            'file_modified': datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'file_extension': os.path.splitext(self.latest_doc)[1],
        }
        try:
            if meta['file_extension'].lower() == '.docx':
                d = Document(self.latest_doc)
                c = d.core_properties
                meta['doc_author'] = c.author or 'Не указан'
                meta['doc_title'] = c.title or 'Не указан'
                meta['doc_pages'] = len(d.sections)
        except:
            pass
        return meta


class FileManager:
    def __init__(self, upload_dir: str = 'uploads'):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    def scan_folders(self, root: str) -> List[StudentFolder]:
        if not os.path.exists(root):
            return []
        folders = []
        for item in os.listdir(root):
            p = os.path.join(root, item)
            if os.path.isdir(p):
                folders.append(StudentFolder(p))
        folders.sort(key=lambda x: x.student_name)
        return folders