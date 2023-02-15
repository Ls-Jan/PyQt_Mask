

import sys
from PyQt5.QtGui import QPainter,QPen,QColor,QPixmap,QBrush,QBitmap
from PyQt5.QtCore import Qt,QRect,QPoint,pyqtSignal
from PyQt5.QtWidgets import QApplication,QWidget

import win32gui as WGui
import win32con as WCon


class XJ_Mask(QWidget):#遮罩，右键双击固定遮罩，调用Set_Floating恢复遮罩的
    arg_borderWidth=2#边界粗细
    arg_borderMargin=4#边界的探测宽度(用于鼠标对边界的检测
    arg_borderColor=QColor(0,255,255)#边界颜色
    arg_maskColor=QColor(0,0,0,0)#遮罩颜色
    arg_shadowColor=QColor(0,0,0,1)#阴影颜色
    signal_fix=pyqtSignal()#当遮罩固定时触发
    signal_move=pyqtSignal()#当遮罩移动时触发

    def __init__(self,parent=None):
        super().__init__(parent)
        self.__anchor=''#离鼠标最近的边界
        self.__rect=QRect(0,0,0,0)#遮罩坐标
        self.__clickPos=None#鼠标点击时的位置(QPoint)，用于拖拽(该值为空时说明未点中遮罩，不进行拖拽行为
        self.__clickRect=[0,0,0,0]#鼠标点击时的遮罩坐标(LTRB)，用于拖拽
        self.__steerable=False#遮罩是否可动/非固定
        self.__range=None#遮罩选取范围

        self.setAttribute(Qt.WA_TranslucentBackground, True)#透明背景。该属性要和Qt.FramelessWindowHint配合使用，单独用的话不生效
        self.Set_Floating(False)
        # self.setAttribute(Qt.WA_DeleteOnClose)#无用的俩属性
        # self.setAttribute(Qt.WA_QuitOnClose)
    # def __del__(self):#Debug，判断是否顺利析构
    #     print("Del_Mask")

    def Set_Floating(self,flag):#设置遮罩是否浮动(浮动时可修改位置)
        #鼠标穿透需要顺序执行语句(Qt日常发癫)：https://blog.csdn.net/hellokandy/article/details/125898007
        #日常迷惑之：先设置属性Attribute后设置窗口标志WindowFlags才能使属性生效(至少点击穿透是如此)，而且还得提前把窗口标志清掉，莫名其妙。而且这还是文档没写的哦，还是自己试出来的呢(笑)
        self.__steerable=flag
        # winFlags=Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint|Qt.ToolTip#窗口置顶+窗体无边界+去除任务栏图标
        winFlags=Qt.FramelessWindowHint|Qt.ToolTip#窗体无边界+去除任务栏图标
        #又一个奇怪的点：即使不使用Qt.WindowStaysOnTopHint，只靠上面俩属性，也能使窗口处于置顶状态
        #但只要调用一下self.lower()那么置顶效果立马清除(并且只能使用Qt.WindowStaysOnTopHint重新恢复置顶效果)
        self.setMouseTracking(flag)#时刻捕捉鼠标移动/不捕捉鼠标移动
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_TransparentForMouseEvents,not flag)#撤销点击穿透/点击穿透
        self.setWindowFlags(winFlags)
        self.show()
        if(not flag):
            self.signal_fix.emit()

    def Set_MaskRange(self,L,T,R,B):#设置遮罩选取范围
        self.__range=QRect(L,T,R-L+1,B-T+1)

    def Set_MaskPos(self,L,T,R,B):#调整遮罩位置
        if(L<R and T<B):
            dL,dT=self.pos().x(),self.pos().y()
            rect=QRect(L-dL,T-dT,R-L+1,B-T+1)
            if(rect!=self.__rect):#减少不必要的性能影响
                self.__rect=self.__GetLimitRect(rect,self.__range)
                self.update()
                self.signal_move.emit()
                return True
        return False


    def Get_MaskRange(self):#获取遮罩选取范围(QRect/None)
        return self.__range

    def Get_MaskPos(self):#返回遮罩位置(QRect)
        L,T=self.pos().x(),self.pos().y()
        rect=self.__rect
        return QRect(L+rect.left(),T+rect.top(),rect.width(),rect.height())

    def Get_Floating(self):#判断遮罩是否浮动
        return self.__steerable


    def Opt_ClearMaskRange(self):#清除遮罩拖拽范围
        self.__range=None

    def Opt_Raise(self,topMost=True):#窗口置顶(topMost为真则保持置顶)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint,True)
        WGui.SetWindowPos(self.winId(),WCon.HWND_TOPMOST,0,0,0,0,WCon.SWP_NOMOVE | WCon.SWP_NOSIZE | WCon.SWP_FRAMECHANGED | WCon.SWP_NOACTIVATE)
        if(not topMost):
            WGui.SetWindowPos(self.winId(),WCon.HWND_NOTOPMOST,0,0,0,0,WCon.SWP_NOMOVE | WCon.SWP_NOSIZE | WCon.SWP_FRAMECHANGED | WCon.SWP_NOACTIVATE)#HWND_NOTOPMOST取消当前的置顶效果，不影响窗口位置
        self.show()

    def Opt_RaiseAfter(self,hwnd):#窗口置于指定窗口下方
        try:
            WGui.SetWindowPos(self.winId(),hwnd,0,0,0,0,WCon.SWP_NOMOVE | WCon.SWP_NOSIZE | WCon.SWP_NOACTIVATE | WCon.SWP_FRAMECHANGED)
            WGui.SetWindowPos(self.winId(),WCon.HWND_NOTOPMOST,0,0,0,0,WCon.SWP_NOMOVE | WCon.SWP_NOSIZE | WCon.SWP_FRAMECHANGED | WCon.SWP_NOACTIVATE)#HWND_NOTOPMOST取消当前的置顶效果，不影响窗口位置
            self.show()
        except Exception as e:#抓异常是因为，一旦hwnd是任务管理器的窗口，那么就会报错。。错误是“pywintypes.error: (5, 'SetWindowPos', '拒绝访问。')”
            # print('>>>',e)
            pass

    def Opt_MaximumArea(self):#将遮罩显示范围最大化，一般不需要调用。不设置为私有仅仅以防万一
        #多屏的分辨率信息：https://blog.csdn.net/ieeso/article/details/93717182
        desktop = QApplication.desktop()
        L,T,R,B=0,0,0,0
        for i in range(desktop.screenCount()):
            rect=desktop.screenGeometry(i)
            rL,rT,rR,rB=self.__GetLTRB(rect)
            if(L>rL):
                L=rL
            if(R<rR):
                R=rR
            if(T>rT):
                T=rT
            if(B<rB):
                B=rB
        self.setGeometry(L+1,T+1,R-L,B-T)#留1像素，因为有些(例如我)会设置“隐藏任务栏”，留这一丝距离以保障鼠标贴近屏幕边界时任务栏能够出现


    def showEvent(self,event):
        self.Opt_MaximumArea()
        
    def paintEvent(self,event):
        rect=self.__rect
        if(self.arg_shadowColor.alpha()!=0):#如果不用绘制阴影的话就减少这部分代码开销
            pix=QPixmap(self.width(),self.height())#预先绘制到QPixmap对象(内存)，然后再绘制到屏幕上
            pix.fill(self.arg_shadowColor)
            mask=QBitmap(self.width(),self.height())#蒙版

            pmask=QPainter(mask)
            mask.fill(Qt.black)#黑色为绘制区
            pmask.eraseRect(rect)#擦除绘制区
            pmask.end()
            pix.setMask(mask)#设置蒙版
            
            pself=QPainter(self)
            pself.drawPixmap(0,0,pix)
            pself.end()

        pself=QPainter(self)
        pself.fillRect(self.__rect,self.arg_maskColor)#画遮罩
        if(self.__steerable):#画周边
            pself.setPen(QPen(QColor(0,0,0,1),(self.arg_borderWidth+self.arg_borderMargin)<<1))#增大鼠标对边沿的检测范围
            pself.drawRect(self.__rect)
            pself.setPen(QPen(self.arg_borderColor,self.arg_borderWidth))
            pself.drawRect(self.__rect)
        pself.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:#按下左键，拖拽
            if(self.__anchor):#非空串
                self.__clickPos=event.pos()
                self.__clickRect=self.__GetLTRB(self.__rect)
            else:
                self.__clickPos=None

    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.RightButton:#双击右键固定遮罩位置
            self.Set_Floating(False)

    def mouseMoveEvent(self,event):
        pos=event.pos()
        anchor=self.__anchor
        if(event.buttons() & Qt.LeftButton):#左键拖拽
            if(self.__clickPos):
                pos=self.__GetLimitPoint(pos,self.__range)#将pos约束于范围内
                flag_inner=len(anchor)==4#在矩形内部
                dx=pos.x()-self.__clickPos.x()
                dy=pos.y()-self.__clickPos.y()
                L,T,R,B=self.__clickRect

                if(anchor.find('L')!=-1):#移动左边界
                    L=L+dx
                if(anchor.find('R')!=-1):#移动右边界
                    R=R+dx
                if(anchor.find('T')!=-1):#移动上边界
                    T=T+dy
                if(anchor.find('B')!=-1):#移动下边界
                    B=B+dy

                if(not flag_inner):#在边界角点上
                    if(L>R):
                        L,R=R,L
                        if(anchor.find('L')!=-1):
                            anchor=anchor.replace('L','R')
                        else:
                            anchor=anchor.replace('R','L')
                    if(T>B):
                        T,B=B,T
                        if(anchor.find('T')!=-1):
                            anchor=anchor.replace('T','B')
                        else:
                            anchor=anchor.replace('B','T')

                self.__rect=self.__GetLimitRect(QRect(L,T,R-L+1,B-T+1),self.__range,flag_inner)
            self.signal_move.emit()
        else:
            self.__anchor=self.__GetNearestBorder(pos)
        self.__SetCursor(anchor)
        self.update()

    def closeEvent(self,event):#来一拳。因为这种无边框窗口的关闭事件并不会通知到消息循环系统中，从而导致该窗口关闭后程序还卡在消息循环中没退出的情况发生
        if(not self.parent()):#尽管这样，还是不够完美，还是出现乱打拳的情况
            exit()


    def __GetNearestBorder(self,pos):#判断距离最近的边，有效结果8种(均为字串)，对应四边和四角：L、T、R、B、LT、LB、RT、RB。无效结果2种，LTRB说明鼠标在矩形内部，空串说明鼠标在矩形外
        rst=''

        rect=self.__rect
        if(rect):
            L=rect.left()
            T=rect.top()
            R=rect.right()
            B=rect.bottom()

            x=pos.x()
            y=pos.y()

            DL=abs(L-x)
            DR=abs(R-x)
            DT=abs(T-y)
            DB=abs(B-y)

            m=self.arg_borderWidth+self.arg_borderMargin+5
            MidX=L-m<x<R+m
            MidY=T-m<y<B+m

            if(DL<m or DR<m):
                if(MidY):
                    rst=rst+('L' if DL<DR else 'R')
            if(DT<m or DB<m):
                if(MidX):
                    rst=rst+('T' if DT<DB else 'B')
            if(len(rst)==0):
                if(MidX and MidY):
                    rst='LTRB'
        return rst

    def __SetCursor(self,anchor):#根据anchor设置光标
        if(len(anchor)>2):
            self.setCursor(Qt.SizeAllCursor)
        elif(len(anchor)>1):
            if(anchor=='LT' or anchor=='RB'):
                self.setCursor(Qt.SizeFDiagCursor)#左上右下
            else:
                self.setCursor(Qt.SizeBDiagCursor)#右上左下
        elif(len(anchor)>0):
            if(anchor=='L' or anchor=='R'):
                self.setCursor(Qt.SizeHorCursor)#左右
            else:
                self.setCursor(Qt.SizeVerCursor)#上下
        else:
            self.setCursor(Qt.ArrowCursor)

    def __GetLTRB(self,rect:QRect):#返回rect的左上右下的值
        return rect.left(),rect.top(),rect.right(),rect.bottom()

    def __GetLimitRect(self,rect:QRect,range:QRect,fixed=True):#约束矩形于范围内。fixed为真则尽可能不变动rect的大小
        if(type(range)==QRect and range.isValid()):
            L,T,R,B=self.__GetLTRB(rect)
            W,H=R-L,B-T
            rL,rT,rR,rB=self.__GetLTRB(range)
            fL,fR,fT,fB=(False,)*4

            if(L<rL):
                L=rL
                fL=True
            if(T<rT):
                T=rT
                fT=True
            if(R>rR):
                R=rR
                fR=True
            if(B>rB):
                B=rB
                fB=True
            if(fixed):
                if(fL ^ fR):
                    if(fL):
                        R=L+W
                    else:
                        L=R-W
                if(fT ^ fB):
                    if(fT):
                        B=T+H
                    else:
                        T=B-H

            rect=QRect(L,T,R-L+1,B-T+1)
        return rect

    def __GetLimitPoint(self,pos:QPoint,range:QRect):#约束点于范围内
        x,y=pos.x(),pos.y()
        if(range):
            L,T,R,B=self.__GetLTRB(range)
            if(x<L):
                x=L
            elif(x>R):
                x=R
            if(y<T):
                y=T
            elif(y>B):
                y=B
        return QPoint(x,y)

