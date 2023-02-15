
#include<Windows.h>

static HDC hdc;
static HDC hmdc;
static HANDLE hDIB;

//截屏代码示例：https://learn.microsoft.com/zh-cn/windows/win32/gdi/capturing-an-image#code-example
extern "C" _declspec (dllexport) int Screenshot(int L, int T, int R, int B, void** data) {
	int W = R - L + 1;
	int H = B - T + 1;

	HBITMAP hbmp;
	BITMAP bmp;
	hbmp = CreateCompatibleBitmap(hdc, W, H);
	SelectObject(hmdc, hbmp);
	BitBlt(hmdc, 0, 0, W, H,
		hdc, L, T,
		SRCCOPY);
	GetObject(hbmp, sizeof(BITMAP), &bmp);

	BITMAPINFOHEADER   bi;
	bi.biSize = sizeof(BITMAPINFOHEADER);
	bi.biWidth = bmp.bmWidth;
	bi.biHeight = bmp.bmHeight;
	bi.biPlanes = 1;
	bi.biBitCount = 32;
	bi.biCompression = BI_RGB;
	bi.biSizeImage = 0;
	bi.biXPelsPerMeter = 0;
	bi.biYPelsPerMeter = 0;
	bi.biClrUsed = 0;
	bi.biClrImportant = 0;

	// Add the size of the headers to the size of the bitmap to get the total file size.
	DWORD dwBmpSize = ((bmp.bmWidth * bi.biBitCount + 31) / 32) * 4 * bmp.bmHeight;
	if (hDIB) {
		// Unlock and Free the DIB from the heap.
		GlobalUnlock(hDIB);
		GlobalFree(hDIB);
	}
	// Starting with 32-bit Windows, GlobalAlloc and LocalAlloc are implemented as wrapper functions that 
	// call HeapAlloc using a handle to the process's default heap. Therefore, GlobalAlloc and LocalAlloc 
	// have greater overhead than HeapAlloc.
	hDIB = GlobalAlloc(GHND, dwBmpSize);
	*data = GlobalLock(hDIB);
	// Gets the "bits" from the bitmap, and copies them into a buffer 
	// that's pointed to by lpbitmap.
	GetDIBits(hdc, hbmp, 0,
		(UINT)bmp.bmHeight,
		*data,
		(BITMAPINFO*)&bi, DIB_RGB_COLORS);
	DeleteObject(hbmp);
	return dwBmpSize;

	{//这一段是保存为bmp的代码，用不上，注释了
		/*
		BITMAPFILEHEADER   bmfHeader;
		// Offset to where the actual bitmap bits start.
		bmfHeader.bfOffBits = (DWORD)sizeof(BITMAPFILEHEADER) + (DWORD)sizeof(BITMAPINFOHEADER);
		// Size of the file.
		bmfHeader.bfSize = dwBmpSize + sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);
		// bfType must always be BM for Bitmaps.
		bmfHeader.bfType = 0x4D42; // BM.

		// A file is created, this is where we will save the screen capture.
		HANDLE hFile = CreateFile(L"Screenshot.bmp",
			GENERIC_WRITE,
			0,
			NULL,
			CREATE_ALWAYS,
			FILE_ATTRIBUTE_NORMAL, NULL);
		DWORD dwBytesWritten = 0;
		WriteFile(hFile, (LPSTR)&bmfHeader, sizeof(BITMAPFILEHEADER), &dwBytesWritten, NULL);
		WriteFile(hFile, (LPSTR)&bi, sizeof(BITMAPINFOHEADER), &dwBytesWritten, NULL);
		WriteFile(hFile, (LPSTR)*data, dwBmpSize, &dwBytesWritten, NULL);
		// Close the handle for the file that was created.
		CloseHandle(hFile);
		*/
	}
}




BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
	switch (fdwReason) {
	case DLL_PROCESS_ATTACH: {
		hdc = GetDC(NULL);
		hmdc = CreateCompatibleDC(hdc);
	}; break;
	case DLL_PROCESS_DETACH: {
		//Clean up
		DeleteObject(hmdc);
		ReleaseDC(NULL, hdc);
		if (hDIB) {
			// Unlock and Free the DIB from the heap.
			GlobalUnlock(hDIB);
			GlobalFree(hDIB);
		}
	}; break;
	case DLL_THREAD_ATTACH: {
	}; break;
	case DLL_THREAD_DETACH: {
	}; break;
	default: {
	}; break;
	}
	return TRUE;

}

