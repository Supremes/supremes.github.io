---
title: Python 算法刷题模板
date: 2026-08-09
tags:
  - 面试
  - 算法
  - Python
---
# Python 算法刷题模板

只保留面试手写高频 API、13 类套路骨架，以及数组 / 字符串 / 数学的专项映射。先在[套路速记](../01-套路速记/刷题笔记.md)完成判型，再来找代码骨架。

## 01. Python 高频 API

```python
from collections import Counter, defaultdict, deque
from heapq import heappush, heappop, heapify
from bisect import bisect_left, bisect_right
from math import inf

# 列表 / 字符串
n = len(nums)
nums.sort()                        # 原地排序
ordered = sorted(nums, reverse=True)
chars = list(s)
text = "".join(chars)
rev = s[::-1]

for i, x in enumerate(nums):
    pass
for a, b in zip(nums, nums[1:]):
    pass

# 字典 / 集合 / 计数
freq = Counter(nums)
groups = defaultdict(list)
seen = set()
value = mapping.get(key, 0)

# 双端队列：同时承担队列和栈
q = deque()
q.append(x)
q.popleft()
q.appendleft(x)
q.pop()

# heapq 默认小顶堆；大顶堆存负数
heap = nums[:]
heapify(heap)
heappush(heap, x)
smallest = heappop(heap)

max_heap = []
heappush(max_heap, -x)
largest = -heappop(max_heap)

# 自定义排序
intervals.sort(key=lambda item: (item[0], item[1]))
words.sort(key=lambda word: (len(word), word))
```

- `range(l, r)` 是左闭右开；整除用 `//`。
- 不要写 `grid = [[0] * n] * m`，各行会引用同一个列表；应写 `[[0] * n for _ in range(m)]`。
- 函数默认参数不要用可变对象：用 `path=None`，再在函数内初始化。
- Python 整数不会溢出，但下标、负数整除和浮点比较仍要检查。
- 栈和队列统一优先 `deque`；只有 Top K、动态最值才用 `heapq`。

## 01.5 数组 / 字符串 / 数学专项映射

- **数组**：有序/原地 → 双指针；区间和 → 前缀和；矩阵 → 模拟或图；Top K → 堆。
- **字符串**：频次 → 哈希；连续子串 → 滑窗；回文 → 双指针或 DP。
- **数学**：快速幂、最大公约数、取模、开方边界；能证明单调时优先二分。

## 02. 哈希

题：LC 1 两数之和（P0）、LC 49 字母异位词分组（P0）

```python
def two_sum(nums, target):
    first = {}
    for i, x in enumerate(nums):
        need = target - x
        if need in first:
            return [first[need], i]
        first.setdefault(x, i)
    return []


def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```

- 依赖“之前见过什么”时先查后存。
- 字典 key 必须可哈希；列表要转成元组。

## 03. 双指针

题：LC 15 三数之和（P0）、LC 283 移动零（P0）

```python
def three_sum(nums):
    nums.sort()
    ans = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                ans.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
    return ans


def move_zeroes(nums):
    slow = 0
    for fast, x in enumerate(nums):
        if x != 0:
            nums[slow], nums[fast] = nums[fast], nums[slow]
            slow += 1
```

- 对撞指针先确认数据有序；快慢指针先定义 `slow` 的含义。
- 去重必须区分固定指针去重和左右指针去重。

## 04. 滑动窗口

题：LC 3 无重复字符的最长子串（P0）、LC 76 最小覆盖子串（P1）

```python
def length_of_longest_substring(s):
    count = defaultdict(int)
    left = ans = 0

    for right, ch in enumerate(s):
        count[ch] += 1
        while count[ch] > 1:
            count[s[left]] -= 1
            left += 1
        ans = max(ans, right - left + 1)
    return ans
```

通用顺序：

```python
left = 0
for right, x in enumerate(nums):
    # x 入窗口
    while window_is_invalid:
        # nums[left] 出窗口
        left += 1
    # 在窗口合法时更新答案
```

- “最长合法窗口”通常合法后更新；“最短覆盖窗口”通常收缩前/中更新。
- 数组含负数且要求和恰好为 `k` 时，优先前缀和，不要硬套窗口。

## 05. 前缀和

题：LC 560 和为 K 的子数组（P0）

```python
def subarray_sum(nums, k):
    freq = defaultdict(int)
    freq[0] = 1
    prefix = ans = 0

    for x in nums:
        prefix += x
        ans += freq[prefix - k]
        freq[prefix] += 1
    return ans
```

- `freq[0] = 1` 表示从下标 `0` 开始的子数组。
- 求数量存出现次数；求最长长度通常存最早下标。

## 06. 链表

题：LC 206 反转链表（P0）、LC 19 删除倒数第 N 个结点（P1）

```python
def reverse_list(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev, cur = cur, nxt
    return prev


def remove_nth_from_end(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next
```

- 头节点可能变化就先上 `dummy`。
- 改 `next` 前先保存后继节点。

## 07. 二叉树

题：LC 104 二叉树最大深度（P0）、LC 102 层序遍历（P0）

```python
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))


def level_order(root):
    if not root:
        return []

    ans, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            node = q.popleft()
            level.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        ans.append(level)
    return ans
```

