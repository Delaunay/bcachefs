from bcachefs import Bcachefs

from PIL import Image, ImageFile
from torch.utils.data.dataset import Dataset


class BcacheFSDataset(Dataset):
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


def pil_loader(file_object):
    img = Image.open(file_object, 'r')
    img = img.convert('RGB')
    return img


class BCHImageNet(BcacheFSDataset):
    def __init__(self, path, transforms) -> None:
        self.classes = dict()
        self.transforms = transforms
        super().__init__(path)
        
    def filter(self, name):
        dirent = self.image.find_dirent(name)

        if dirent.is_dir:
            return None
        try:
            filename = name.split('/')[-1]
            class_, _ = filename.split('_')

            class_idx = self.classes.get(class_)

            if class_idx is None:
                class_idx = len(self.classes)
                self.classes[class_] = class_idx
            
            return name, class_idx
        except:
            return None

    def load(self, name, class_):
        print(name)
        with self.image.open(name, 'r') as file:
            image = pil_loader(file)

        return self.transforms(image), class_


if __name__ == '__main__':
    import os

    this = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(this, ".."))

    def filepath(path):
        return os.path.join(project_root, path)
        
    MINI = "testdata/mini_bcachefs.img"

    from torch.utils.data import DataLoader
    from torchvision import transforms

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    with BCHImageNet(filepath(MINI), preprocess) as dataset:
        print(len(dataset))

        loader = DataLoader(dataset, batch_size=4, num_workers=4)

        for batch in loader:
            print(batch)
