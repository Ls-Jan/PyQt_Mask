
import sys
from PyQt5.QtWidgets import QApplication,QWidget,QTableWidget,QListWidget,QPushButton
from PyQt5.QtWidgets import QAbstractItemView,QHeaderView,QSplitter,QHBoxLayout,QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from XJ_MaskSeries import *
from XJ_ScreenShot import *


class Main(QWidget):
    __screenShot=None#XJ_ScreenShot，用于截取屏幕选定遮罩区域
    __widLst_type=None#QListWidget，类型选择列表
    __widTbl_floating=None#QTableWidget，浮动型Mask
    __widTbl_following=None#QTableWidget，追随型Mask
    __keywords={
        'valid':' 启用 ',
        'pos':' 位置 ',
        'color':' 颜色 ',
        'alpha':' 透明度 ',
        'remove':' 移除 ',
        'pid':' PID ',
        'title':' 窗口标题 ',
    }
    __header={
        XJ_MaskSeries_Floating:['valid','remove','pos','color','alpha'],
        XJ_MaskSeries_Following:['valid','remove','pid','title','pos','color','alpha'],
    }
    __maskLsts={}#为了顺利析构关闭mask
    def __init__(self):
        super().__init__()
        self.__screenShot=XJ_ScreenShot()
        self.__widLst_type=QListWidget(self)
        self.__widTbl_floating=QTableWidget(self)
        self.__widTbl_following=QTableWidget(self)
        self.__maskLsts={self.__widTbl_floating:[],self.__widTbl_following:[]}

        #设置self.__screenShot
        self.__screenShot.signal_finish.connect(self.__AddMask)
        #设置self.__widLst_type
        self.__Init_WidLst(self.__widLst_type)
        #设置self.__widTbl_floating
        self.__Init_WidTbl(self.__widTbl_floating,XJ_MaskSeries_Floating)
        #设置self.__widTbl_following
        self.__Init_WidTbl(self.__widTbl_following,XJ_MaskSeries_Following)
        #显示表格(默认浮动型)
        self.__widTbl_following.hide()
        self.__widLst_type.setCurrentRow(0)
        #设置布局与样式
        self.__Init_Layout()
        self.__Init_Style()

    def __Init_WidLst(self,wid):
        wid.addItem('浮动型Mask')
        wid.addItem('追随型Mask')
        wid.setMinimumWidth(120)#避免过窄
        wid.mouseDoubleClickEvent=wid.mousePressEvent#双击触发切换
        wid.mousePressEvent=lambda event:None#屏蔽单击
        wid.currentRowChanged.connect(self.__ChangeMaskType)

    def __Init_WidTbl(self,wid,maskType):
        headerLst=self.__header[maskType]
        wid.setColumnCount(len(headerLst))
        wid.setHorizontalHeaderLabels([self.__keywords[key] for key in headerLst])
        wid.verticalHeader().hide()  # 隐藏行首
        wid.setEditTriggers(QAbstractItemView.NoEditTriggers)    # 设置tablewidget不可编辑
        wid.setSelectionMode(QAbstractItemView.NoSelection)      # 设置tablewidget不可选中
        wid.setSelectionBehavior(QAbstractItemView.SelectRows)   # 设置行选中
        wid.setSelectionMode(QAbstractItemView.SingleSelection)  # 设置行选中

        #调整列宽
        header=wid.horizontalHeader()
        wid.resizeColumnsToContents()
        for key in headerLst:
            mode=QHeaderView.Interactive#默认模式
            if(key in {'valid','remove','color'}):#固定列宽
                mode=QHeaderView.Fixed
            elif(key in {'pos','pid','title'}):#自适应列宽
                mode=QHeaderView.ResizeToContents
            elif(key in {'alpha'}):#自动拉伸
                mode=QHeaderView.Stretch
            header.setSectionResizeMode(headerLst.index(key),mode)
        
        vbox=QVBoxLayout()
        btn=QPushButton('添加')
        vbox.addStretch(1)
        vbox.addWidget(btn)
        hbox=QHBoxLayout(wid)
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        btn.clicked.connect(self.__SelectMaskPos)

    def __Init_Layout(self):#设置布局
        spt=QSplitter(Qt.Horizontal,self)
        spt.addWidget(self.__widLst_type)
        spt.addWidget(self.__widTbl_floating)
        spt.addWidget(self.__widTbl_following)
        spt.setStretchFactor(0,1)
        spt.setStretchFactor(1,9)
        spt.setStretchFactor(2,9)
        hbox=QHBoxLayout(self)
        hbox.addWidget(spt)

    def __Init_Style(self):#设置样式
        #背景为黑
        #字体为黄
        self.setStyleSheet(
        '''
            QHeaderView::section{
                background-color:rgb(24,24,24);
            }
            QWidget{
                background-color:rgb(24,24,24);
                color:rgb(240,240,0);
            }
        ''')

    def __ChangeMaskType(self,num):#切换当前Mask类型
        if(num==0):
            self.__widTbl_floating.show()
            self.__widTbl_following.hide()
        elif(num==1):
            self.__widTbl_floating.hide()
            self.__widTbl_following.show()

    def __SelectMaskPos(self):#选取遮罩位置
        widTbl=self.sender().parent()
        self.__screenShot.arg_allowDrag= widTbl is self.__widTbl_floating
        self.__screenShot.Opt_Start()        

    def __AddMask(self,rect):#添加遮罩
        self.__screenShot.hide()
        if(rect):
            if(self.__widTbl_floating.isVisible()):
                widTbl=self.__widTbl_floating
                maskType=XJ_MaskSeries_Floating
            else:
                widTbl=self.__widTbl_following
                maskType=XJ_MaskSeries_Following

            rect=[rect[i]+(rect[i-2] if i>=2 else 0) for i in range(4)]
            row=widTbl.rowCount()
            widTbl.setRowCount(row+1)
            XJ_MaskSeries=maskType(self,rect)
            header=self.__header[maskType]
            for pst in range(len(header)):
                #嘛，没办法，特事特办，既然没办法居中，那索性全给我居中(哪里有“特”了，明明都是“普”
                #样例：https://blog.51cto.com/u_15246509/5147236
                key=header[pst]
                wid=eval(f'XJ_MaskSeries.wid_{key}')
                cell=QWidget(widTbl)
                box=QHBoxLayout(cell)
                box.setContentsMargins(0,0,0,0)
                box.setAlignment(Qt.AlignCenter)
                box.addWidget(wid)
                widTbl.setCellWidget(row,pst,cell)
            XJ_MaskSeries.wid_remove.clicked.connect(self.__RemoveMask)
            self.__maskLsts[widTbl].append(XJ_MaskSeries)

    def __RemoveMask(self):#移除遮罩
        btn=self.sender()
        if(btn):
            wid=btn.parent()
            cell=wid.parent()
            widTbl=cell.parent()
            index = widTbl.indexAt(wid.pos()).row() 
            widTbl.model().removeRow(index)
            self.__maskLsts[widTbl].pop(index)


from Resource import Resource#导入资源，用于打包时的整合。资源路径格式为":/..."

if __name__ == '__main__':
    app = QApplication(sys.argv)

    win=Main()
    win.show()
    win.setWindowTitle("简单遮罩")#设置窗口标题
    win.setWindowIcon(QIcon(':/logo.ico'))#设置图标
    # app.setWindowIcon(QIcon(':/logo.ico'))#设置图标
    win.resize(800,200)
    sys.exit(app.exec())


