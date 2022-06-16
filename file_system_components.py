import pickle
from datetime import datetime
from bitarray import bitarray

BLOCK_NUM = 2 ** 10  # 块数
BLOCK_SIZE = 4  # 每块的大小

FAT_FREE = -2  # 表示FAT表中此块未被使用
FAT_END = -1  # 表示为FAT表中链表结尾

SPACE_OCCUPY = 1  # 磁盘被占用
SPACE_FREE = 0  # 未被占用


class FCB:
    def __init__(self, file_name, create_time, length, start_address=None):
        self.file_name = file_name
        self.create_time = create_time
        self.modify_time = create_time
        self.length = length
        self.start_address = start_address


class FAT:
    def __init__(self):
        self.block_num = BLOCK_NUM
        self.table = []
        for i in range(BLOCK_NUM):
            self.table.append(FAT_FREE)


# 磁盘
class Disk(list):
    def __init__(self):
        super(Disk, self).__init__()
        for i in range(BLOCK_NUM):
            self.append("")


# 空闲空间bitmap
class FreeSpace:
    def __init__(self):
        self.bitmap = bitarray(BLOCK_NUM)
        self.bitmap.setall(0)


# 多级目录中的文件夹结点
# 多级目录中 文件结点直接为FCB 且一定为叶节点
class FileTreeNode:  # dir
    def __init__(self, name: str, create_time):
        self.tree_node_children = []
        self.leaf_node_children = []
        self.dir_name = name
        self.create_time = create_time
        self.modify_time = create_time

    def size(self):
        return len(self.tree_node_children) + len(self.leaf_node_children)


class FileTree:
    def __init__(self):
        # 根目录为/
        self.root = FileTreeNode("/", datetime.now())


class FileSystem:
    def __init__(self, system_info_file=None):
        import os
        # 存在文件则直接读取
        if system_info_file and os.path.exists(system_info_file):
            with open(system_info_file, "rb") as f:
                self.file_tree = pickle.load(f)
                self.free_space = pickle.load(f)
                self.disk = pickle.load(f)
                self.fat = pickle.load(f)
        else: # 否则手动创建
            print("file loss")
            self.file_tree = FileTree()
            self.free_space = FreeSpace()
            self.disk = Disk()
            self.fat = FAT()
            self.create_dir(self.file_tree.root, "文件夹1", datetime.now())
            self.create_dir(self.file_tree.root.tree_node_children[0], "文件夹2", datetime.now())
            self.create_dir(self.file_tree.root.tree_node_children[0].tree_node_children[0], "文件夹3", datetime.now())
            self.create_file("文件1", self.file_tree.root)
            self.create_file("文件2", self.file_tree.root.tree_node_children[0])
            self.create_file("文件3", self.file_tree.root.tree_node_children[0])

    # 找到并返回空闲空间的index
    def find_free_index(self):
        # 0 -> free
        return self.free_space.bitmap.find(0)

    def create_dir(self, file_tree_node: FileTreeNode, name, create_time):
        for node in file_tree_node.tree_node_children:
            if node.dir_name == name:
                print("dir name exists")
                return

        file_tree_node.tree_node_children.append(FileTreeNode(name, create_time))
        file_tree_node.modify_time = create_time

    # 清空文件夹内全部内容
    def __clear_dir(self, node: FileTreeNode):
        for leaf in node.leaf_node_children:
            self.delete_file(leaf)
        for dir in node.tree_node_children:
            self.__clear_dir(dir)

    def delete_dir(self, delete_node: FileTreeNode):
        self.__clear_dir(delete_node)
        # 广度优先删除
        cursor = self.file_tree.root
        queue = [cursor]
        while delete_node not in cursor.tree_node_children and queue != []:
            cursor = queue.pop(0)
            queue.extend(cursor.tree_node_children)
        cursor.tree_node_children.remove(delete_node)

    def rename_dir(self, file_tree_node: FileTreeNode, new_name):
        file_tree_node.dir_name = new_name
        file_tree_node.modify_time = datetime.now() # 修改时间变更

    def create_file(self, name, file_tree_node: FileTreeNode):
        if name not in file_tree_node.leaf_node_children:
            file_tree_node.leaf_node_children.append(FCB(name, datetime.now(), 0))

    def rename_file(self, fcb: FCB, new_name: str, parent_node: FileTreeNode):
        fcb.file_name = new_name
        fcb.modify_time = datetime.now()
        parent_node.modify_time = datetime.now()

    # 打开并读取返回文件数据
    def open_and_read_file(self, fcb: FCB):
        if fcb.start_address is None:
            return ""
        cursor = fcb.start_address
        data = ""
        while cursor != FAT_END:
            data += self.disk[cursor]
            cursor = self.fat.table[cursor]
        return data

    # 写入并保存数据
    def write_and_close_file(self, data, fcb: FCB):
        cur_index = FAT_END
        fcb.length = len(data)
        fcb.modify_time = datetime.now()

        while data != "":
            next_index = self.find_free_index()
            if next_index == -1:
                raise AssertionError("don't have enough space!!")
            if cur_index == FAT_END:
                fcb.start_address = next_index
            else:
                self.fat.table[cur_index] = next_index

            self.disk[next_index] = data[:BLOCK_SIZE]
            data = data[BLOCK_SIZE:]
            self.free_space.bitmap[next_index] = SPACE_OCCUPY

            cur_index = next_index
            self.fat.table[cur_index] = FAT_END

    def delete_file(self, fcb: FCB):
        cursor = fcb.start_address
        if cursor is not None:
            while cursor != FAT_END:
                self.disk[cursor] = ""
                self.free_space.bitmap[cursor] = SPACE_FREE

                next_position = self.fat.table[cursor]
                self.fat.table[cursor] = SPACE_FREE

                cursor = next_position

        self.__delete_file_recursively(fcb, self.file_tree.root)

    def __delete_file_recursively(self, fcb: FCB, file_tree_node: FileTreeNode):
        if fcb in file_tree_node.leaf_node_children:
            file_tree_node.leaf_node_children.remove(fcb)
            return
        else:
            for node in file_tree_node.tree_node_children:
                self.__delete_file_recursively(fcb, node)
    # 格式化
    def format(self):
        print("formatting..")
        self.file_tree.root.tree_node_children = []
        self.file_tree.root.leaf_node_children = []
        self.free_space = FreeSpace()
        self.disk = Disk()
        self.fat = FAT()

    def save(self, system_info_file: str):
        # save all data in local position
        print("saving")
        with open(system_info_file, "wb") as f:
            pickle.dump(self.file_tree, f)
            pickle.dump(self.free_space, f)
            pickle.dump(self.disk, f)
            pickle.dump(self.fat, f)
