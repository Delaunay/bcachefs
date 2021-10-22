from bcachefs import Bcachefs


class BcacheFSDataset:
    def __init__(self, path) -> None:
        self.image = Bcachefs(path)
        self.files = []
        self._build_index()

    def _build_index(self):
        for name in self.image.namelist():
            result = self.filter(name)

            if result:
                self.files.append(result)

    def filter(self, name):
        """Used to filter files inside the archives we are interested in
        
        Parameters
        ----------
        name: str
            full path to a file in the archive
        
        Returns
        -------
        the data that will passed along to `load`

        """
        dirent = self.image.find_dirent(name)

        if dirent.is_file:
            return name
        
        return None

    def load(self, name, *args):
        """Load a sample"""
        with self.image.open(name, 'r') as data:
            return data.read()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.image.close()

    def close(self):
        self.image.close()

    def __getitem__(self, index):
        data = self.load(*self.files[index])
        return data

    def __len__(self):
        return len(self.files)
