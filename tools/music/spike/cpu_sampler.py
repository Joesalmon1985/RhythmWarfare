"""THROWAWAY (M2.1 spike): samples a process's CPU time and working set every 0.1 s until it exits (Windows, ctypes only).
   python cpu_sampler.py <pid file to wait for> <out csv>   -> rows: unix time, cpu seconds (user + kernel), working set MB, private bytes MB"""
import ctypes, ctypes.wintypes as w, os, sys, time

pid_file, out = sys.argv[1], sys.argv[2]
t_end = time.time() + 1800
while not os.path.exists(pid_file) and time.time() < t_end:
    time.sleep(0.05)
pid = int(open(pid_file).read().strip())
k32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
h = k32.OpenProcess(0x1000 | 0x0010, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ


class PMC(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t), ("PrivateUsage", ctypes.c_size_t)]


def ft(f):
    return (f.dwHighDateTime << 32 | f.dwLowDateTime) / 1e7


with open(out, "w") as o:
    o.write("unix,cpu_s,ws_mb,private_mb\n")
    while True:
        c, e, kt, ut = w.FILETIME(), w.FILETIME(), w.FILETIME(), w.FILETIME()
        if not k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut)):
            break
        code = w.DWORD()
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        if code.value != 259:  # STILL_ACTIVE
            break
        m = PMC(); m.cb = ctypes.sizeof(PMC)
        psapi.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb)
        o.write("%.3f,%.4f,%.1f,%.1f\n" % (time.time(), ft(kt) + ft(ut), m.WorkingSetSize / 1048576, m.PrivateUsage / 1048576))
        o.flush()
        time.sleep(0.1)
