
#使用swig(Windows)工具：https://blog.csdn.net/qq_40088639/article/details/116980025
#安装PyHook3：https://blog.csdn.net/NANGE007/article/details/120048842
#使用PyHook3(个人文章)：https://blog.csdn.net/weixin_44733774/article/details/128379683



import win32gui as WG
import win32api as WA
import win32con as WC
from PyQt5.QtWidgets import QApplication,QWidget
from PyQt5.QtGui import QColor,QPixmap,QBitmap,QPainter,QPen
from PyQt5.QtCore import pyqtSignal,Qt,QRect

from PyHook3 import HookManager#挂钩
from PyHook3 import HookConstants#挂钩事件(枚举)
from threading import Thread#信号量、线程
import sys
from time import sleep
import XJ_GUI


__all__=['XJ_ScreenShot']
class XJ_ScreenShot(QWidget):#抓屏器(参考V信截图
    signal_finish=pyqtSignal(tuple)#槽信号，当完成选取时调用。返回4-tuple，是矩形的LTWH(实际坐标)
    arg_color_shadow=QColor(0,0,0,128)#阴影颜色
    arg_color_inner=QColor(255,0,0,16)#矩形颜色
    arg_color_border=QColor(255,0,0,128)#边界颜色
    arg_width_border=2#边界粗细
    arg_allowDrag=False#拖拽选取，该值为真则鼠标拖拽选取，否则始终选取鼠标指着的窗口

    __rate=1#屏幕分辨率比率(物理:逻辑)
    __tid=0#子线程ID
    __mousePos=None#鼠标按下时的坐标位置
    __rect=None#绘制的矩形
    __img=None#底片
    __signal_start=pyqtSignal()#不能使用threading.Thread创建线程
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground, True)#透明背景。该属性要和Qt.FramelessWindowHint配合使用，单独用的话不生效
        self.setAttribute(Qt.WA_TransparentForMouseEvents,True)#点击穿透
        self.setWindowFlags(Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint|Qt.ToolTip)#窗口置顶+窗体无边界+去除任务栏图标
        self.__signal_start.connect(self.__ThreadProc)
        
    def Opt_Start(self,screenImg=None):#开始裁剪。screenImg为裁剪过程中的底片(QPixmap对象，默认为空/透明)，传入整个屏幕的截图使截图过程中的屏幕保持不变(甚至提前往screenImg加入水印)
        if(self.__tid):#防止频繁调用
            return
        self.Opt_MaximumArea()
        self.__rate=XJ_GUI.Get_ScreenRatio()
        self.__img=screenImg
        self.__rect=None
        self.show()
        self.__signal_start.emit()

    def Opt_MaximumArea(self):#将遮罩显示范围最大化，一般不需要调用。不设置为私有仅仅以防万一
        #有Qt版的获取多屏分辨率信息的方法：https://blog.csdn.net/ieeso/article/details/93717182
        #只不过我这里没必要用。
        rect=XJ_GUI.Get_ScreenPos()
        rate=XJ_GUI.Get_ScreenRatio()
        L,T,W,H=[int(r*rate) for r in rect]
        self.setGeometry(L+1,T+1,W,H)#留1像素，因为有些(例如我)会设置“隐藏任务栏”，留这一丝距离以保障鼠标贴近屏幕边界时任务栏能够出现



    def paintEvent(self,event):
        rect=self.__rect
        pix=QPixmap(self.width(),self.height())#预先绘制到QPixmap对象(内存)，然后再绘制到屏幕上
        mask=QBitmap(self.width(),self.height())#蒙版

        pix.fill(self.arg_color_shadow)#阴影颜色
        pmask=QPainter(mask)
        mask.fill(Qt.black)#黑色为绘制区
        if(rect):
            pmask.eraseRect(rect)#擦除绘制区
        pmask.end()
        pix.setMask(mask)#设置蒙版
        pself=QPainter(self)
        if(self.__img):#绘制底片
            pself.drawPixmap(0,0,self.__img)
        pself.drawPixmap(0,0,pix)#画矩形外阴影
        if(rect):#画矩形和矩形边界
            pself.fillRect(rect,self.arg_color_inner)
            pself.setPen(QPen(self.arg_color_border,self.arg_width_border))#绘制边界
            pself.drawRect(rect)
        pself.end()

    def __Update(self,posA,posB):#重绘，posA和posB为矩形对角角点。posA和posB中有一个值无效时，或是self.__allowDrag为假，矩形将以__GetWinRect为准
        if(not posA or not posB or not self.arg_allowDrag):#其中任有一值无效
            L,T,R,B=XJ_GUI.Get_WinMsg(XJ_GUI.Get_WinHandle_Cursor())[1]
        else:
            L,R=sorted([posA[0],posB[0]])
            T,B=sorted([posA[1],posB[1]])
        L,T,R,B=self.__ResizeRect((L,T,R,B))#约束窗口位置
        W=R-L+1
        H=B-T+1
        
        pos=self.pos()
        rect=QRect(L-pos.x()+1,T-pos.y()+1,W,H)
        if(self.__rect!=rect):#减少频繁的update带来的严重卡顿问题
            self.__rect=rect
            self.update()

    def __ThreadProc(self):#给线程运行的函数
        if(self.__tid):
            return
        self.__tid=WA.GetCurrentThreadId()
        self.__mousePos=None
        hm=HookManager()
        hm.MouseAll = self.__OnMouseEvent#设置挂钩函数
        hm.HookMouse()#启动挂钩
        WG.PumpMessages()#进入消息循环，直到self.__OnMouseEvent调用WG.PostThreadMessage(tid,WC.WM_QUIT,0,0)
        hm.UnhookMouse()#关闭挂钩
        self.__tid=0

    def __OnMouseEvent(self,event):#与鼠标挂钩关联的函数
        # print(event.Position)
        if(event.Message==HookConstants.WM_LBUTTONDOWN):#左键按下
            self.__mousePos=event.Position
        elif(event.Message==HookConstants.WM_LBUTTONUP):#左键松开(结束截屏)
            WG.PostThreadMessage(self.__tid,WC.WM_QUIT,0,0)
            sleep(0.01)#休眠极小一段时间，规避一个鼠标过快移动时触发的奇怪的bug：UpdateLayeredWindowIndirect failed for ptDst=(*,*), size=(*x*), dirty=(*x* *, *) (无效的窗口句柄。)
            self.signal_finish.emit(self.__rect.getRect() if(self.__rect) else tuple())
        elif(event.Message==HookConstants.WM_RBUTTONDOWN):#右键按下(无视)
            pass
        elif(event.Message==HookConstants.WM_RBUTTONUP):#右键抬起(取消截屏)
            WG.PostThreadMessage(self.__tid,WC.WM_QUIT,0,0)
            self.signal_finish.emit(tuple())
        else:#鼠标移动，或是其他情况
            self.__Update(self.__mousePos,event.Position)
            # WA.SetCursorPos(event.Position)
            return True
        return False

    def __ResizeRect(self,rect):#将矩形(LTRB)限制在屏幕内。返回的是新矩形(LTRB)
        pos=self.geometry()
        L,T,R,B=rect
        rL,rT,rR,rB=pos.left(),pos.top(),pos.right(),pos.bottom()
        L=max(L,rL)
        R=min(R,rR)
        T=max(T,rT)
        B=min(B,rB)
        return L,T,R,B
        




if __name__=='__main__':
    from PyQt5.QtWidgets import QPushButton
    rect=XJ_GUI.Get_ScreenPos()
    rate=XJ_GUI.Get_ScreenRatio()
    rect=[int(r*rate) for r in rect]

    app = QApplication(sys.argv)
    ss=XJ_ScreenShot()
    ss.arg_allowDrag=True
    ss.arg_color_inner=QColor(255,0,0,16)
    ss.signal_finish.connect(lambda rect:print(rect) or ss.hide())
    # ss.signal_finish.connect(lambda rect:print(rect))

    w=QWidget()
    w.show()
    b=QPushButton("测试",w)
    b.clicked.connect(lambda:ss.Opt_Start())
    # b.clicked.connect(lambda:ss.Opt_Start(QPixmap(XJ_GUI.Get_Screenshot(*rect))))
    b.show()

    app.exec()







