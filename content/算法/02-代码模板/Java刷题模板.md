---
title: Java 算法刷题模板
date: 2026-08-09
tags:
  - 面试
  - 算法
  - Java
---
# Java 算法刷题模板
只保留面试手写高频 API、13 类套路骨架，以及数组 / 字符串 / 数学的基础 API / 专项映射；题号优先对齐远程 leetcode-tracker 的 P0/P1，缺位时保留 P2 锚点。
## 01. Java 高频 API

```java
// 数组 / 字符串
int n = nums.length;
Arrays.sort(nums);
Arrays.fill(dp, INF);
char c = s.charAt(i);
int len = s.length();
char[] cs = s.toCharArray();
String sub = s.substring(l, r);      // [l, r)
StringBuilder sb = new StringBuilder();
sb.append(x);
sb.deleteCharAt(sb.length() - 1);
sb.reverse();
String t = sb.toString();
// List / Map / Set
List<Integer> list = new ArrayList<>();
list.add(x);
list.get(i);
list.set(i, x);
list.remove(list.size() - 1);
Map<Integer, Integer> map = new HashMap<>();
map.put(k, v);
map.get(k);
map.getOrDefault(k, 0);
map.putIfAbsent(k, v);
map.containsKey(k);
Set<Integer> set = new HashSet<>();
set.add(x);
set.contains(x);
// Deque / Queue：栈和普通队列都优先 ArrayDeque
Deque<Integer> stack = new ArrayDeque<>();
stack.push(x);
stack.pop();
stack.peek();
Queue<int[]> q = new ArrayDeque<>();
q.offer(new int[]{x, y});
q.poll();
q.peek();
// PriorityQueue：默认小顶堆；比较器别写 a - b
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
PriorityQueue<Integer> maxHeap = new PriorityQueue<>((a, b) -> Integer.compare(b, a));
PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[1], b[1]));
// 排序 / 比较器
list.sort((a, b) -> Integer.compare(a, b));
Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
Arrays.sort(words, (a, b) -> {
    if (a.length() != b.length()) return Integer.compare(a.length(), b.length());
    return a.compareTo(b);
});
```

- `int[]` 不能直接 `Arrays.asList(nums)`；频繁改字符串用 `StringBuilder`。
- `poll()/peek()` 比 `remove()/element()` 更稳；栈和队列优先 `ArrayDeque`。

## 01.5 数组 / 字符串 / 数学专项映射

- **数组**：先分有序 / 原地 / 区间 / 矩阵 / Top K，再回落到双指针、前缀和、栈、堆、图/网格或模拟；热手题可用 `31 / 48 / 56 / 238`。
- **字符串**：先分频次 / 窗口 / 回文 / 翻转，再回落到哈希、滑窗、双指针、DP；热手题可用 `5 / 438 / 151`。
- **数学**：重点只补 `long`、溢出判断、快速幂、开方边界；题型通常回落到模拟、二分、递归，不单开冗长模板。

## 02. 哈希
题：LC 1 两数之和（P0）、LC 49 字母异位词分组（P0）

```java
Map<Integer, Integer> first = new HashMap<>();
for (int i = 0; i < nums.length; i++) {
    int need = target - nums[i];
    if (first.containsKey(need)) return new int[]{first.get(need), i};
    first.putIfAbsent(nums[i], i);
}
Map<String, List<String>> groups = new HashMap<>();
for (String s : strs) {
    char[] cs = s.toCharArray();
    Arrays.sort(cs);
    String key = new String(cs);
    groups.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
}
return new ArrayList<>(groups.values());
```

- `getOrDefault` 做计数，`putIfAbsent` 保留最早位置。

## 03. 双指针
题：LC 15 三数之和（P0）、LC 283 移动零（P0）

```java
Arrays.sort(nums);
for (int i = 0; i < nums.length - 2; i++) {
    if (i > 0 && nums[i] == nums[i - 1]) continue;
    int l = i + 1, r = nums.length - 1;
    while (l < r) {
        int sum = nums[i] + nums[l] + nums[r];
        if (sum == 0) {
            ans.add(List.of(nums[i], nums[l], nums[r]));
            l++;
            r--;
            while (l < r && nums[l] == nums[l - 1]) l++;
            while (l < r && nums[r] == nums[r + 1]) r--;
        } else if (sum < 0) {
            l++;
        } else {
            r--;
        }
    }
}

int slow = 0;
for (int fast = 0; fast < nums.length; fast++) {
    if (nums[fast] != 0) {
        int tmp = nums[slow];
        nums[slow++] = nums[fast];
        nums[fast] = tmp;
    }
}
```

- 有序数组常用 `l/r` 相向；原地覆盖/去重常用 `slow/fast`。

## 04. 滑动窗口
题：LC 3 无重复字符的最长子串（P0）、LC 76 最小覆盖子串（P1）

