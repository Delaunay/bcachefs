import os

import pytest
import multiprocessing as mp

import bcachefs.bcachefs as bchfs
from bcachefs import Bcachefs
from bcachefs.testing import filepath


MINI = "testdata/mini_bcachefs.img"

TEST_IMAGES = [MINI]


@pytest.mark.parametrize("image", TEST_IMAGES)
def test___enter__(image):
    image = filepath(image)
    assert os.path.exists(image)

    fs = Bcachefs(image)
    assert fs.closed
    assert fs.size == 0
    with fs:
        assert not fs.closed
        assert fs.size > 0

    assert fs.closed
    assert fs.size == 0

    del fs
    with Bcachefs(image) as fs:
        assert not fs.closed
        assert fs.size > 0


@pytest.mark.parametrize("image", TEST_IMAGES)
def test___iter__(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        assert sorted([ent.name for ent in fs]) == [
            "dir",
            "file1",
            "file2",
            "lost+found",
            "n02033041",
            "n02033041_3834.JPEG",
            "n02445715",
            "n02445715_16523.JPEG",
            "n04467665",
            "n04467665_63788.JPEG",
            "n04584207",
            "n04584207_7936.JPEG",
            "n09332890",
            "n09332890_29876.JPEG",
            "subdir",
        ]


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_find_dirent(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        dirent = fs.find_dirent("/")
        assert dirent.parent_inode == 0
        assert dirent.inode == 4096
        assert dirent.type == bchfs.DIR_TYPE
        assert dirent.name == "/"
        assert dirent == bchfs.ROOT_DIRENT

        dir_dirent = fs.find_dirent("/dir")
        assert dir_dirent.parent_inode == bchfs.ROOT_DIRENT.inode
        assert dir_dirent.type == bchfs.DIR_TYPE
        assert dir_dirent.name == "dir"

        subdir_dirent = fs.find_dirent("/dir/subdir")
        assert subdir_dirent.parent_inode == dir_dirent.inode
        assert subdir_dirent.type == bchfs.DIR_TYPE
        assert subdir_dirent.name == "subdir"


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_ls(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        ls = [e.name for e in fs.ls()]
        ls.sort()
        assert ls == [
            "dir",
            "file1",
            "lost+found",
            "n02033041",
            "n02445715",
            "n04467665",
            "n04584207",
            "n09332890",
        ]
        ls = [e.name for e in fs.ls("/dir")]
        assert ls == ["subdir"]
        ls = [e.name for e in fs.ls("/n04467665")]
        assert ls == ["n04467665_63788.JPEG"]


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_read_file(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        inode = fs.find_dirent("file1").inode
        assert bytes(fs.read_file(inode)) == b"File content 1\n"

        inode = fs.find_dirent("dir/subdir/file2").inode
        assert fs.read_file(inode) == b"File content 2\n"
        assert bytes(fs.read_file("dir/subdir/file2")) == b"File content 2\n"


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_file_size(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        inode = fs.find_dirent("file1").inode

        file_size = fs._inode_map.get(inode)
        assert file_size, "file inode should be present"

        extents = fs._extents_map[inode]
        size_check = 0
        for extent in extents:
            size_check += extent.size

        assert (
            size_check - 1 == file_size
        ), "sum of extends is equal to file_size (minus the null character)"


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_walk(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        subdir_walk = list(fs.walk("dir/subdir"))
        assert len(subdir_walk) == 1

        subdir_dirpath, subdir_dirnames, subdir_filenames = subdir_walk[0]
        subdir_filenames = [f.name for f in subdir_filenames]
        assert len(subdir_dirnames) == 0
        assert subdir_filenames == ["file2"]

        dir_walk = list(fs.walk("dir"))
        dir_dirpath, dir_dirnames, dir_filenames = dir_walk[0]
        dir_dirnames = [d.name for d in dir_dirnames]
        assert dir_dirnames == ["subdir"]
        assert len(dir_filenames) == 0

        assert dir_walk[1] == subdir_walk[0]


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_cursor___iter__(image):
    image = filepath(image)
    assert os.path.exists(image)
    with Bcachefs(image) as fs, Bcachefs(image).cd() as cursor:
        assert sorted([ent.name for ent in cursor]) == sorted(
            [ent.name for ent in fs]
        )
        cursor.cd("dir")
        assert sorted([ent.name for ent in cursor]) == ["file2", "subdir"]


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_cursor_cd(image):
    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image).cd() as cursor:
        assert cursor.pwd == "/"
        cursor.cd("dir/subdir")
        assert cursor.pwd == "/dir/subdir"
        cursor.cd("..")
        assert cursor.pwd == "/dir"
        cursor.cd("/dir/subdir")
        assert cursor.pwd == "/dir/subdir"
        cursor.cd("../..")
        assert cursor.pwd == "/"


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_cursor_find_dirent(image):
    image = filepath(image)
    assert os.path.exists(image)
    with Bcachefs(image) as fs, Bcachefs(image).cd() as cursor:
        cursor.cd("dir/subdir")
        assert cursor.find_dirent("file2") == fs.find_dirent("dir/subdir/file2")


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_cursor_ls(image):
    image = filepath(image)
    assert os.path.exists(image)
    with Bcachefs(image) as fs, Bcachefs(image).cd() as cursor:
        cursor.cd("dir/subdir")
        assert cursor.ls() == fs.ls("dir/subdir")
        cursor.cd()
        assert cursor.ls() == fs.ls()


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_cursor_walk(image):
    image = filepath(image)
    assert os.path.exists(image)
    with Bcachefs(image) as fs, Bcachefs(image).cd() as cursor:
        cursor.cd("dir")
        assert list(cursor.walk("subdir")) == list(fs.walk("/dir/subdir"))


def test_namelist():
    image = filepath(MINI)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        assert fs.namelist() == [
            "file1",
            "n09332890/n09332890_29876.JPEG",
            "dir/subdir/file2",
            "n04467665/n04467665_63788.JPEG",
            "n02033041/n02033041_3834.JPEG",
            "n02445715/n02445715_16523.JPEG",
            "n04584207/n04584207_7936.JPEG",
        ]


def count_size(fs, name):
    import coverage

    coverage.process_startup()

    with fs:

        try:
            with fs.open(name, "rb") as f:
                return len(f.read())
        except FileNotFoundError:
            return 0


@pytest.mark.parametrize("image", TEST_IMAGES)
def test_multiprocess(image):

    image = filepath(image)
    assert os.path.exists(image)

    with Bcachefs(image) as fs:
        files = fs.namelist()

        with mp.Pool(4) as p:
            sizes = p.starmap(count_size, [(fs, n) for n in files])

    assert sum(sizes) > 1
