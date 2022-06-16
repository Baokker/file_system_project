import sys

# pyqt5
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QTextOption, QCursor
from PyQt5.QtCore import QRect, QModelIndex
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QHBoxLayout, \
    QPlainTextEdit, QMainWindow, QMessageBox, QInputDialog, QTreeView, QAbstractItemView, QMenu

from file_system_components import *

# QSS样式
from qt_material import apply_stylesheet

SYSTEM_INFO = "file_system_info"


class FileSystemUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_system = FileSystem(SYSTEM_INFO)
        self.cur_path = []
        self.cur_selected_file = None
        self.cur_selected_dir = None

        self.fake_root = FileTreeNode("", datetime.now())
        self.fake_root.tree_node_children.append(self.file_system.file_tree.root)
        self.setup_ui()

    def setup_ui(self):
        # 窗体信息
        self.resize(800, 600)
        self.setWindowTitle("文件系统模拟")
        self.setWindowIcon(QIcon('imgs/cover.png'))

        # 菜单栏
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("文件")
        fileMenu.addAction(QIcon('imgs/format.png'), "格式化", self.format)
        fileMenu.addAction(QIcon('imgs/save.png'), "保存", self.save)

        createMenu = menuBar.addMenu("创建")
        createMenu.addAction(QIcon('imgs/create_file.png'), "创建文件", self.create_file)
        createMenu.addAction(QIcon('imgs/create_dir.png'), "创建文件夹", self.create_dir)

        deleteMenu = menuBar.addMenu("删除")
        deleteMenu.addAction(QIcon('imgs/delete_file.png'), "删除文件", self.delete_file)
        deleteMenu.addAction(QIcon('imgs/delete_dir.png'), "删除文件夹", self.delete_dir)

        renameMenu = menuBar.addMenu("重命名")
        renameMenu.addAction(QIcon('imgs/rename.png'), "重命名文件", self.rename_file)
        renameMenu.addAction(QIcon('imgs/rename.png'), "重命名文件夹", self.rename_dir)

        infoMenu = menuBar.addMenu('说明')
        infoMenu.addAction(QIcon('imgs/about.png'), "关于..", self.about)
        infoMenu.addAction(QIcon('imgs/tutorial.png'), "用法", self.tutorial)

        # 设置layout
        widget = QWidget()
        v1 = QVBoxLayout()
        widget.setLayout(v1)
        self.setCentralWidget(widget)

        # 上方路径栏
        self.path_label = QLabel(" > ".join(self.cur_path))
        self.update_path_label()
        v1.addWidget(self.path_label)

        # 左侧文件树
        self.treeView = QTreeView()
        self.update_file_tree_model()
        self.treeView.expandAll()

        h1 = QHBoxLayout()
        h1.addWidget(self.treeView)
        v1.addLayout(h1)

        # 右侧文件内容展示
        # 标签
        label = QLabel("当前打开文件内容")
        label.setAlignment(QtCore.Qt.AlignCenter)
        # 文本编辑框
        self.text_edit = QPlainTextEdit()
        self.text_edit.setWordWrapMode(QTextOption.WrapAnywhere)
        # 保存按钮
        self.save_button = QPushButton("save")
        self.save_button.clicked.connect(self.save_file)

        v2 = QVBoxLayout()
        v2.addWidget(label)
        v2.addWidget(self.text_edit)
        v2.addWidget(self.save_button)
        h1.addLayout(v2)

        # 底部文件/文件夹信息
        self.footer = QLabel()
        v1.addWidget(self.footer)

    # 鼠标点击左侧条目时，更新选中的文件夹/文件，同时更新各部分组件
    def click_item(self, cur: QModelIndex, pre: QModelIndex):
        reverse_cur_path = []
        file_order = cur.row()  # 保存原有文件位置索引

        while cur.data() is not None:
            reverse_cur_path.append(cur.data())
            cur = cur.parent()

        self.cur_path = list(reversed(reverse_cur_path))

        # update selected file
        cursor = self.fake_root  # 类似虚拟头结点 以便遍历到对应文件夹
        for i in range(len(self.cur_path) - 1):
            cursor = next((x for x in cursor.tree_node_children if x.dir_name == self.cur_path[i]))

        # 最后一项可能是文件夹或文件 通过索引判断 位置在前为文件 在后为文件夹
        if len(cursor.tree_node_children) - 1 < file_order:
            self.cur_selected_file = cursor.leaf_node_children[file_order - len(cursor.tree_node_children)]
            print("file ", self.cur_selected_file.file_name)
            self.cur_selected_dir = cursor  # 同时获得所在文件夹
        else:
            self.cur_selected_dir = cursor.tree_node_children[file_order]
            print("dir ", self.cur_selected_dir.dir_name)
            self.cur_selected_file = None

        # update path label
        self.update_path_label()
        # update footer
        self.update_footer()
        # text edit
        self.update_text_edit()

        # set button enable
        if self.cur_selected_file is not None:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

    # 构建tree model所需函数
    def __append_items_recursively(self, model, file_tree_node: FileTreeNode):
        for node in file_tree_node.tree_node_children:
            child_item = QStandardItem(node.dir_name)
            self.__append_items_recursively(child_item, node)
            model.appendRow(child_item)
        for leaf_node in file_tree_node.leaf_node_children:
            model.appendRow(QStandardItem(leaf_node.file_name))

    # 构建tree model
    def build_file_tree_model(self) -> QStandardItemModel:
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['名称'])
        root_item = QStandardItem(self.file_system.file_tree.root.dir_name)
        model.appendRow(root_item)
        self.__append_items_recursively(root_item, self.file_system.file_tree.root)
        return model

    # 更新所有部件
    def update_all_components(self):
        self.update_file_tree_model()
        self.update_footer()
        self.update_path_label()
        self.update_text_edit()

    def update_file_tree_model(self):
        self.treeView.setModel(self.build_file_tree_model())
        self.treeView.expandAll()
        # 增加点击事件
        self.treeView.selectionModel().currentChanged.connect(self.click_item)
        # 增加右击点击事件
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.right_click_item)
        # 设为不可更改
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 鼠标滚轮
        self.treeView.header().setStretchLastSection(True)
        self.treeView.horizontalScrollBar().setEnabled(True)
        self.treeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.treeView.verticalScrollBar().setEnabled(True)
        self.treeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

    def update_path_label(self):
        self.path_label.setText(" > ".join(self.cur_path))

    def update_text_edit(self):
        if self.cur_selected_file is not None:
            self.text_edit.setEnabled(True)
            self.text_edit.setPlainText(self.file_system.open_and_read_file(self.cur_selected_file))
        else:
            self.text_edit.setPlainText("尚未在左侧选中文件")
            self.text_edit.setEnabled(False)

    def update_footer(self):
        if self.cur_selected_dir is not None:
            self.footer.setText("(selected dir) " + self.cur_selected_dir.dir_name + "   |   contains " + str(
                self.cur_selected_dir.size()) + " items\n" +
                                "created in " + str(self.cur_selected_dir.create_time) + ", modified in " + str(
                self.cur_selected_dir.modify_time))
            if self.cur_selected_file is not None:
                self.footer.setText(self.footer.text() +
                                    "\n(selected file) " + self.cur_selected_file.file_name + "   |   length: " + str(
                    self.cur_selected_file.length) + "\n" +
                                    "created in " + str(self.cur_selected_file.create_time) + ", modified in " + str(
                    self.cur_selected_file.modify_time))
        else:
            self.footer.setText("not selected")

    def save_file(self):
        data = self.file_system.open_and_read_file(self.cur_selected_file)

        if self.text_edit.toPlainText() == data:
            QMessageBox.warning(self, "警告", "无任何变动！")
            return

        ans = QMessageBox.question(self, '确认', "是否保存？", QMessageBox.Yes | QMessageBox.No)

        if ans == QMessageBox.Yes:
            self.file_system.write_and_close_file(self.text_edit.toPlainText(), self.cur_selected_file)
            self.update_footer()

    # 右键点击，同时会触发click item
    # 增加右键菜单 根据选中文件或文件夹 跳出不同选项
    def right_click_item(self):
        if self.cur_selected_dir is None and self.cur_selected_file is None:
            return

        right_click_menu = QMenu()
        if self.cur_selected_file is not None:
            right_click_menu.addAction(QIcon('imgs/delete_file.png'), "删除文件", self.delete_file)
            right_click_menu.addAction(QIcon('imgs/rename.png'), "重命名文件", self.rename_file)
        elif self.cur_selected_dir is not None:
            right_click_menu.addAction(QIcon('imgs/create_file.png'), "创建文件", self.create_file)
            right_click_menu.addAction(QIcon('imgs/create_dir.png'), "创建文件夹", self.create_dir)
            right_click_menu.addAction(QIcon('imgs/rename.png'), "重命名文件夹", self.rename_dir)
            right_click_menu.addAction(QIcon('imgs/delete_dir.png'), "删除文件夹", self.delete_dir)

        right_click_menu.exec_(QCursor.pos())
        right_click_menu.show()

    # 关于
    def about(self):
        QMessageBox.about(self, '关于', '本项目为2022年操作系统课程第三次作业文件管理系统项目\n'
                                      '作者：2052329 方必诚\n'
                                      '指导老师：王冬青')

    # 说明
    def tutorial(self):
        QMessageBox.about(self, '教程', '上方菜单栏可进行文件/文件夹操作\n'
                                      '左侧文件树可左键选中/右键操作\n'
                                      '右侧显示选中文件内容，点击save可保存')

    # 格式化
    def format(self):
        ans = QMessageBox.question(self, '确认', "是否格式化？", QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.file_system.format()
            self.cur_selected_file = None
            self.cur_selected_dir = self.file_system.file_tree.root
            self.cur_path = [self.cur_selected_dir.dir_name]
            self.update_all_components()

    def save(self):
        ans = QMessageBox.question(self, '确认', "保存到本地文件？", QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.file_system.save(SYSTEM_INFO)

    def create_file(self):
        new_file_name, ok = QInputDialog.getText(self, '创建文件', '输入创建文件名：')
        if ok:
            if new_file_name == "":
                QMessageBox.warning(self, "警告", "文件名为空！")
            elif self.cur_selected_dir is None:
                QMessageBox.warning(self, "警告", "请先在左侧选中创建文件所在的文件夹！")
            elif len([x for x in self.cur_selected_dir.leaf_node_children if x.file_name == new_file_name]) > 0:
                QMessageBox.warning(self, "警告", "已有重复文件名！")
            else:
                self.file_system.create_file(new_file_name, self.cur_selected_dir)
                self.update_file_tree_model()
                self.update_all_components()

    def create_dir(self):
        new_dir_name, ok = QInputDialog.getText(self, '创建文件夹', '输入创建文件夹名：')
        if ok:
            if new_dir_name == "":
                QMessageBox.warning(self, "警告", "文件夹名为空！")
            elif self.cur_selected_dir is None:
                QMessageBox.warning(self, "警告", "请先在左侧选中创建文件夹所在的文件夹！")
            elif len([x for x in self.cur_selected_dir.tree_node_children if x.dir_name == new_dir_name]) > 0:
                QMessageBox.warning(self, "警告", "已有重复文件夹名！")
            else:
                self.file_system.create_dir(self.cur_selected_dir, new_dir_name, datetime.now())
                self.update_all_components()

    def delete_file(self):
        if self.cur_selected_file is None:
            QMessageBox.warning(self, "警告", "请先在左侧选中删除的文件！")
        else:
            ans = QMessageBox.question(self, '确认', "删除" + self.cur_selected_file.file_name + "？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans == QMessageBox.Yes:
                self.file_system.delete_file(self.cur_selected_file)
                self.cur_selected_file = None
                self.update_all_components()

    def delete_dir(self):
        if self.cur_selected_dir is None:
            QMessageBox.warning(self, "警告", "请先在左侧选中删除的文件夹！")
        elif self.cur_selected_dir == self.file_system.file_tree.root:
            QMessageBox.warning(self, "警告", "根文件夹不可删除！")
        else:
            ans = QMessageBox.question(self, '确认', "删除" + self.cur_selected_dir.dir_name + "？",
                                       QMessageBox.Yes | QMessageBox.No)
            if ans == QMessageBox.Yes:
                self.file_system.delete_dir(self.cur_selected_dir)
                self.cur_selected_dir = None
                self.cur_selected_file = None
                self.update_all_components()

    def rename_file(self):
        if self.cur_selected_file is None:
            QMessageBox.warning(self, "警告", "请先在左侧选中重命名的文件！")
        else:
            new_file_name, ok = QInputDialog.getText(self, '重命名文件', '输入新文件名：')
            if ok:
                if new_file_name == "":
                    QMessageBox.warning(self, "警告", "文件名为空！")
                elif len([x for x in self.cur_selected_dir.leaf_node_children if x.file_name == new_file_name]) > 0:
                    QMessageBox.warning(self, "警告", "已有重复文件名！")
                else:
                    self.file_system.rename_file(self.cur_selected_file, new_file_name, self.cur_selected_dir)
                    self.update_all_components()

    def rename_dir(self):
        if self.cur_selected_dir is None:
            QMessageBox.warning(self, "警告", "请先在左侧选中重命名的文件夹！")
        else:
            new_dir_name, ok = QInputDialog.getText(self, '重命名文件夹', '输入新文件夹名：')
            if ok:
                if new_dir_name == "":
                    QMessageBox.warning(self, "警告", "文件夹名为空！")
                elif len([x for x in self.cur_selected_dir.tree_node_children if x.dir_name == new_dir_name]) > 0:
                    QMessageBox.warning(self, "警告", "已有重复文件夹名！")
                else:
                    self.file_system.rename_dir(self.cur_selected_dir, new_dir_name)
                    self.update_all_components()

    # 关闭窗口时弹出确认消息
    def closeEvent(self, event):
        self.save()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    u = FileSystemUI()

    # setup stylesheet
    apply_stylesheet(app, theme='dark_pink.xml')

    u.show()
    sys.exit(app.exec_())