- DFS 先明确“函数返回给父节点什么”。
- BFS 每轮先固定 `len(q)`，再处理这一层。

## 08. 图 / 网格

题：LC 200 岛屿数量（P0）、LC 207 课程表（P1）

```python
def num_islands(grid):
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])

    def dfs(r, c):
        if not (0 <= r < rows and 0 <= c < cols):
            return
        if grid[r][c] != "1":
            return
        grid[r][c] = "0"
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dfs(r + dr, c + dc)

    ans = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                ans += 1
                dfs(r, c)
    return ans


def can_finish(num_courses, prerequisites):
    graph = [[] for _ in range(num_courses)]
    indegree = [0] * num_courses
    for course, pre in prerequisites:
        graph[pre].append(course)
        indegree[course] += 1

    q = deque(i for i, degree in enumerate(indegree) if degree == 0)
    done = 0
    while q:
        node = q.popleft()
        done += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)
    return done == num_courses
```

- BFS/DFS 都要尽早标记，避免重复入队或递归。
- 网格 DFS 可能触发 Python 递归深度限制；深图优先改迭代。

## 09. 回溯

题：LC 46 全排列（P0）、LC 39 组合总和（P1）

```python
def permute(nums):
    ans, path = [], []
    used = [False] * len(nums)

    def dfs():
        if len(path) == len(nums):
            ans.append(path.copy())
            return
        for i, x in enumerate(nums):
            if used[i]:
                continue
            used[i] = True
            path.append(x)
            dfs()
            path.pop()
            used[i] = False

    dfs()
    return ans
```

组合类只需把循环起点改成 `start`：

```python
def dfs(start):
    for i in range(start, len(nums)):
        path.append(nums[i])
        dfs(i + 1)
        path.pop()
```

- 收集答案时用 `path.copy()`，不能直接存 `path`。
- 排列用 `used`；组合用 `start`；有重复元素时做同层去重。

## 10. 二分

题：LC 35 搜索插入位置（P0）、LC 34 查找首尾位置（P1）

```python
def lower_bound(nums, target):
    left, right = 0, len(nums)       # [left, right)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] >= target:
            right = mid
        else:
            left = mid + 1
    return left
```

答案二分：

```python
def binary_search_answer(min_answer, max_answer):
    left, right = min_answer, max_answer
    while left < right:
        mid = (left + right) // 2
        if check(mid):
            right = mid
        else:
            left = mid + 1
    return left
```

- 可以直接用 `bisect_left(nums, target)`，但面试要会手写边界。
- 先固定区间定义，不要混用 `[l, r]` 和 `[l, r)`。

## 11. 栈 / 单调栈

题：LC 20 有效的括号（P0）、LC 739 每日温度（P1）

```python
def daily_temperatures(temperatures):
    ans = [0] * len(temperatures)
    stack = []                       # 存下标，温度单调递减

    for i, value in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < value:
            prev = stack.pop()
            ans[prev] = i - prev
        stack.append(i)
    return ans
```

- 需要计算距离时栈里存下标。
- 弹栈条件中的 `<`、`<=` 决定相等元素如何处理。

## 12. 堆

题：LC 215 数组中的第 K 个最大元素（P0）、LC 295 数据流中位数（P2）

```python
def find_kth_largest(nums, k):
    heap = []
    for x in nums:
        heappush(heap, x)
        if len(heap) > k:
            heappop(heap)
    return heap[0]
```

- 第 K 大：小顶堆保留 K 个最大值。
- `heapq` 只保证堆顶最小，不保证整个列表有序。

## 13. 贪心

题：LC 55 跳跃游戏（P0）、LC 56 合并区间（数组 P0）

```python
def can_jump(nums):
    farthest = 0
    for i, step in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + step)
    return True


def merge(intervals):
    intervals.sort(key=lambda item: item[0])
    ans = []
    for start, end in intervals:
        if not ans or ans[-1][1] < start:
            ans.append([start, end])
        else:
            ans[-1][1] = max(ans[-1][1], end)
    return ans
```

- 贪心必须能说明局部选择为什么不会损失全局最优。
- 区间题先按起点或终点排序，再明确合并/选择规则。

## 14. DP

题：LC 198 打家劫舍（P0）、LC 322 零钱兑换（P1）

一维 DP / 滚动变量：

```python
def rob(nums):
    prev2 = prev1 = 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1
```

二维 DP：

```python
rows, cols = len(grid), len(grid[0])
dp = [[0] * cols for _ in range(rows)]
dp[0][0] = grid[0][0]

for r in range(rows):
    for c in range(cols):
        if r == 0 and c == 0:
            continue
        up = dp[r - 1][c] if r > 0 else inf
        left = dp[r][c - 1] if c > 0 else inf
        dp[r][c] = min(up, left) + grid[r][c]
```

- 先用一句话定义 `dp[i]` / `dp[i][j]`，再写转移。
- 一维压缩时，遍历方向必须服从依赖关系。
- Python 二维数组必须用列表推导创建，不能使用共享行引用。

## 面试前最后检查

- 能否在 30 秒内完成判型，并说出目标复杂度？
- 能否脱离 IDE 写出当前语言的最小骨架？
- 是否检查了空输入、单元素、重复值、负数、越界与可变对象引用？
- Python 是否误用了共享二维列表、可变默认参数或错误的堆方向？
