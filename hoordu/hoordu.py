from .config import get_logger
from . import models
from .util import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import shutil
import pathlib

class hoordu(object):
    def __init__(self, config):
        self.config = config
        self.logger = get_logger('hoordu', self.config.get('logto'))
        self.engine = create_engine(self.config.database, echo=self.config.get('debug', False))
        self._Session = sessionmaker(bind=self.engine)
        self.session = self._Session()
        
        self.filespath = '{}/files'.format(self.config.base_path)
        self.thumbspath = '{}/thumbs'.format(self.config.base_path)
    
    def create_all(self):
        models.Base.metadata.create_all(self.engine)
    
    def register_service(self, name):
        service = self.session.query(models.Service).filter(models.Service.name==name).one_or_none()
        
        if service is not None:
            return service
            
        else:
            service = models.Service(name=name, version=0)
            self.add(service)
            self.flush()
            return service
    
    def add(self, *args):
        return self.session.add_all(args)
    
    def flush(self):
        return self.session.flush()
    
    def commit(self):
        return self.session.commit()
    
    def import_file(self, file, orig=None, thumb=None, move=False):
        mvfun = shutil.move if move else shutil.copy
        
        if orig is not None:
            file.hash = md5(orig)
            file.mime = mime_from_file(orig)
            file.ext = ''.join(pathlib.Path(orig).suffixes)[1:]
        
        dst, tdst = self._get_file_paths(file)
        
        if orig is not None:
            pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
            mvfun(orig, dst)
            file.file_present = True
        
        if thumb is not None:
            pathlib.Path(tdst).parent.mkdir(parents=True, exist_ok=True)
            mvfun(thumb, tdst)
            file.thumb_present = True
    
    def _file_slot(self, file):
        return file.id // self.config.files_slot_size
    
    def _get_file_paths(self, file):
        file_slot = self._file_slot(file)
        
        if file.ext:
            filepath = '{}/{}/{}'.format(self.filespath, file_slot, file.id)
        else:
            filepath = '{}/{}/{}'.format(self.filespath, file_slot, file.id)
        
        thumbpath = '{}/{}/{}.jpg'.format(self.thumbspath, file_slot, file.id)
        
        return filepath, thumbpath
