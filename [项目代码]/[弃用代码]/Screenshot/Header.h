#pragma once

//截取屏幕信息并转换为字节序(数组)，*data存放数组指针，返回值为数组长度。
//获取的图片数据将在下一次调用该函数时失效，多线程使用时请控制调用
int Screenshot(int L, int T, int R, int B, void** data);

