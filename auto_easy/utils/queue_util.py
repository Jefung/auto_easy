import time
from collections import deque


class TimeSortedQueue:
    def __init__(self, max_size):
        """
        初始化 TimeSortedQueue 类

        :param max_size: 队列的最大长度
        """
        self.max_size = max_size
        self.queue = deque()  # 使用deque作为底层数据结构实现队列

    def put(self, data):
        """
        将数据放入队列，按照写入时间排序，若超过队列最大长度，则废弃最老的数据

        :param data: 要放入队列的任意类型数据
        """
        cur_time_ms = int(time.time() * 1000)  # 获取当前时间戳
        element = (cur_time_ms, data)  # 将时间戳和数据组成元组
        self.queue.append(element)  # 先添加到队列末尾
        self.queue = deque(sorted(self.queue, key=lambda x: x[0]))  # 按照时间戳对队列元素重新排序
        if len(self.queue) > self.max_size:
            self.queue.popleft()  # 移除最老的数据（队列头部元素）

    def get_all(self, max_lag_ms=-1, oldest_lag_ms=-1, desc=False):
        """
        返回队列中的所有元素以及对应的写入时间

        :return: 包含元素和写入时间的元组列表，按照写入时间从早到晚排序
        """
        ans = []
        cur_time_ms = int(time.time() * 1000)
        ts_list = []
        for item in list(self.queue):
            item_time_ms = item[0]
            item_val = item[1]
            if max_lag_ms == -1 or cur_time_ms - item_time_ms <= max_lag_ms:
                ans.append(item_val)
                ts_list.append(item_time_ms)

        if oldest_lag_ms >= 0 and len(ts_list) > 0 and cur_time_ms - min(ts_list) < oldest_lag_ms:
            return []

        if desc:
            return list(ans)
        return list(reversed(ans))

    def get_queue_vals(self):
        return list(reversed(list(self.queue)))

    def get(self, max_lag_ms=-1):
        if len(self.queue) == 0:
            return None
        newest = list(reversed(list(self.queue)))[0]
        newest_time_ms = newest[0]
        newest_val = newest[1]
        cur_time_ms = int(time.time() * 1000)
        if max_lag_ms <= 0 or cur_time_ms - newest_time_ms <= max_lag_ms:
            return newest_val
        return None

    def __iter__(self):
        """
        实现迭代器协议，使得类的实例可以被迭代，按写入时间顺序遍历元素和时间戳
        """
        return iter(self.queue)


if __name__ == '__main__':
    pass
    queue_obj = TimeSortedQueue(max_size=5)
    for i in range(10):
        time.sleep(0.05)
        queue_obj.put(f"element_{i}")
        # print(queue_obj.get())

    # 遍历队列元素和写入时间
    for element in queue_obj:
        print(element)

    # 获取所有元素和写入时间
    print(queue_obj.get_all())