if __name__=='__main__':
    app = QApplication(sys.argv)
    w=QWidget()
    w.show()
    # mk= XJ_Mask(w)
    mk= XJ_Mask()
    mk.Set_MaskPos(500,500,800,800)
    mk.arg_borderColor=QColor(0,255,255)
    mk.arg_maskColor=QColor(255,0,0,64)
    mk.arg_shadowColor=QColor(0,0,0,128)
    # mk.arg_shadowColor=QColor(0,0,0,255)
    # mk.arg_shadowColor=QColor(0,0,0,0)
    mk.Set_Floating(True)
    mk.show()
    mk.signal_move.connect(lambda:print(mk.Get_MaskPos()))
    mk.signal_fix.connect(lambda:print('Fix'))
    mk.Opt_Raise(False)
    mk.Set_MaskRange(500,500,1000,1000)


    # mk.lower()
    # from time import sleep
    # sleep(2)
    # mk.raise_()

    sys.exit(app.exec())



if __name__=='__mains__':
    app = QApplication(sys.argv)

    from PyQt5.QtCore import QTimer
    import XJ_Screen 

    mk= XJ_Mask()
    mk.Set_MaskPos(500,500,800,800)
    mk.Set_MaskPos(500,500,20,20)
    mk.arg_borderColor=QColor(0,255,255)
    mk.arg_maskColor=QColor(255,0,0,64)
    mk.arg_shadowColor=QColor(0,0,0,128)

    def Func():
        hwnd=XJ_Screen.Get_WinHandle_Cursor(True)
        rect=mk.geometry()
        if(mk.isVisible()):
            print('Hide',hwnd)
            mk.hide()
        else:
            print('Show',hwnd)
            mk.Opt_RaiseAfter(hwnd)
            # mk.Opt_Raise(False)
            # mk.Opt_Raise(True)
    timer=QTimer()
    timer.timeout.connect(Func)
    timer.start(1000)
    sys.exit(app.exec())



if __name__=='__mains__':
    app = QApplication(sys.argv)

    from PyQt5.QtCore import QTimer
    import XJ_Screen 

    mk= XJ_Mask()
    mk.Set_MaskPos(500,500,800,800)
    mk.arg_borderColor=QColor(0,255,255)
    mk.arg_maskColor=QColor(255,0,0,64)
    mk.arg_shadowColor=QColor(0,0,0,128)

    def Func():
        hwnd=XJ_Screen.Get_WinHandle_Cursor(True)
        rect=mk.geometry()
        if(mk.isVisible()):
            print('Hide',hwnd)
            mk.hide()
        else:
            print('Show',hwnd)
            mk.Opt_Raise(False)
            # mk.Opt_Raise(True)
    timer=QTimer()
    timer.timeout.connect(Func)
    timer.start(1000)
    sys.exit(app.exec())
























