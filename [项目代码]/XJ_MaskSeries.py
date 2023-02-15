
import sys
from PyQt5.QtWidgets import QApplication,QWidget,QCheckBox,QLabel,QTableWidget,QPushButton,QHBoxLayout
from PyQt5.QtCore import Qt,QObject,QTimer

import XJ_GUI 
from XJ_Mask import *
from XJ_Slider import *
from XJ_ColorChoose import *


__all__=['XJ_MaskSeries_Floating','XJ_MaskSeries_Following']


class FlatButton(QLabel):#不过就是有点击事件的Label罢了。QPushButton设置成QLabel的样式是真的麻烦(而且我找不到)
    doubleClicked=pyqtSignal()#防止误触，使用双击触发事件
    def mouseDoubleClickEvent(self,event):
        self.doubleClicked.emit()



class XJ_MaskSeries_Base(QObject):#一份Mask(包含大量的控件)，继承QObject是为了蹭槽信号pyqtSignal
    validChange=pyqtSignal(bool)#槽信号，当启用框被点击时触发信号

    wid_valid=None#【Mask启用选择-QCheckBox】
    wid_pos=None#【Mask的位置-FlatButton】
    wid_color=None#【颜色-XJ_ColorChoose】
    wid_alpha=None#【透明度-XJ_Slider】
    wid_remove=None#【移除Mask-QPushButton】
    
    __mask=None#XJ_Mask
    def __init__(self,parent):#toTop为Mask的置顶。因为追随型窗口不需要置顶，只需要覆盖目标窗口上方即可
        super().__init__()
        self.wid_valid=QCheckBox(parent)
        self.wid_alpha=XJ_Slider_Horizon(parent)
        self.wid_color=XJ_ColorChoose(parent)
        self.wid_remove=QPushButton(parent)
        self.wid_pos=FlatButton(parent)
        self.__mask=XJ_Mask()#这里不加parent，要不然结束时无法顺利析构mask

        #设置复选框
        valid=self.wid_valid
        valid.setCheckState(Qt.Checked)#Qt.Unchecked
        valid.stateChanged.connect(self.CB_SetMaskVisible)
        #设置颜色按钮
        color=self.wid_color
        color.valueChanged.connect(self.CB_ColorChange)
        color.SetColor((0,0,0))
        #设置移除按钮
        remove=self.wid_remove
        remove.setIcon(QApplication.style().standardIcon(60))#Qt自带的ICON：https://blog.csdn.net/wh_19931117/article/details/80444107
        #设置滑动条
        slider=self.wid_alpha
        slider.valueChanged.connect(self.CB_AlphaChange)
        slider.setMaximum(100)
        slider.setMinimum(0)
        slider.setValue(50)
        #设置遮罩位置文本wid_pos
        pos=self.wid_pos
        pos.doubleClicked.connect(self.CB_FloatMask)
        #设置遮罩self.__mask
        __mask=self.__mask
        __mask.signal_fix.connect(self.CB_MaskFixed)
        __mask.signal_move.connect(self.CB_MaskMove)

    def Set_MaskPos(self,L,T,R,B):#调整遮罩位置
        self.__mask.Set_MaskPos(L,T,R,B)
        self.CB_MaskMove()
    def Set_MaskRange(self,range:list):#设置遮罩范围(LTRB)，为空则清除
        if(range):
            self.__mask.Set_MaskRange(*range)
        else:
            self.__mask.Opt_ClearMaskRange()

    #Opt为Operate或者Option的缩写，意为操作/选择
    def Opt_RaiseMask(self,topMost=False,belowActive=False):#belowActive为真时遮罩处于活跃窗口下方(并且topMost不生效)，belowActive为假则显示在最上方(此时toTop为True则遮罩恒置顶)
        self.__mask.Opt_Raise(topMost)
        if(belowActive):
            self.__mask.Opt_RaiseAfter(XJ_GUI.Get_WinHandle_Active())

    #CB为CallBack缩写
    def CB_AlphaChange(self,value:int):#滑动条变化时修改Mask透明度
        self.__mask.arg_maskColor.setAlpha((100-value)*255/100)
        self.__mask.update()
    def CB_ColorChange(self,value:tuple):#修改Mask颜色
        self.__mask.arg_maskColor=QColor(*value[:3],self.__mask.arg_maskColor.alpha())
        self.__mask.update()
    def CB_SetMaskVisible(self,flag:bool):#设置Mask是否可见
        if(flag):
            self.__mask.show()
        else:
            self.__mask.hide()
    def CB_FloatMask(self):#设置Mask为浮动状态，使其可调整位置
        self.__mask.Set_Floating(True)
    def CB_MaskFixed(self):#Mask固定时调用
        if(self.wid_valid.checkState()==Qt.Unchecked):
            self.__mask.hide()
    def CB_MaskMove(self):#Mask移动时调用，用于更新wid_pos值
        rect=self.__mask.Get_MaskPos()
        LTRB=[rect.left(),rect.top(),rect.right(),rect.bottom()]
        self.wid_pos.setText(str(LTRB))



