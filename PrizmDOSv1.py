#PrizmDOS v1 | An MS-DOS simulator for the CASIO Prizm calculator (fx-CG10/20/50)
#Sorry for vibecoding! I don't usually code, and this script is just for fun. Enjoy, I guess!

# State lives in one-item lists so functions can change it without "global".
cols = [21]          # screen width in characters
page_lines = [6]     # lines shown before "-- More --"
line_count = [0]     # lines printed since the last pause
capture = [None]     # list while output is redirected with > or >>
echo_on = [1]        # batch ECHO ON/OFF
errorlevel = [0]     # set to 1 by failing commands
label = ["PRIZM"]    # volume label
DISK = 33554432      # fake disk size in bytes
STAMP = ["10-02-26", "12:00p"]  # date/time shown on new files
cwd = []             # current directory as a list of names
env = {"PATH": "C:\\DOS", "PROMPT": "$P$G", "COMSPEC": "C:\\COMMAND.COM"}

def system_file(n):
    return ["", "09-30-93", " 6:22a", n]

def dos_file(t):
    return [t, "09-30-93", " 6:22a"]

root = {
    "COMMAND.COM": system_file(54619),
    "AUTOEXEC.BAT": dos_file("@ECHO OFF\nPROMPT $P$G\nPATH C:\\DOS\nSET TEMP=C:\\DOS\nVER"),
    "CONFIG.SYS": dos_file("DEVICE=C:\\DOS\\HIMEM.SYS\nFILES=30\nBUFFERS=20"),
    "DOS": {
        "HIMEM.SYS": system_file(29128),
        "EDIT.COM": system_file(413),
        "WIN.EXE": system_file(262144),
        "README.TXT": dos_file("Welcome to PrizmDOS.\nType HELP for commands.\nTry EDIT, TREE, DIR /W."),
    },
    "GAMES": {},
}

# Mock programs: file name -> what it prints. Other .EXE/.COM files print a DOS notice.
PROGRAMS = {"WIN.EXE": "Linux is better!"}

U = {
    "DIR": "DIR [path] [/W] [/B]\nWildcards * ? work.",
    "CD": "CD [path]\nCD..  CD\\",
    "MD": "MD path",
    "RD": "RD path\nEmpty dirs only.",
    "TYPE": "TYPE file",
    "COPY": "COPY src dest\nCOPY CON file types\ntext, end with a .",
    "DEL": "DEL file or *.EXT",
    "REN": "REN old new",
    "MOVE": "MOVE src dest",
    "ECHO": "ECHO text|ON|OFF\nECHO. = blank line\nECHO hi > file",
    "SET": "SET [VAR=value]\nUse %VAR% in lines.",
    "PATH": "PATH [dir;dir]",
    "PROMPT": "PROMPT text\n$P path $G > $N C\n$_ newline",
    "DATE": "Prints a greeting.",
    "TIME": "Prints a reminder.",
    "FIND": 'FIND [/I][/N] "t" file',
    "TREE": "TREE [/F]",
    "MODE": "MODE [cols [lines]]",
    "EDIT": "EDIT file\nLine editor, H=help",
    "FORMAT": "FORMAT C:\nWipes the RAM disk.",
    "DELTREE": "DELTREE dir",
    "LABEL": "LABEL [name]",
    "SAVEFS": "SAVEFS [file]\nSave disk to a real\nfile (if allowed).",
    "LOADFS": "LOADFS [file]",
    "IF": "IF [NOT] EXIST f cmd\nIF [NOT] ERRORLEVEL n cmd\nIF [NOT] a==b cmd",
    "GOTO": "GOTO label\nlabel line = :NAME",
    "CALL": "CALL file.bat [args]",
    "PAUSE": "Waits for ENTER.",
    "REM": "REM comment",
    "EXIT": "Leave DOS.",
    "CASIOWIN": "Starts CASIOWIN.\nWhat could go wrong?",
    "HELP": "HELP [command]",
    "VER": "VER",
    "VOL": "VOL",
    "CLS": "CLS",
    "MEM": "MEM",
    "CHKDSK": "CHKDSK",
}

def is_dir(x):
    return type(x) is dict

def is_file(x):
    return type(x) is list

def new_file(t):
    return [t, STAMP[0], STAMP[1]]

def file_size(f):
    if len(f) > 3:
        return f[3]
    return len(f[0])

