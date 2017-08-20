from os import walk
from os.path import join
from zipfile import ZipFile

from .core import Package


class ZipPackage(Package):
    """A Zip File package"""

    def __init__(self, ref=None, callback=None, cache=None, env=None):

        super(ZipPackage, self).__init__(ref, callback=callback, cache=cache, env=env)

    def save_path(self, path=None):
        base = self.doc.find_first_value('Root.Name') + '.zip'

        if path and not path.endswith('.zip'):
            return join(path, base)
        elif path:
            return path
        else:
            return base

    def _init_zf(self, path):



        self.zf = ZipFile(self.save_path(path), 'w')

    def save(self, path=None):

        self.check_is_ready()

        root_dir = self.doc.find_first_value('Root.Name')

        self._init_zf(path)

        for root, dirs, files in walk(self.source_dir):
            for f in files:
                source = join(root, f)
                rel = source.replace(self.source_dir,'').strip('/')
                dest = join(root_dir, rel)

                self.zf.write(source,dest)

        self.zf.close()

        return self.save_path(path)