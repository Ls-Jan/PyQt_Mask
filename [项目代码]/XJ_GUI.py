
import win32gui as WGui
import win32api as WApi
import win32print as WPrint
import win32process as WProc
import win32con as WCon
import win32ui as WUi

from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QImage
import numpy as np
import cv2

__all__=['Get_CursorPos','Get_ScreenPos','Get_ScreenRatio','Get_Screenshot','Get_WinMsg','Get_WinHandle_Active','Get_WinHandle_Active']

#GDI对象要及时释放(包括释放win32gui.GetDC(None)获取的上下文句柄)，避免造成严重的性能浪费：https://blog.csdn.net/youyudexiaowangzi/article/details/122002401

def Get_Screenshot(L:int,T:int,W:int,H:int):#传入实际坐标截取屏幕，支持跨屏。返回QImage对象。
    """
        Get Screenshot by physical position.
        Be careful, it will conflict with PyHook3 when using the GUI of PyQt5.
        ->Input:<int>,<int>,<int>,<int>
        ->Return:<PyQt5.QtGui.QImage>
    """

    #使用win32API进行截图
    hdc = WGui.GetDC(None)#屏幕设备的上下文句柄。h-Handle
    cdc = WUi.CreateDCFromHandle(hdc)#PyCDC对象。c-MFC
    mdc = cdc.CreateCompatibleDC()#PyCDC对象，之后将以该对象为准进行操作。m-Memory
    img = WUi.CreateBitmap()#PyCBitmap对象，屏幕数据将保存到此

    #截图，数据保存至img中
    img.CreateCompatibleBitmap(cdc, W, H)#初始化对象(申请内存空间)，关联cdc对象
    mdc.SelectObject(img)#设置操作对象
    mdc.BitBlt((0, 0), (W, H), cdc, (L,T), WCon.SRCCOPY)#复制数据(截屏)

    #PyCBitmap对象转np数组：https://blog.csdn.net/wwf1093996635/article/details/109127759
    data=np.frombuffer(QByteArray(img.GetBitmapBits(True)), dtype='uint8')#转为np数组
    data.shape = (H,W,4)#修改维度

    #np数组转QPixmap对象：https://blog.csdn.net/weixin_44431795/article/details/122016214
    data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
    img=QImage(data, data.shape[1], data.shape[0], data.shape[1]*3,QImage.Format_RGB888)

    #释放资源
    #cdc和mdc不需要显式调用DelectDC，它们在析构时会自动释放占用的资源：http://www.markjour.com/docs/pywin32-docs/PyCDC__DeleteDC_meth.html
    WGui.DeleteDC(hdc)
    return img  

def Get_CursorPos():#获取鼠标位置(逻辑坐标)
    """
        Get Cursor Position
        ->Return:(<int>,<int>)
    """
    return WApi.GetCursorPos()

def Get_ScreenRatio():#获取屏幕分辨率比率(实际:逻辑)：https://blog.csdn.net/frostime/article/details/104798061
    """
        Get physical/logical of the screen size.
        ->Return:<float>
    """
    hdc=WGui.GetDC(None)
    LSize=[WApi.GetSystemMetrics(0),WApi.GetSystemMetrics(1)]#L-Logical
    PSize=[WPrint.GetDeviceCaps(hdc, WCon.DESKTOPHORZRES),WPrint.GetDeviceCaps(hdc, WCon.DESKTOPVERTRES)]#P-Physical
    WGui.DeleteDC(hdc)
    return PSize[0]/LSize[0]#计算比率