def commas(n):
    s = str(n)
    r = ""
    while len(s) > 3:
        r = "," + s[-3:] + r
        s = s[:-3]
    return s + r

def out(s):
    if capture[0] is not None:
        capture[0].append(s)
        return
    for l in s.split("\n"):
        while 1:
            n = cols[0]
            more = 0
            if len(l) > n:
                k = n
                while k > 0 and l[k] != " ":
                    k -= 1
                if k > 0:
                    c = l[:k]
                    l = l[k + 1:]
                else:
                    c = l[:n]
                    l = l[n:]
                more = 1
            else:
                c = l
            print(c)
            line_count[0] += 1
            if line_count[0] >= page_lines[0]:
                input("-- More --")
                line_count[0] = 0
            if not more:
                break

def error(m):
    out(m)
    errorlevel[0] = 1

def confirm(m):
    return input(m + " (Y/N)?").strip().upper()[:1] == "Y"

def resolve(p):
    p = p.upper().replace("/", "\\")
    if p[1:2] == ":":
        p = p[2:]
    o = []
    if p[:1] != "\\":
        o = cwd[:]
    for s in p.split("\\"):
        if s == "" or s == ".":
            continue
        if s == "..":
            if o:
                o.pop()
        else:
            o.append(s)
    return o

def get_node(p):
    d = root
    for s in p:
        if is_dir(d) and s in d:
            d = d[s]
        else:
            return None
    return d

def pwd(p):
    return "C:\\" + "\\".join(p)

def valid_name(n):
    i = n.find(".")
    if i < 0:
        b = n
        e = ""
    else:
        b = n[:i]
        e = n[i + 1:]
    if b == "" or len(b) > 8 or len(e) > 3 or "." in e:
        return 0
    for c in n:
        if c in ' "/\\[]:|<>+=;,*?':
            return 0
    return 1

def write_file(p, v):
    if not p:
        return 0
    par = get_node(p[:-1])
    if not is_dir(par) or not valid_name(p[-1]) or is_dir(par.get(p[-1])):
        return 0
    par[p[-1]] = v
    return 1

def wildcard(n, p):
    if p == "*.*" or p == "*":
        return 1
    if p == "":
        return n == ""
    if p[0] == "*":
        return wildcard(n, p[1:]) or (n != "" and wildcard(n[1:], p))
    if n != "" and (p[0] == "?" or p[0] == n[0]):
        return wildcard(n[1:], p[1:])
    return 0

def dir_size(d):
    t = 0
    for k in d:
        v = d[k]
        if is_dir(v):
            t += dir_size(v)
        else:
            t += file_size(v)
    return t

def count_tree(d):
    f = 0
    n = 0
    for k in d:
        if is_dir(d[k]):
            n += 1
            a, b = count_tree(d[k])
            f += a
            n += b
        else:
            f += 1
    return f, n

def prompt():
    s = env.get("PROMPT", "$N$G")
    m = {"P": pwd(cwd), "G": ">", "L": "<", "N": "C", "Q": "=", "B": "|",
         "V": "MS-DOS (sim) 6.22", "_": "\n", "$": "$"}
    o = ""
    j = 0
    while j < len(s):
        if s[j] == "$" and j + 1 < len(s):
            o += m.get(s[j + 1].upper(), "")
            j += 2
        else:
            o += s[j]
            j += 1
    return o

def expand(s, P):
    o = ""
    j = 0
    while j < len(s):
        ch = s[j]
        if ch == "%" and j + 1 < len(s):
            n = s[j + 1]
            if n == "%":
                o += "%"
                j += 2
                continue
            if n.isdigit():
                k = int(n)
                if k < len(P):
                    o += P[k]
                j += 2
                continue
            k = s.find("%", j + 1)
            if k > j + 1:
                o += env.get(s[j + 1:k].upper(), "")
                j = k + 1
                continue
        o += ch
        j += 1
    return o

# ---------- commands ----------

