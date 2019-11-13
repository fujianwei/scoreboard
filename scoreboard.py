from tkinter import *
import tkinter.scrolledtext
import tkinter.filedialog
import time
from tkinter.messagebox import showinfo

file = ''
# file = 'LD F6 34 R2|LD F2 45 R3|MULT F0 F2 F4|SUBD F8 F6 F2|DIVD F10 F0 F6|ADDD F6 F8 F2'
IS = [[''] * 4 for i in range(6)]  # 创建指令的 表格6行4列
FS = [[''] * 9 for i in range(5)]  # 创建功能部件的 表格5行9列
RS = [[''] * 6 for i in range(1)]  # 创建寄存及的 表格1行6列
_is = ['issue', 'read', 'exec', 'write']
_fs = ['Busy', 'OP', 'Fi', 'Fj', 'Fk', 'Qj', 'Qk', 'Rj', 'Rk']
_rs = ['F0', 'F2', 'F4', 'F6', 'F8', 'F10']

def ope():  # 打开文件选择 同时开始
    filename = tkinter.filedialog.askopenfilename()
    if filename != '':
        global file  # 不写这一行会导致歧义，python会产生一个新的局部变量也命名为file，导致修改的不是全局变量
        file = open(filename).read()
        content = file.split('|')
        for con in content:
            txt.insert(END, con+'\n')
        # print(content)


def run():
    run_process()

def popupmenu(event):
     mainmenu.post(event.x_root, event.y_root)


def about():
    # 弹出一个新的窗口 上面写有学号和姓名
    showinfo(title='关于', message='小组成员：付建伟')


def help():
    # 弹出新建窗口 展示如何使用
    showinfo(title='使用帮助', message='使用方法：\n'
                                   '点击菜单中的文件按钮，选择写有汇编语言的文件\n'
                                   '点击确定后即可开始运行\n'
                                   '文件中的代码要求：必须使用汇编语言\n\n'
                                   '关于：\n'
                                   '开发者信息\n\n'
                                   '退出：\n'
                                   '"文件" - "退出" ')


