from os import walk
from os.path import join
from zipfile import ZipFile
from metapack.util import slugify

from .core import PackageBuilder


class ZipPackageBuilder(PackageBuilder):
    """A Zip File package"""

    def __init__(self, source_ref=None, package_root=None,  callback=None, env=None):
        super().__init__(source_ref, package_root, callback, env)

        self.cache_path = self.package_name + ".zip"

        self.package_path = self.package_root.join(self.cache_path)


    def save(self, path=None):

        self.check_is_ready()

        root_dir = slugify(self.doc.find_first_value('Root.Name'))

        self.prt("Creating ZIP Package at '{}' from filesystem package at '{}'"
                 .format(self.package_path, self.source_dir))

        self.zf = ZipFile(self.package_path.path, 'w')


        for root, dirs, files in walk(self.source_dir):
            for f in files:
                source = join(root, f)
                rel = source.replace(self.source_dir,'').strip('/')
                dest = join(root_dir, rel)

                self.zf.write(source,dest)

        self.zf.close()

        return self.package_path