def c_dir(a, r):
    w = 0
    b = 0
    ar = ""
    for x in a:
        u = x.upper()
        if u == "/W":
            w = 1
        elif u == "/B":
            b = 1
        elif u == "/P":
            pass
        elif x[0] == "/":
            return error("Invalid switch - " + x)
        else:
            ar = x
    t = resolve(ar) if ar else cwd[:]
    pat = "*.*"
    if ar:
        if "*" in ar or "?" in ar:
            pat = t[-1] if t else "*.*"
            t = t[:-1]
        elif not is_dir(get_node(t)):
            if t and is_file(get_node(t)):
                pat = t[-1]
                t = t[:-1]
            else:
                return error("File not found")
    d = get_node(t)
    if not is_dir(d):
        return error("Path not found")
    if not b:
        if cols[0] >= 40:
            out(" Volume in drive C is " + label[0])
            out(" Volume Serial Number is 1A2B-3C4D")
            out(" Directory of " + pwd(t))
        else:
            out(" Vol C is " + label[0])
            out(" Dir of " + pwd(t))
        out("")
    its = []
    if t and (pat == "*.*" or pat == "*"):
        its.append((".", {}))
        its.append(("..", {}))
    ks = list(d.keys())
    ks.sort()
    for n in ks:
        if wildcard(n, pat):
            its.append((n, d[n]))
    nfl = 0
    nd = 0
    tb = 0
    ws = []
    for n, v in its:
        bs = n
        ext = ""
        if n[0] != ".":
            i = n.find(".")
            if i >= 0:
                bs = n[:i]
                ext = n[i + 1:]
        if is_dir(v):
            nd += 1
            zs = "<DIR>"
            st = STAMP[0] + "  " + STAMP[1]
        else:
            nfl += 1
            tb += file_size(v)
            zs = commas(file_size(v))
            st = v[1] + "  " + v[2]
        if b:
            out(n)
        elif w:
            ws.append("[" + n + "]" if is_dir(v) else n)
        else:
            row = "%-8s %-3s %7s" % (bs, ext, zs)
            if cols[0] >= 40:
                row += "  " + st
            out(row)
    if w:
        c = cols[0] // 14
        if c < 1:
            c = 1
        for i in range(0, len(ws), c):
            out("".join(["%-14s" % x for x in ws[i:i + c]]))
    if not b:
        fr = commas(DISK - dir_size(root))
        if cols[0] >= 40:
            out("%9d file(s)%15s bytes" % (nfl, commas(tb)))
            out("%9d dir(s)%16s bytes free" % (nd, fr))
        else:
            out("%d file(s) %s bytes" % (nfl, commas(tb)))
            out("%d dir(s) %s free" % (nd, fr))

def c_cd(a, r):
    if not a:
        return out(pwd(cwd))
    p = resolve(a[0])
    if is_dir(get_node(p)):
        cwd[:] = p
    else:
        error("Invalid directory")

def c_md(a, r):
    if not a:
        return error("Required parameter missing")
    for x in a:
        p = resolve(x)
        par = get_node(p[:-1]) if p else None
        if not is_dir(par) or not valid_name(p[-1]):
            error("Unable to create\ndirectory")
        elif p[-1] in par:
            error("Directory already\nexists")
        else:
            par[p[-1]] = {}

def c_rd(a, r):
    if not a:
        return error("Required parameter missing")
    for x in a:
        p = resolve(x)
        d = get_node(p) if p else None
        if not is_dir(d) or d or cwd[:len(p)] == p:
            error("Invalid path, not\ndirectory, or dir\nnot empty")
        else:
            get_node(p[:-1]).pop(p[-1])

def c_type(a, r):
    if not a:
        return error("Required parameter missing")
    for x in a:
        f = get_node(resolve(x))
        if is_file(f):
            for l in f[0].split("\n"):
                out(l)
        else:
            error("File not found - " + x.upper())

def c_copy(a, r):
    a = [x for x in a if x[0] != "/"]
    if len(a) < 1:
        return error("Required parameter missing")
    if a[0].upper() == "CON":
        if len(a) < 2:
            return error("Required parameter missing")
        print("End with . alone")
        t = []
        while 1:
            l = input("")
            if l == ".":
                break
            t.append(l)
        if write_file(resolve(a[1]), new_file("\n".join(t))):
            out("        1 file(s) copied")
        else:
            error("Unable to create file")
        return
    sp = resolve(a[0])
    d = get_node(sp[:-1]) if sp else None
    if not is_dir(d):
        return error("File not found")
    ms = [n for n in d if is_file(d[n]) and wildcard(n, sp[-1])]
    ms.sort()
    if not ms:
        return error("File not found")
    dp = resolve(a[1]) if len(a) > 1 else cwd[:]
    dd = is_dir(get_node(dp))
    if not dd and len(ms) > 1:
        return error("Cannot copy many\nfiles to one file")
    k = 0
    for n in ms:
        tp = dp + [n] if dd else dp
        if tp == sp[:-1] + [n]:
            error("File cannot be\ncopied onto itself")
        elif write_file(tp, d[n][:]):
            k += 1
        else:
            error("Unable to create file")
    out("%9d file(s) copied" % k)

