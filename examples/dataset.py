from bcachefs.dataset import BcacheFSDataset
from PIL import Image, ImageFile


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

    from torch.utils.data import DataLoader
    from torchvision import transforms

    from bcachefs.testing import filepath

    MINI = "testdata/mini_bcachefs.img"

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