```java
// 不定长窗口：先扩右，再按条件收左
Map<Character, Integer> cnt = new HashMap<>();
int l = 0, ans = 0;
for (int r = 0; r < s.length(); r++) {
    char c = s.charAt(r);
    cnt.put(c, cnt.getOrDefault(c, 0) + 1);
    while (cnt.get(c) > 1) {
        char left = s.charAt(l++);
        cnt.put(left, cnt.get(left) - 1);
    }
    ans = Math.max(ans, r - l + 1);
}
// 定长窗口：长度固定为 k
for (int r = 0, l = 0; r < nums.length; r++) {
    add(nums[r]);
    if (r - l + 1 > k) remove(nums[l++]);
    if (r - l + 1 == k) updateAnswer();
}
```

- 先扩右再按条件收左；移出左端元素时先更新计数。

## 05. 前缀和
题：LC 560 和为 K 的子数组（P0，远程当前仅此类锚点）

```java
Map<Integer, Integer> cnt = new HashMap<>();
cnt.put(0, 1);
int pre = 0, ans = 0;
for (int x : nums) {
    pre += x;
    ans += cnt.getOrDefault(pre - k, 0);
    cnt.put(pre, cnt.getOrDefault(pre, 0) + 1);
}
return ans;
```

- 先查 `pre - k`，后加入当前 `pre`；`cnt.put(0, 1)` 别漏。

## 06. 链表
题：LC 206 反转链表（P0）、LC 142 环形链表 II（P1）

```java
// dummy：统一处理头结点变化
ListNode dummy = new ListNode(0, head);
ListNode slow = dummy, fast = dummy;
for (int i = 0; i < n; i++) fast = fast.next;
while (fast.next != null) {
    slow = slow.next;
    fast = fast.next;
}
slow.next = slow.next.next;
return dummy.next;
// 迭代反转
ListNode prev = null, cur = head;
while (cur != null) {
    ListNode next = cur.next;
    cur.next = prev;
    prev = cur;
    cur = next;
}
return prev;
// 快慢指针找环入口
ListNode p1 = head, p2 = head;
while (p2 != null && p2.next != null) {
    p1 = p1.next;
    p2 = p2.next.next;
    if (p1 == p2) break;
}
if (p2 == null || p2.next == null) return null;
for (ListNode p = head; p != p1; p = p.next, p1 = p1.next) {}
return p1;
```

- 需要改头时先想 `dummy`；判空永远看 `fast != null && fast.next != null`。

## 07. 二叉树
题：LC 104 二叉树的最大深度（P0）、LC 199 二叉树的右视图（P1）

```java
// DFS：前中后序都只是在递归返回前后插逻辑
int dfs(TreeNode root) {
    if (root == null) return 0;
    int left = dfs(root.left);
    int right = dfs(root.right);
    return Math.max(left, right) + 1;
}
// BFS：层序模板
List<List<Integer>> levelOrder(TreeNode root) {
    if (root == null) return new ArrayList<>();
    Queue<TreeNode> q = new ArrayDeque<>();
    q.offer(root);
    List<List<Integer>> ans = new ArrayList<>();

    while (!q.isEmpty()) {
        int size = q.size();
        List<Integer> level = new ArrayList<>(size);
        for (int i = 0; i < size; i++) {
            TreeNode node = q.poll();
            level.add(node.val);
            if (node.left != null) q.offer(node.left);
            if (node.right != null) q.offer(node.right);
        }
        ans.add(level);
    }
    return ans;
}
```

- DFS 先定义返回值含义；BFS 每层先记 `size = q.size()`。

## 08. 图/网格
题：LC 200 岛屿数量（P0）、LC 207 课程表（P1）

```java
int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

// 网格 DFS
void dfs(char[][] grid, int x, int y) {
    if (x < 0 || x >= grid.length || y < 0 || y >= grid[0].length) return;
    if (grid[x][y] != '1') return;
    grid[x][y] = '0';
    for (int[] d : dirs) dfs(grid, x + d[0], y + d[1]);
}
// 网格 BFS：入队即标记
Queue<int[]> q = new ArrayDeque<>();
q.offer(new int[]{sx, sy});
visited[sx][sy] = true;
while (!q.isEmpty()) {
    int[] cur = q.poll();
    for (int[] d : dirs) {
        int nx = cur[0] + d[0], ny = cur[1] + d[1];
        if (nx < 0 || nx >= m || ny < 0 || ny >= n) continue;
        if (visited[nx][ny] || blocked(nx, ny)) continue;
        visited[nx][ny] = true;
        q.offer(new int[]{nx, ny});
    }
}
// 拓扑排序 BFS
Queue<Integer> zeroIn = new ArrayDeque<>();
for (int i = 0; i < n; i++) if (indegree[i] == 0) zeroIn.offer(i);
int seen = 0;
while (!zeroIn.isEmpty()) {
    int u = zeroIn.poll();
    seen++;
    for (int v : graph[u]) {
        if (--indegree[v] == 0) zeroIn.offer(v);
    }
}
return seen == n;
```

- DFS 改原数组时最省 `visited`；BFS 一定“入队即标记”。

## 09. 回溯
题：LC 46 全排列（P0）、LC 39 组合总和（P1）