def c_del(a, r):
    a = [x for x in a if x[0] != "/"]
    if not a:
        return error("Required parameter missing")
    t = resolve(a[0])
    d = None
    pat = "*.*"
    if is_dir(get_node(t)):
        d = get_node(t)
    elif t:
        d = get_node(t[:-1])
        pat = t[-1]
    if not is_dir(d):
        return error("File not found")
    if (pat == "*.*" or pat == "*") and not confirm("All files in dir will\nbe deleted!\nAre you sure"):
        return
    ms = [n for n in list(d.keys()) if is_file(d[n]) and wildcard(n, pat)]
    if not ms:
        return error("File not found")
    for n in ms:
        d.pop(n)

def c_ren(a, r):
    if len(a) < 2:
        return error("Required parameter missing")
    p = resolve(a[0])
    n = a[1].upper()
    d = get_node(p[:-1]) if p else None
    if not is_dir(d) or p[-1] not in d or n in d or not valid_name(n):
        return error("Duplicate file name\nor file not found")
    d[n] = d.pop(p[-1])

def c_move(a, r):
    if len(a) < 2:
        return error("Required parameter missing")
    s = resolve(a[0])
    par = get_node(s[:-1]) if s else None
    if not is_dir(par) or s[-1] not in par:
        return error("Cannot find file")
    dp = resolve(a[1])
    if is_dir(get_node(dp)):
        dp = dp + [s[-1]]
    dpar = get_node(dp[:-1]) if dp else None
    if not is_dir(dpar) or dp[-1] in dpar or not valid_name(dp[-1]) or dp[:len(s)] == s:
        return error("Cannot move file")
    dpar[dp[-1]] = par.pop(s[-1])
    out(pwd(s) + " =>")
    out(pwd(dp) + " [ok]")

def c_echo(a, r):
    t = r.strip().upper()
    if t == "" and r[:1] != ".":
        out("ECHO is " + ("on" if echo_on[0] else "off"))
    elif t == "ON":
        echo_on[0] = 1
    elif t == "OFF":
        echo_on[0] = 0
    else:
        out(r[1:] if r[:1] in (" ", ".") else r)

def c_set(a, r):
    t = r.strip()
    if not t:
        k = list(env.keys())
        k.sort()
        for x in k:
            out(x + "=" + env[x])
    elif "=" in t:
        k, v = t.split("=", 1)
        k = k.strip().upper()
        v = v.strip()
        if v == "":
            env.pop(k, None)
        else:
            env[k] = v
    else:
        error("Environment variable\nnot defined")

def c_path(a, r):
    t = r.strip().lstrip("= ")
    if r.strip() == "":
        out("PATH=" + env["PATH"] if "PATH" in env else "No Path")
    elif t == ";":
        env.pop("PATH", None)
    else:
        env["PATH"] = t.upper()

def c_prompt(a, r):
    t = r.strip().lstrip("=").strip()
    env["PROMPT"] = t if t else "$N$G"

def c_ver(a, r):
    out("")
    out("PrizmDOS v1")
    out("")

def c_vol(a, r):
    out(" Volume in drive C is " + label[0])
    out(" Volume Serial Number is 1A2B-3C4D")

def c_label(a, r):
    if a:
        label[0] = " ".join(a).upper()[:11]
    else:
        out("Volume in drive C is " + label[0])
        t = input("Volume label (11\ncharacters, ENTER=none)? ")
        label[0] = t.upper()[:11]

def c_date(a, r):
    out("Lovely day out there!")

def c_time(a, r):
    out("Check your watch!")

def c_mem(a, r):
    out("655360 bytes total conventional memory")
    out("655360 bytes available to MS-DOS")
    out(" 598240 largest executable program size")
    out("")
    out("1048576 bytes total contiguous extended memory")

def c_chkdsk(a, r):
    f, n = count_tree(root)
    u = dir_size(root)
    out(" Volume " + label[0] + " created " + STAMP[0])
    out(" Volume Serial Number is 1A2B-3C4D")
    out("")
    out(commas(DISK) + " bytes total disk space")
    out(commas(u) + " bytes in " + str(f) + " user files")
    out(commas(DISK - u) + " bytes available on disk")
    out("")
    out("655,360 total bytes memory")
    out("598,240 bytes free")