def Get_ScreenPos(i=-1):#获取第i个屏幕的位置(逻辑坐标：左上宽高)，如果i不存在则返回None。特别的，i为-1则返回整体(所有屏幕组合成的一个大矩形)的位置
    """
        Return Specified Screen Logical Position(L,T,W,H).
        If given i is invalid then return Zero.
        Specially , it will return Combined Screen Logical Position(L,T,W,H) if i equal -1.
        ->Input:<int>
        ->Return:(<int>,<int>,<int>,<int>)
    """
    lst=[msg[2] for msg in WApi.EnumDisplayMonitors(None, None)]#各个屏幕的位置信息(逻辑坐标)
    L,T,R,B=0,0,0,0
    if(0<=i<len(lst)):
        return lst[i]
    elif(i==-1):
        for rect in lst:
            L=min(rect[0],L)
            T=min(rect[1],T)
            R=max(rect[0]+rect[2],R)
            B=max(rect[1]+rect[3],B)
    return (L,T,R-L,B-T)

def Get_WinHandle_Active():#获取当前活跃窗口的句柄
    """
        Get Handle from the window which is active.
        ->Return:<int>
    """
    return WGui.GetForegroundWindow()

def Get_WinHandle_Cursor(rootWin:bool=False):#获取当前鼠标对应窗口的窗口句柄
    """
        Get Handle from the window which is under the mouse cursor.
        If given argument 'rootWin' is True then return the root window's handle.
        ->Input:<bool>
        ->Return:<int>
    """
    point=WApi.GetCursorPos()
    hwnd=WGui.WindowFromPoint(point)
    if(rootWin):
        h=hwnd
        while(h):
            hwnd=h
            h=WGui.GetParent(h)
    return hwnd

def Get_WinMsg(hwnd:int):#获取窗口句柄对应窗口的信息。信息依次是标题、窗口位置(逻辑坐标:左上右下)、PID。注意窗口位置可能超过实际显示范围
    """
        Get [ title , logicalPosition(L,T,R,B) , PID ] from hwnd.
        If given hwnd is invalid then return None.
        The window position maybe be out of place.
        ->Input:<int>
        ->Return:(<string>,(<int>,<int>,<int>,<int>),<int>)
    """
    if(WGui.IsWindow(hwnd)):
        rect=WGui.GetWindowRect(hwnd)
        title=WGui.GetWindowText(hwnd)
        pid=WProc.GetWindowThreadProcessId(hwnd)[1]
        return title,rect,pid
    return None

def Get_WinVisible(rect:tuple,screen:int=-1):#判断窗口坐标(逻辑坐标)在对应屏幕中是否可见，i为-1则判断所有屏幕
    """
        Indicates if the window positoin(LTWH)(logical) is visible in assigned screen.
        If given 'screen' is -1 then assigned all screens.
        ->Input:(<int>,<int>,<int>,<int>),<int>
        ->Return:<bool>
    """
    L,T,W,H=rect
    R=L+W
    B=T+H

    lst=[msg[2] for msg in WApi.EnumDisplayMonitors(None, None)]#各个屏幕的位置信息(逻辑坐标)
    if(0<=screen<len(lst)):
        lst=[lst[screen]]
    elif(screen!=-1):
        lst=[]
    for S_LTWH in lst:#S-Screen
        SL,ST,SW,SH=S_LTWH
        SR=SL+SW
        SB=ST+SH
        if(not (R<SL or L>SR) and not (B<ST or T>SB)):
            return True
    return False






if __name__=='__main__':
    rate=Get_ScreenRatio()

    # hwnd=Get_WinHandle_Active()
    hwnd=Get_WinHandle_Cursor(True)
    from time import sleep,time
    # sleep(1)
    rect=Get_WinMsg(hwnd)[1]
    print('Visible:',Get_WinVisible(rect))
    rect=[int(r*rate) for r in rect]
    print('Position:',rect)
    print('Hwnd:',hwnd)

    # WGui.ShowWindow(hwnd,WCon.SW_HIDE)
    # WGui.ShowWindow(hwnd,WCon.SW_SHOW)
    # WGui.ShowWindow(65096,WCon.SW_SHOW)

    rect=Get_ScreenPos()
    rect=[int(r*rate) for r in rect]
    print('ScreenPos:',rect)
    img=Get_Screenshot(*rect)
    img.save("Screenshot.png")