```java
// 子集 / 组合
List<List<Integer>> ans = new ArrayList<>();
List<Integer> path = new ArrayList<>();
void dfs(int start) {
    ans.add(new ArrayList<>(path));
    for (int i = start; i < nums.length; i++) {
        if (i > start && nums[i] == nums[i - 1]) continue;
        path.add(nums[i]);
        dfs(i + 1);         // 组合总和改成 dfs(i)
        path.remove(path.size() - 1);
    }
}
// 全排列
boolean[] used = new boolean[nums.length];
void perm() {
    if (path.size() == nums.length) {
        ans.add(new ArrayList<>(path));
        return;
    }
    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue;
        used[i] = true;
        path.add(nums[i]);
        perm();
        path.remove(path.size() - 1);
        used[i] = false;
    }
}
```

- 回溯固定三件事：选、递归、撤销；去重通常先排序。

## 10. 二分
题：LC 35 搜索插入位置（P0）、LC 34 在排序数组中查找首尾位置（P1）

```java
int lowerBound(int[] nums, int target) {
    int l = 0, r = nums.length;
    while (l < r) {
        int m = l + (r - l) / 2;
        if (nums[m] >= target) r = m;
        else l = m + 1;
    }
    return l;
}
int upperBound(int[] nums, int target) {
    int l = 0, r = nums.length;
    while (l < r) {
        int m = l + (r - l) / 2;
        if (nums[m] > target) r = m;
        else l = m + 1;
    }
    return l;
}
```

- 边界二分统一用左闭右开 `[l, r)`；命中不要 `return`，继续压边界。

## 11. 栈
题：LC 20 有效的括号（P0）、LC 739 每日温度（P1）

```java
// 括号匹配
Deque<Character> st = new ArrayDeque<>();
for (char c : s.toCharArray()) {
    if (c == '(' || c == '[' || c == '{') {
        st.push(c);
    } else {
        if (st.isEmpty()) return false;
        char open = st.pop();
        if ((c == ')' && open != '(') ||
            (c == ']' && open != '[') ||
            (c == '}' && open != '{')) return false;
    }
}
return st.isEmpty();
// 单调栈：通常压下标，不压值
Deque<Integer> mono = new ArrayDeque<>();
for (int i = 0; i < nums.length; i++) {
    while (!mono.isEmpty() && nums[i] > nums[mono.peek()]) {
        int idx = mono.pop();
        ans[idx] = nums[i];
    }
    mono.push(i);
}
```

- 单调栈通常压下标；栈题优先 `ArrayDeque`，不要用 `Stack`。

## 12. 堆
题：LC 215 数组中的第 K 个最大元素（P0）、LC 295 数据流的中位数（P2）

```java
// Top K：维护大小为 k 的小顶堆
PriorityQueue<Integer> minHeap = new PriorityQueue<>();
for (int x : nums) {
    minHeap.offer(x);
    if (minHeap.size() > k) minHeap.poll();
}
return minHeap.peek();
// 词频 / 二元组
PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> Integer.compare(a[1], b[1]));
for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
    pq.offer(new int[]{e.getKey(), e.getValue()});
    if (pq.size() > k) pq.poll();
}
```

- 前 K 大用小顶堆；数据流中位数改双堆；比较器一律 `Integer.compare(...)`。

## 13. 贪心
题：LC 55 跳跃游戏（P0）、LC 122 买卖股票的最佳时机 II（P1）

```java
// 可达性：维护当前最远边界
int farthest = 0;
for (int i = 0; i < nums.length; i++) {
    if (i > farthest) return false;
    farthest = Math.max(farthest, i + nums[i]);
}
return true;
// 累加局部最优：所有正收益都拿走
int profit = 0;
for (int i = 1; i < prices.length; i++) {
    if (prices[i] > prices[i - 1]) {
        profit += prices[i] - prices[i - 1];
    }
}
return profit;
```

- 贪心先问当前这一步最不吃亏什么；跳跃类盯最远边界，股票 II 盯相邻正收益。

## 14. DP
题：LC 70 爬楼梯（P0）、LC 72 编辑距离（P1）

```java
// 1D DP：先定义 dp[i] 含义，再填初值
int[] dp = new int[n + 1];
dp[0] = 1;
dp[1] = 1;
for (int i = 2; i <= n; i++) {
    dp[i] = dp[i - 1] + dp[i - 2];
}
// 2D DP：编辑距离
int m = word1.length(), n = word2.length();
int[][] dp2 = new int[m + 1][n + 1];
for (int i = 0; i <= m; i++) dp2[i][0] = i;
for (int j = 0; j <= n; j++) dp2[0][j] = j;
for (int i = 1; i <= m; i++) {
    for (int j = 1; j <= n; j++) {
        if (word1.charAt(i - 1) == word2.charAt(j - 1)) {
            dp2[i][j] = dp2[i - 1][j - 1];
        } else {
            dp2[i][j] = 1 + Math.min(dp2[i - 1][j - 1],
                Math.min(dp2[i - 1][j], dp2[i][j - 1]));
        }
    }
}
```

- DP 最容易错在初始化：`dp[0]`、第一行、第一列先想清。