def c_format(a, r):
    if not a or a[0].upper()[:2] != "C:":
        return error("Invalid drive specification")
    out("WARNING, ALL DATA ON NON-REMOVABLE DISK DRIVE C: WILL BE LOST!")
    if not confirm("Proceed with Format"):
        return
    out("Formatting 32.0M")
    out("Format complete.")
    l = input("Volume label (11 chars, ENTER=none)? ")
    root.clear()
    cwd[:] = []
    label[0] = l.upper()[:11]
    out(commas(DISK) + " bytes total disk space")
    out(commas(DISK) + " bytes available on disk")

def c_deltree(a, r):
    if not a:
        return error("Required parameter missing")
    for x in a:
        p = resolve(x)
        if not p or not is_dir(get_node(p)):
            error("Directory not found")
        elif confirm("Delete " + x.upper() + "\nand all its subdirs? [yn]"):
            get_node(p[:-1]).pop(p[-1])
            if cwd[:len(p)] == p:
                cwd[:] = p[:-1]
            out("Deleting " + x.upper() + "...")

def tree_lines(d, pre, fl):
    ks = list(d.keys())
    ks.sort()
    ds = [k for k in ks if is_dir(d[k])]
    if fl:
        fs = [k for k in ks if is_file(d[k])]
        for f in fs:
            out(pre + ("|   " if ds else "    ") + f)
        if fs and ds:
            out(pre + "|")
    for i in range(len(ds)):
        last = i == len(ds) - 1
        out(pre + ("\\---" if last else "+---") + ds[i])
        tree_lines(d[ds[i]], pre + ("    " if last else "|   "), fl)

def c_tree(a, r):
    fl = "/F" in [x.upper() for x in a]
    out(pwd(cwd) if cwd else "C:.")
    tree_lines(get_node(cwd), "", fl)

def c_find(a, r):
    s = r.strip()
    i = s.find('"')
    j = s.find('"', i + 1) if i >= 0 else -1
    if i < 0 or j < 0:
        return error("FIND: Parameter format\nnot correct")
    o = s[:i].upper()
    tx = s[i + 1:j]
    ic = "/I" in o
    ln = "/N" in o
    if ic:
        tx = tx.upper()
    for x in s[j + 1:].split():
        f = get_node(resolve(x))
        if not is_file(f):
            error("File not found - " + x.upper())
            continue
        out("---------- " + x.upper())
        k = 0
        for l in f[0].split("\n"):
            k += 1
            if tx in (l.upper() if ic else l):
                out(("[%d]" % k if ln else "") + l)

def c_mode(a, r):
    k = 0
    for x in a:
        u = x.upper().replace("CON", "")
        if u[:5] == "COLS=":
            cols[0] = max(10, int(u[5:]))
        elif u[:6] == "LINES=":
            page_lines[0] = max(4, int(u[6:]))
        elif u.isdigit():
            if k == 0:
                cols[0] = max(10, int(u))
            else:
                page_lines[0] = max(4, int(u))
            k += 1
    out("Status for device CON:")
    out("Columns=%d" % cols[0])
    out("Lines=%d" % page_lines[0])

def c_cls(a, r):
    for i in range(12):
        print("")
    line_count[0] = 0