def run_process():
    codesplit = get_codes(file)
    if file == '':
        showinfo(title='警告', message='请选择文件')
        return None
    instructionlist = []  # 存放每一个指令 instructionlist[i]._op [i]._source1...
    for s in codesplit:  # ins的变量赋值
        ins = Instruction()
        ss = s.split(' ')  # ss是指令块
        ins._op = ss[0]
        ins._dest = ss[1]
        ins._source1 = ss[2]
        ins._source2 = ss[3]
        ins._state = 0
        ins._stage = [0, 0, 0, 0]
        instructionlist.append(ins)  # instructionlis是一个6x4的二维数组
        if ss[0] == 'MULT':
            ins._clock = 10
        elif ss[0] == 'DIVD':
            ins._clock = 40
        elif ss[0] == 'SUBD' or ss[0] == 'ADDD':
            ins._clock = 2
        elif ss[0] == 'LD':
            ins._clock = 1
        else:
            pass
    cycle = 1
    lastnow = 0  # 当前执行的指令最后一个

    while True:
        # 找到当前正在执行的指令后面一条指令
        flag = 0
        for i in range(0, 6):
            if instructionlist[i]._state == 1 and instructionlist[i+1]._state == 0:
                lastnow = i
            if instructionlist[0]._state == 0:
                lastnow = 0
            if instructionlist[5]._state == 1:
                lastnow = 5
            if instructionlist[i]._state == 2:
                flag += 1
        txt_process.insert(END, '当前执行的最后一条指令为第%d条指令' % (lastnow+1))
        if flag == 6:  # 6条指令全部执行完了
            break

        # 然后需要判断当前所有正在执行的指令和当前指令的下一个指令
        # 因为每个循环需要判断下一条指令是否需要执行
        lastnow = lastnow + 1
        if lastnow + 1 > 5:
            lastnow = 5
        recordreset = []  # 记录每个周期执行中需要复原
        recordissue = 0  # 用来记录每次只能发射一个
        # 判断所有的正在执行的指令在目前的状态，能不能往下执行一下
        lastnow2 = lastnow + 1
        for i in range(0, lastnow2):
            if instructionlist[i]._state == 2:  # 如果是处于执行状态，那么无视该指令，继续执行
                continue
            for j in range(0, 4):  # 看每条指令执行到了什么状态
                if instructionlist[i]._stage[j] == 0:  # 首先看这条指令执行到了什么阶段
                    if j == 0:
                        if read_fs(instructionlist[i]._op):  # fs的第一列不是busy，没有结构相关
                            x = fun_num(instructionlist[i]._op)  # x：根据op找到应该使用FS表的第几（x+1）行
                            FS[x][0] = 'Busy'
                            FS[x][1] = instructionlist[i]._op
                            FS[x][2] = instructionlist[i]._dest
                            FS[x][3] = instructionlist[i]._source1
                            FS[x][4] = instructionlist[i]._source2

                            read_rs(instructionlist[i]._source1, instructionlist[i]._source2, x)  # 读相关，如果都是空，那么在fs处写上
                            write_rs(instructionlist[i]._dest, instructionlist[i]._op)  # 把op内容写到rs
                            instructionlist[i]._stage[j] = cycle
                            IS[i][0] = cycle  # 什么时候发射的
                            recordissue += 1  # 发射记录一次
                            break
                        else:
                            break
                    if j == 1:
                        read_rs(instructionlist[i]._source1, instructionlist[i]._source2, fun_num(instructionlist[i]._op))
                        index = fun_num(instructionlist[i]._op)
                        if FS[index][7] == 'yes' and FS[index][8] == 'yes':
                            # 都是ready的话就执行，读取操作数，指令状态发生变化
                            instructionlist[i]._stage[j] = cycle
                            IS[i][1] = cycle
                            break
                        else:
                            break
                    if j == 2:
                        instructionlist[i]._clock -= 1
                        if instructionlist[i]._clock == 0:
                            instructionlist[i]._stage[j] = cycle
                            IS[i][2] = cycle
                        break
                    if j == 3:  # 没有考虑到读后写相关
                        # 读后写相关：先读完，再写入
                        # 指令满足的条件：在该条指令之前，且还没有完成读操作数（没发射 或 发射但没有读操作数），且源操作数是该指令的目的操作数
                        # 则：需要等待满足上述条件的指令读完操作数后，再写入目的寄存器
                        # 读完：本周期不能写入目的寄存器：instructionlist[k]._stage[1]==当前周期数
                        write = 1

                        for k in range(0, i):  # 检查在当前即将执行写操作的指令之前的所有指令
                            if instructionlist[k]._stage[1] == 0:  # 还没读 或者 还没发射
                                if instructionlist[k]._source1 == instructionlist[i]._dest or instructionlist[k]._source2 == instructionlist[i]._dest:
                                    write = 0  # 找到了 还没进行读操作的指令 write设为0
                            if IS[k][1] == cycle:  # IS[i][2]表示读占用的周期，如果是本周期，即：正在读，那么后面的指令不可以写，只能等下一个周期写（等我读完，下个周期就读完）
                                write = 0
                        # 如果上述条件都满足，则不执行写操作
                        # 如果不满足，则执行写操作

                        if write == 1:  # 没有 没进行读操作 的指令，那么可以写
                            instructionlist[i]._stage[j] = cycle
                            instructionlist[i]._state = 2
                            IS[i][3] = cycle
                            recordreset.append(i)  # 指令执行完了，需要复原记一下
                        break

            if recordissue != 0:
                break

        # 复原：
        for x in recordreset:
            index = fun_num(instructionlist[x]._op)
            clear_fs(index)
            clear_rs(instructionlist[x]._dest)

        txt_process.insert(END, '\n')
        txt_process.insert(END, '当前周期数：%d\n' % cycle)
        # print('当前周期数', cycle)
        txt_process.insert(END, '=====IS状态=====\n')
        for i in range(len(IS)):
            if i == 0:  # 第一行输出名称
                for k in range(len(IS[i])):
                    txt_process.insert(END, '%s\t' % _is[k])
                txt_process.insert(END, '\n')
            for j in range(0, len(IS[i])):
                txt_process.insert(END, '%s\t' % IS[i][j])
            txt_process.insert(END, '\n')
            # print(IS[i])

        txt_process.insert(END, '=====FS状态=====\n')
        for i in range(len(FS)):
            if i == 0:  # 第一行输出名称
                for k in range(len(FS[i])):
                    txt_process.insert(END, '%s\t' % _fs[k])
                txt_process.insert(END, '\n')
            for j in range(len(FS[i])):
                txt_process.insert(END, '%s\t' % FS[i][j])
            txt_process.insert(END, '\n')
            # print(FS[i])

        txt_process.insert(END, '=====RS状态=====\n')
        for i in range(len(RS)):
            if i == 0:  # 第一行输出名称
                for k in range(len(RS[i])):
                    txt_process.insert(END, '%s\t' % _rs[k])
                txt_process.insert(END, '\n')
            for j in range(len(RS[i])):
                txt_process.insert(END, '%s\t' % RS[i][j])
        txt_process.insert(END, '\n')
        txt_process.insert(END, '\n')
        txt_process.insert(END, '============================================================================================')
        txt_process.insert(END, '\n')
        txt_process.insert(END, '\n')
        # print(RS[i])


        cycle += 1

    txt_process.insert(END, '\n')
    txt_process.insert(END, '指令执行完毕')

def get_codes(codes):
    code = codes
    codesplit = code.split('|')
    return codesplit



# FS表格第一列初始化为no
for i in range(0, 5):
    FS[i][0] = 'no'


