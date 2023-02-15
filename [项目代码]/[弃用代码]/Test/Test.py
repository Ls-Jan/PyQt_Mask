import numpy as np
from cv2 import cv2
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QByteArray


def Get_Screenshot(L:int,T:int,W:int,H:int):#传入实际坐标截取屏幕，支持跨屏。返回QImage对象。【需注意，需要DLL文件“Screenshot.dll”】
    """
        Get Screenshot by physical position.
        It need 'Screenshot.dll' .
        ->Input:<int>,<int>,<int>,<int>
        ->Return:<PyQt5.QtGui.QImage>
    """
    
    from ctypes import windll,pointer,c_void_p,string_at
    data=c_void_p()#截屏数据的指针
    size=windll.Screenshot.Screenshot(L,T,L+W-1,T+H-1,pointer(data))#Screenshot为自己写的DLL，用于截屏
    data=np.frombuffer(QByteArray(string_at(data,size)), dtype='uint8')#转为np数组
    data.shape = (H,W,4)#修改维度
    data=cv2.flip(data,0)#不知道为啥，图片是被翻转的(x轴)，于是就补转一次
    
    #np数组转QPixmap对象：https://blog.csdn.net/weixin_44431795/article/details/122016214
    data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
    img=QImage(data, data.shape[1], data.shape[0], data.shape[1]*3,QImage.Format_RGB888)
    return img


if __name__=='__main__':
	img=Get_Screenshot(-500,-500,1000,1000)
	img.save("Screenshot.png")