class XJ_MaskSeries_Floating(XJ_MaskSeries_Base):#一份浮动的Mask(包含大量的控件)
    def __init__(self,parent,maskPos:tuple):#maskPos为4元组LTRB
        super().__init__(parent)
        self.Set_MaskPos(*maskPos)
        


class XJ_MaskSeries_Following(XJ_MaskSeries_Base):#一份追随窗口的Mask(包含大量的控件)
    wid_title=None#【进程名称-QLabel】
    wid_pid=None#【进程PID-QLabel】

    __offset=[0,0,0,0]#Mask的位置修正
    __timer=None#【定时器-QTimer】。刷新间隔为100ms
    __hwnd=None#窗口句柄
    __valid=True#窗口是否有效
    __active=True#窗口是否活跃
    __dot='<sup><font size=5 color=#EE0000>●</font></sup>'#红点样式
    def __init__(self,parent,__=None):#添加一个无效参数使得构造函数与XJ_MaskSeries_Floating一致
        super().__init__(parent)
        self.wid_title=QLabel(parent)
        self.wid_pid=QLabel(parent)
        self.__timer=QTimer(parent)
        self.__hwnd=XJ_GUI.Get_WinHandle_Cursor()
        self.__rootHwnd=XJ_GUI.Get_WinHandle_Cursor(True)
        #设置定时器__timer
        self.__timer.setInterval(100)
        self.__timer.timeout.connect(self.Opt_Update)
        self.__timer.start()

    #Opt为Operate或者Option的缩写，意为操作/选择
    def Opt_Update(self):#需要定时调用该函数以更新遮罩信息(供内部调用，外部不需要显式调用)
        msg=XJ_GUI.Get_WinMsg(self.__hwnd)
        if(msg):#窗口存在
            self.__valid=True
            self.wid_title.setText(str(msg[0]))
            self.wid_pid.setText(str(msg[2]))
            if(XJ_GUI.Get_WinVisible(msg[1])):#窗口可见
                rate=XJ_GUI.Get_ScreenRatio()#虽然不知道为什么，rate值居然为1而不是其他值，不管了
                W_LTRB=[int(r*rate) for r in msg[1]]#W-Window
                O_LTRB=self.__offset#O-Offset
                M_LTRB=[W_LTRB[i]+O_LTRB[i] for i in range(4)]#M-Mask
                self.Set_MaskPos(*M_LTRB)
                if(M_LTRB[0]<M_LTRB[2] and M_LTRB[1]<M_LTRB[3]):#遮罩有效
                    hwnd=XJ_GUI.Get_WinHandle_Active()
                    if(hwnd==self.__rootHwnd):#当前为活跃窗口
                        if(not self.__active):#从非活跃切换为活跃
                            self.__active=True
                            self.Opt_RaiseMask(topMost=True)
                    else:#当前不是活跃窗口
                        if(self.__active):#从活跃切换为非活跃
                            self.__active=False
                            self.Opt_RaiseMask(belowActive=True)
                    super().CB_SetMaskVisible(True)
                else:#遮罩无效(隐藏Mask并设置红点提示)
                    self.wid_pos.setText(self.wid_pos.text()+self.__dot)#添加红点
                    super().CB_SetMaskVisible(False)
            else:#窗口不可见(隐藏Mask)
                super().CB_SetMaskVisible(False)
        else:#窗口不存在(隐藏Mask并设置红点提示)
            if(self.__valid):
                self.wid_pid.setText(self.wid_pid.text()+self.__dot)#添加红点
                self.__valid=False
            super().CB_SetMaskVisible(False)

    #CB为CallBack缩写
    def CB_FloatMask(self):#设置Mask为浮动状态，同时暂停自动刷新
        self.__timer.stop()
        self.Set_MaskRange(XJ_GUI.Get_WinMsg(self.__hwnd)[1])
        super().CB_FloatMask()
    def CB_MaskFixed(self):#Mask固定时调用，同时更新wid_pos值
        M_LTRB=eval(self.wid_pos.text())
        W_LTRB=XJ_GUI.Get_WinMsg(self.__hwnd)[1]
        O_LTRB=[M_LTRB[i]-W_LTRB[i] for i in range(4)]
        self.__offset=O_LTRB
        self.Set_MaskRange(None)
        super().CB_MaskFixed()
        if(self.wid_valid.checkState()==Qt.Checked):
            self.__timer.start()
    def CB_SetMaskVisible(self,flag:bool):#设置Mask是否可见
        super().CB_SetMaskVisible(flag)
        if(flag):
            self.__timer.start()
        else:
            self.__timer.stop()





if __name__ == '__main__':
    app = QApplication(sys.argv)

    win=QWidget()
    hbox=QHBoxLayout(win)
    # ms=XJ_MaskSeries_Floating(None,(200,200,500,500))
    ms=XJ_MaskSeries_Following(None,(200,200,500,500))
    for key in dir(ms):
        if(key.find('wid_')==0):
            wid=eval(f'ms.{key}')
            hbox.addWidget(wid)
    win.show()

    sys.exit(app.exec())


