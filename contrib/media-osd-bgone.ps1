# media-osd-bgone.ps1: disable media-control OSD on win10do
# v1.1, 2021-06-25, ed <irc.rizon.net>, MIT-licensed
# https://github.com/9001/copyparty/blob/hovudstraum/contrib/media-osd-bgone.ps1
#
# locates the first window that looks like the media OSD and minimizes it;
# doing this once after each reboot should do the trick
# (adjust the width/height filter if it doesn't work)
#
# ---------------------------------------------------------------------
#
# tip: save the following as "media-osd-bgone.bat" next to this script:
#   start cmd /c "powershell -command ""set-executionpolicy -scope process bypass; .\media-osd-bgone.ps1"" & ping -n 2 127.1 >nul"
#
# then create a shortcut to that bat-file and move the shortcut here:
#   %appdata%\Microsoft\Windows\Start Menu\Programs\Startup
#
# and now this will autorun on bootup


Add-Type -TypeDefinition @"
using System;
using System.IO;
using System.Threading;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace A {
  public class B : Control {

    [DllImport("user32.dll")]
    static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);

    [DllImport("user32.dll", SetLastError = true)]
    static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string lpszClass, string lpszWindow);

    [DllImport("user32.dll", SetLastError=true)]
    static extern bool GetWindowRect(IntPtr hwnd, out RECT lpRect);

    [DllImport("user32.dll")]
    static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
      public int x;
      public int y;
      public int x2;
      public int y2;
    }
    
    bool fa() {
      RECT r;
      IntPtr it = IntPtr.Zero;
      while ((it = FindWindowEx(IntPtr.Zero, it, "NativeHWNDHost", "")) != IntPtr.Zero) {
        if (FindWindowEx(it, IntPtr.Zero, "DirectUIHWND", "") == IntPtr.Zero)
          continue;
        
        if (!GetWindowRect(it, out r))
          continue;

        int w = r.x2 - r.x + 1;
        int h = r.y2 - r.y + 1;

        Console.WriteLine("[*] hwnd {0:x} @ {1}x{2} sz {3}x{4}", it, r.x, r.y, w, h);
        if (h != 141)
          continue;
        
        ShowWindow(it, 6);
        Console.WriteLine("[+] poof");
        return true;
      }
      return false;
    }

    void fb() {
      keybd_event((byte)Keys.VolumeMute, 0, 0, 0);
      keybd_event((byte)Keys.VolumeMute, 0, 2, 0);
      Thread.Sleep(500);
      keybd_event((byte)Keys.VolumeMute, 0, 0, 0);
      keybd_event((byte)Keys.VolumeMute, 0, 2, 0);

      while (true) {
        if (fa()) {
          break;
        }
        Console.WriteLine("[!] not found");
        Thread.Sleep(1000);
      }
      this.Invoke((MethodInvoker)delegate {
        Application.Exit();
      });
    }

    public void Run() {
      Console.WriteLine("[+] hi");
      new Thread(new ThreadStart(fb)).Start();
      Application.Run();
      Console.WriteLine("[+] bye");
    }
  }
}
"@ -ReferencedAssemblies System.Windows.Forms

(New-Object -TypeName A.B).Run()