class Instruction(object):  # 定义指令类以及里面的属性
    def __init__(self):
        self._op = ''
        self._dest = ''
        self._source1 = ''
        self._source2 = ''
        self._state = 0  # 0-not run ; 1-running ; 2-finished
        self._stage = [0]*4
        self._clock = 0


def fun_num(s):  # 获取操作指令对应的那个
    if s == 'LD':
        return 0
    elif s == 'MULT':
        return 1
    elif s == 'ADDD' or s == 'SUBD':
        return 3
    elif s == 'DIVD':
        return 4
    else:
        pass


def clear_fs(x):  # 清空function表的第x行
    FS[x][0] = 'no'
    for i in range(1, 9):
        FS[x][i] = ''


def read_fs(s):  # 判断FS的结构相关(第一列)
    if s == 'LD' and FS[0][0] == 'no':  # 加载的相关
        return True
    elif s == 'MULT' and FS[1][0] == 'no':  # 乘法相关
        return True
    elif s == 'SUBD' and FS[3][0] == 'no':  # 减法相关
        return True
    elif s == 'DIVD' and FS[4][0] == 'no':  # 除法相关
        return True
    elif s == 'ADDD' and FS[3][0] == 'no':  # 加法相关
        return True
    else:
        return False


# 读取源操作数的状态是否有空闲然后写入
# 读取指令中的两个源操作数的状态看看是否ready，然后写入FS中,还有对应的占用是什么
def read_rs(x1, x2, x):  # 两个源操作数x1,x2; x是第几行
    rs = ["F0", "F2", "F4", "F6", "F8", "F10"]
    if x1 in rs:  # 被占用了
        index1 = rs.index(x1)
        if RS[0][index1] != '':
            if FS[x][7] != 'yes':  # 如果源寄存器状态不为yes，则可以更改为no，一旦写为'yes'，则不可再更改
                FS[x][7] = 'no'
                FS[x][5] = RS[0][index1]  # 在FS对应的位置写上RS的内容
        else:
            FS[x][7] = 'yes'
    else:
        FS[x][7] = 'yes'

    if x2 in rs:  # 被占用了
        index2 = rs.index(x2)  # 查找x2在RS表中的位置并返回下标
        if RS[0][index2] != '':  # 如果不是空的话
            if FS[x][8] != 'yes':  # 如果源寄存器状态不为yes，则可以更改为no，一旦写为'yes'，则不可再更改
                FS[x][8] = 'no'  # 在FS表中写上no
                FS[x][6] = RS[0][index2]  # 在FS表中写上RS对应的内容
        else:
            FS[x][8] = 'yes'
    else:
        FS[x][8] = 'yes'


# 指令发射之后要将目的寄存器占用，然后在RS中写入指令的操作符instruction._op
def write_rs(reg, y):  # 把状态写入对应的寄存器里
    rs = ["F0", "F2", "F4", "F6", "F8", "F10"]
    index = rs.index(reg)  # 找到位置然后写入对应的状态
    RS[0][index] = y


def clear_rs(reg):  # 清除RS
    rs = ["F0", "F2", "F4", "F6", "F8", "F10"]
    index = rs.index(reg)  # 找到位置然后写入对应的状态
    RS[0][index] = ''


root = Tk()
root.title('Scoreboard Algorithm')
root.geometry('700x600')

lb1 = Label(root, text='使用前请点击"帮助"了解使用详情', font=('宋体', 14, 'bold'))
lb1.place(relx=0.01, rely=0.03)

# ---------------------菜单----------------------------------
mainmenu = Menu(root)

menuFile = Menu(mainmenu)  # 菜单分组 menuFile
mainmenu.add_cascade(label='文件', menu=menuFile)
menuFile.add_command(label="打开", command=ope)  # 打开选择文件
menuFile.add_separator()  # 分割线
menuFile.add_command(label="退出", command=root.destroy)

menuEdit = Menu(mainmenu)  # 菜单分组 menuEdit
mainmenu.add_cascade(label='帮助', menu=menuEdit)
menuEdit.add_command(label="help", command=help)

menuAbout = Menu(mainmenu)  # 菜单分组 menuAbout
mainmenu.add_cascade(label='关于', menu=menuAbout)
menuAbout.add_command(label='About', command=about)

root.config(menu=mainmenu)
root.bind('Button-3', popupmenu)  # 根窗体绑定鼠标右击响应事件

# ------------------------鼠标按钮事件-----------------------------------
btn = Button(root, text='运行全部', command=run).place(x=400, y=20)

# ------------------------文本框显示汇编代码 和 运行结果-------------------------------------
txt = Text(root, width=30, height=12)
txt.pack(fill=tkinter.X, side=tkinter.BOTTOM)
txt.insert(END, '此处展示运行代码\n')


# ------------------------带滚动条的文本框------------------------------------------
txt_process = tkinter.scrolledtext.ScrolledText(root, width=92, height=25)
txt_process.place(x=13, y=60)
txt_process.insert(END, '此处展示代码执行过程\n')

root.mainloop()