def c_help(a, r):
    if a and a[0].upper() in U:
        return out(U[a[0].upper()])
    out("Commands (CMD /?):")
    ws = list(U.keys())
    ws.sort()
    c = max(1, cols[0] // 8)
    for i in range(0, len(ws), c):
        out("".join(["%-8s" % x for x in ws[i:i + c]]))

def c_savefs(a, r):
    n = a[0] if a else "DOSDISK.TXT"
    try:
        f = open(n, "w")
        f.write(repr(root))
        f.close()
        out("Disk saved.")
    except:
        error("No file access")

def c_loadfs(a, r):
    n = a[0] if a else "DOSDISK.TXT"
    try:
        f = open(n)
        d = eval(f.read())
        f.close()
        if not is_dir(d):
            raise ValueError
        root.clear()
        root.update(d)
        cwd[:] = []
        out("Disk loaded.")
    except:
        error("Cannot load disk")

def c_edit(a, r):
    if not a:
        return error("Required parameter missing")
    p = resolve(a[0])
    f = get_node(p)
    par = get_node(p[:-1]) if p else None
    if is_dir(f) or not is_dir(par) or not valid_name(p[-1]):
        return error("Invalid filename")
    ls = f[0].split("\n") if is_file(f) and f[0] != "" else []
    mod = 0
    print("EDIT " + pwd(p))
    print("H=help")
    while 1:
        line_count[0] = 0
        c = input("*").strip()
        cm = c[:1].upper()
        ag = c[1:].strip()
        if cm == "L":
            for i in range(len(ls)):
                out("%3d %s" % (i + 1, ls[i]))
        elif cm == "A" or cm == "I":
            n = len(ls)
            if cm == "I" and ag.isdigit():
                n = max(0, min(len(ls), int(ag) - 1))
            print("End with . alone")
            while 1:
                t = input("%d>" % (n + 1))
                if t == ".":
                    break
                ls.insert(n, t)
                n += 1
                mod = 1
        elif cm == "E":
            if ag.isdigit() and 1 <= int(ag) <= len(ls):
                ls[int(ag) - 1] = input(ag + ">")
                mod = 1
            else:
                print("Bad line number")
        elif cm == "D":
            q = ag.split()
            if q and q[0].isdigit():
                n = int(q[0])
                m = int(q[1]) if len(q) > 1 and q[1].isdigit() else n
                if 1 <= n <= m <= len(ls):
                    for i in range(m - n + 1):
                        ls.pop(n - 1)
                    mod = 1
                    continue
            print("Bad line number")
        elif cm == "S" or cm == "X":
            par[p[-1]] = new_file("\n".join(ls))
            mod = 0
            if cm == "X":
                break
            print("Saved")
        elif cm == "Q":
            if mod and not confirm("Discard changes"):
                continue
            break
        else:
            print("L list A append")
            print("I n insert before n")
            print("E n edit D n [m] del")
            print("S save X save+exit")
            print("Q quit  . ends input")

# ---------- batch / run ----------

def find_batch(t):
    n = t.upper()
    b = n.replace("/", "\\").split("\\")[-1]
    if "." not in b:
        n += ".BAT"
    if not n.endswith(".BAT"):
        return None
    ds = []
    if "\\" in n or "/" in n:
        p = resolve(n)
        f = get_node(p)
        if is_file(f):
            return f[0].split("\n")
        return None
    ds.append(cwd[:])
    for x in env.get("PATH", "").split(";"):
        if x:
            ds.append(resolve(x))
    for d in ds:
        dd = get_node(d)
        if is_dir(dd) and is_file(dd.get(n)):
            return dd[n][0].split("\n")
    return None

def find_exe(t):
    n = t.upper().replace("/", "\\")
    names = [n] if n[-4:] in (".EXE", ".COM") else [n + ".COM", n + ".EXE"]
    for x in names:
        if "\\" in x:
            if is_file(get_node(resolve(x))):
                return x.split("\\")[-1]
            continue
        dirs = [cwd[:]]
        for d in env.get("PATH", "").split(";"):
            if d:
                dirs.append(resolve(d))
        for d in dirs:
            dd = get_node(d)
            if is_dir(dd) and is_file(dd.get(x)):
                return x
    return None

def run_step(l):
    w = l.split()
    c = w[0].upper()
    if c == "REM":
        return None
    if c == "PAUSE":
        input("Press any key to continue . . . ")
        return None
    if c == "GOTO":
        return ("G", w[1].upper() if len(w) > 1 else "")
    if c == "EXIT":
        return "X"
    if c == "CALL":
        if len(w) < 2:
            return error("Required parameter missing")
        L = find_batch(w[1])
        if L is None:
            return error("Bad command or file name")
        o = echo_on[0]
        rr = run_batch(L, [w[1].upper()] + w[2:])
        echo_on[0] = o
        return "X" if rr == 0 else None
    if c == "IF":
        try:
            i = 1
            neg = 0
            if w[i].upper() == "NOT":
                neg = 1
                i += 1
            k = w[i].upper()
            if k == "EXIST":
                cond = get_node(resolve(w[i + 1])) is not None
                i += 2
            elif k == "ERRORLEVEL":
                cond = errorlevel[0] >= int(w[i + 1])
                i += 2
            else:
                x, y = w[i].split("==", 1)
                cond = x == y
                i += 1
            if neg:
                cond = not cond
            if cond and len(w) > i:
                return run_step(" ".join(w[i:]))
            return None
        except:
            return error("Syntax error")
    if run(l) == 0:
        return "X"
    return None

def run_batch(lines, P):
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if s == "" or s[0] == ":":
            continue
        q = 0
        if s[0] == "@":
            q = 1
            s = s[1:].strip()
        s = expand(s, P)
        if s == "":
            continue
        if s.upper().split()[0] == "SHIFT":
            if len(P) > 1:
                P.pop(1)
            continue
        if echo_on[0] and not q:
            out(prompt() + s)
        st = run_step(s)
        if st == "X":
            return 0
        if type(st) is tuple:
            lab = ":" + st[1]
            ok = 0
            for j in range(len(lines)):
                if lines[j].strip().upper() == lab:
                    i = j + 1
                    ok = 1
                    break
            if not ok:
                error("Label not found")
                return 1
    return 1

def crash():
    print("Starting CASIOWIN...")
    print("")
    print("Divide overflow")
    print("Fatal exception 0E")
    print("at 0028:C0011E36")
    print("System halted.")

def run(line):
    line = line.strip()
    if line == "":
        return 1
    k = 0
    while k < len(line) and line[k] not in " ./\\=":
        k += 1
    c = line[:k].upper()
    rest = line[k:]
    if len(line) == 2 and line[1] == ":":
        if line.upper() != "C:":
            error("Invalid drive specification")
        return 1
    tg = None
    ap = 0
    if "|" in line:
        line = line.split("|", 1)[0].strip()
        rest = line[k:]
    if c != "PROMPT":
        i = line.find(">")
        if i >= 0:
            ap = line[i:i + 2] == ">>"
            tg = line[i + (2 if ap else 1):].strip()
            line = line[:i].strip()
            rest = line[k:]
            capture[0] = []
    a = rest.split()
    rv = 1
    if "/?" in a and c in U:
        out(U[c])
    elif c == "EXIT":
        rv = 0
    elif c == "CASIOWIN":
        crash()
        rv = 0
    elif c in ("REM", "PAUSE", "IF", "CALL", "GOTO"):
        if run_step(line) == "X":
            rv = 0
    elif c in CM:
        errorlevel[0] = 0
        CM[c](a, rest)
    else:
        t = line.split()[0]
        exe = find_exe(t)
        L = find_batch(t)
        if exe:
            errorlevel[0] = 0
            out(PROGRAMS.get(exe, "This program cannot be run in DOS mode."))
        elif L is None:
            error("Bad command or file name")
        else:
            errorlevel[0] = 0
            o = echo_on[0]
            if run_batch(L, [t.upper()] + line.split()[1:]) == 0:
                rv = 0
            echo_on[0] = o
    if tg is not None:
        buf = capture[0]
        capture[0] = None
        if tg.upper() != "NUL":
            tx = "\n".join(buf)
            f = get_node(resolve(tg))
            if ap and is_file(f):
                f[0] = f[0] + "\n" + tx if f[0] else tx
            elif not write_file(resolve(tg), new_file(tx)):
                error("Access denied?")
    return rv

CM = {
    "DIR": c_dir, "CD": c_cd, "CHDIR": c_cd, "MD": c_md, "MKDIR": c_md,
    "RD": c_rd, "RMDIR": c_rd, "TYPE": c_type, "COPY": c_copy,
    "DEL": c_del, "ERASE": c_del, "REN": c_ren, "RENAME": c_ren,
    "MOVE": c_move, "ECHO": c_echo, "SET": c_set, "PATH": c_path,
    "PROMPT": c_prompt, "VER": c_ver, "VOL": c_vol, "LABEL": c_label,
    "DATE": c_date, "TIME": c_time, "MEM": c_mem, "CHKDSK": c_chkdsk,
    "FORMAT": c_format, "DELTREE": c_deltree, "TREE": c_tree,
    "FIND": c_find, "MODE": c_mode, "CLS": c_cls, "HELP": c_help,
    "SAVEFS": c_savefs, "LOADFS": c_loadfs, "EDIT": c_edit,
}

print("Starting PrizmDOS...")
print("")
L0 = find_batch("C:\\AUTOEXEC.BAT")
if L0:
    run_batch(L0, ["AUTOEXEC.BAT"])
echo_on[0] = 1
while 1:
    line_count[0] = 0
    try:
        s = input(prompt() if echo_on[0] else "")
        if run(expand(s, [])) == 0:
            break
    except EOFError:
        break
    except Exception:
        capture[0] = None
        print("Error")
