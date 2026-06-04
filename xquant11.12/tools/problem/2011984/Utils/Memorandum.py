"""备忘录"""

# 同一个值生成一个dict
{}.fromkeys(["a", 'b', 'c'], 20)

# 2个list组成一个dict
a = dict(zip(["a", "b", "c"], [1, 2, 3]))
key, content = list(a.keys()), list(a.values())

# 计算任务运行时间
import time
start = time.perf_counter()
print('running time: {}min'.format(round((time.perf_counter() - start) / 60, 2)))


# 画图
import matplotlib.pyplot as plt
from matplotlib import font_manager, gridspec

myfont = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf')
fig = plt.figure(figsize=(16, 10))
gs = gridspec.GridSpec(4, 2)
ax1 = fig.add_subplot(gs[0:1, 0:1])

plt.tight_layout()
plt.show()


# 画图选取部分坐标轴
# 1. 分钟序列
minute_index = ['09:30', '10:00', '10:30', '11:00', '13:00', '13:30', '14:00', '14:30', '15:00']
from Utils.UtilsPlot import get_x_axis_pos
x_pos_, x_label_ = get_x_axis_pos(minute_index)
plt.xticks(x_pos_, x_label_)
# 2. 日期序列
all_date = ['20210401', '20210402', '20210403']
n = len(all_date)
show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
plt.xticks(show_idx, [all_date[i] for i in show_idx])


# 画图加标题
plt.title('', fontproperties=myfont)
# 画图加文字
pos_x, pos_y, text = 0, 0, ''
plt.text(pos_x, pos_y, text, ha='center', va='bottom', fontdict={'size': 8})

# 导出excel

