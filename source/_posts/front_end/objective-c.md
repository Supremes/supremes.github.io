---
title: Objective-C 面向对象编程详解
date: 2025-11-28 14:30:00
tags:
  - Objective-C
  - iOS
  - 面向对象
  - Category
  - Protocol
categories: 移动开发
description: 深入解析 Objective-C 的面向对象特性，包括 Category、Protocol、Extension 等核心概念，以及 UIViewController 和 UIApplication 的生命周期详解
---

# 面向对象

### 1. **Category（分类）**

**Category** 是 Objective-C 中用于扩展已有类功能的一种机制，无需继承即可为类添加方法。它的主要用途是增强类的功能或将类的实现分模块组织。

#### 特点：
- **无需子类化**：可以在不修改原始类源码的情况下，为类添加新的方法。
- **动态扩展**：Category 在运行时动态地将方法添加到类中。
- **模块化开发**：可以将类的功能拆分成多个文件，便于团队协作或代码管理。
- **限制**：
  - 不能添加实例变量，只能添加方法。
  - 如果 Category 中定义的方法与原始类或另一个 Category 中的方法同名，会覆盖原始方法（可能导致不可预测的行为）。
  - 不能直接访问原始类的私有方法或变量。

#### 语法：
```objc
@interface 原类名 (CategoryName)
// 声明新方法
- (void)newMethod;
@end

@implementation 原类名 (CategoryName)
// 实现新方法
- (void)newMethod {
    NSLog(@"This is a new method added by Category.");
}
@end
```

#### 应用场景：
1. **扩展系统类**：例如，为 `NSString` 添加一个自定义方法：
   ```objc
   @interface NSString (MyExtension)
   - (NSString *)reverseString;
   @end
   
   @implementation NSString (MyExtension)
   - (NSString *)reverseString {
       NSMutableString *reversed = [NSMutableString stringWithCapacity:self.length];
       for (NSInteger i = self.length - 1; i >= 0; i--) {
           [reversed appendString:[NSString stringWithFormat:@"%C", [self characterAtIndex:i]]];
       }
       return reversed;
   }
   @end
   ```
   使用：
   ```objc
   NSString *str = @"Hello";
   NSLog(@"%@", [str reverseString]); // 输出: olleH
   ```

2. **代码组织**：将大类的实现分成多个 Category，增强可读性和维护性。例如，`UIViewController` 可以按功能分为 `DataHandling` 和 `UIConfiguration` 两个 Category。

3. **修复或增强功能**：在不修改第三方库的情况下，为其类添加功能。

#### 注意事项：
- **方法冲突**：如果多个 Category 或原始类定义了同名方法，运行时会选择其中一个（不可预测），应避免命名冲突。
- **调试困难**：Category 的方法覆盖可能导致调试复杂。
- **最佳实践**：为避免冲突，建议在方法名中加入前缀（如 `my_reverseString`）。

---

### 2. **Protocol（协议）**

**Protocol** 是 Objective-C 中定义一组方法规范的机制，类似于接口（interface）。它用于声明一组方法，供类实现，以保证类具有特定行为。

#### 特点：
- **抽象性**：Protocol 仅定义方法签名，不提供实现。
- **多类共享**：多个类可以实现同一个 Protocol，实现代码共享或行为一致性。
- **可选与必须**：方法可以标记为 `@required`（默认，必须实现）或 `@optional`（可选实现）。
- **类型检查**：编译器可以检查类是否遵循某个 Protocol。

#### 语法：
```objc
@protocol MyProtocol <NSObject>
// 必须实现的方法
@required
- (void)requiredMethod;

// 可选实现的方法
@optional
- (void)optionalMethod;
@end

@interface MyClass : NSObject <MyProtocol>
@end

@implementation MyClass
- (void)requiredMethod {
    NSLog(@"Required method implemented.");
}
@end
```

#### 应用场景：
1. **委托模式（Delegate）**：最常见的用途，例如 `UITableViewDelegate` 和 `UITableViewDataSource`。
   ```objc
   @protocol MyDelegate <NSObject>
   @required
   - (void)didCompleteTask;
   @optional
   - (void)progressUpdated:(float)progress;
   @end
   
   @interface MyClass : NSObject
   @property (weak, nonatomic) id<MyDelegate> delegate;
   @end
   ```

2. **接口定义**：定义一组标准接口，供不同类实现。例如，多个视图控制器实现同一个数据处理协议。
3. **类型安全**：通过 Protocol 限制对象类型，确保对象支持特定方法：
   ```objc
   id<MyProtocol> obj = [[MyClass alloc] init];
   [obj requiredMethod]; // 编译器确保方法存在
   ```

#### 注意事项：
- **NSObject 协议**：通常 Protocol 会继承 `<NSObject>` 协议，以确保对象支持基本方法（如 `respondsToSelector:`）。
- **动态检查**：使用 `conformsToProtocol:` 和 `respondsToSelector:` 检查对象是否遵循协议或实现某方法：
   ```objc
   if ([obj conformsToProtocol:@protocol(MyProtocol)]) {
       if ([obj respondsToSelector:@selector(optionalMethod)]) {
           [obj optionalMethod];
       }
   }
   ```

### 3 **Extension（类扩展）**

- **定义**：类扩展是匿名的 Category，通常用于在类的实现文件中声明私有方法或属性。
- **特点**：
  - 可以在 `.m` 文件中声明私有方法或属性。
  - 可以添加实例变量（与 Category 不同）。
  - 仅在当前类实现文件可见，外部无法访问。
- **语法**：
  ```objc
  @interface MyClass ()
  @property (nonatomic, strong) NSString *privateProperty;
  - (void)privateMethod;
  @end
  
  @implementation MyClass
  - (void)privateMethod {
      NSLog(@"This is a private method.");
  }
  @end
  ```
- **用途**：隐藏实现细节，声明私有接口，或为只读属性添加私有读写支持。

### 4  **Dynamic Runtime（运行时动态性）**

- Objective-C 的运行时系统提供了强大的动态特性，支持以下功能：
  - **方法交换（Method Swizzling）**：在运行时替换方法实现，常用于调试或修改系统类行为。
  - **动态添加方法**：通过 `class_addMethod` 动态为类添加方法。
  - **关联对象（Associated Objects）**：通过 `objc_setAssociatedObject` 为 Category 添加“伪属性”。
  - **示例**（添加关联对象）：
    ```objc
    #import <objc/runtime.h>
    @interface NSObject (MyCategory)
    @property (nonatomic, strong) NSString *associatedString;
    @end
    
    @implementation NSObject (MyCategory)
    static char kAssociatedStringKey;
    - (void)setAssociatedString:(NSString *)string {
        objc_setAssociatedObject(self, &kAssociatedStringKey, string, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    - (NSString *)associatedString {
        return objc_getAssociatedObject(self, &kAssociatedStringKey);
    }
    @end
    ```
  - **用途**：增强 Category 功能，实现动态行为修改。

---

### 5. **Category vs Protocol vs 其他方案对比**

| 特性/机制        | Category                 | Protocol             | Extension          | Block              |
| ---------------- | ------------------------ | -------------------- | ------------------ | ------------------ |
| **用途**         | 扩展类方法               | 定义接口规范         | 声明私有方法/属性  | 回调和函数式编程   |
| **添加实例变量** | 否（可通过关联对象实现） | 否                   | 是                 | 否                 |
| **代码复用**     | 高（直接扩展类）         | 中（需实现）         | 低（仅限当前类）   | 高（独立逻辑）     |
| **动态性**       | 高（运行时添加方法）     | 中（运行时检查方法） | 低（编译时确定）   | 高（捕获上下文）   |
| **典型场景**     | 系统类扩展、代码模块化   | 委托模式、接口定义   | 私有接口、属性扩展 | 异步回调、事件处理 |

---

### 6. **总结与建议**
- **Category** 适合快速扩展类功能，特别是为系统类或第三方库添加方法，但需注意方法冲突。
- **Protocol** 适合定义标准接口，确保类行为一致，广泛用于委托模式。
- **Extension** 用于私有接口，适合隐藏实现细节。
- **Block** 提供轻量级回调，适合异步任务。
- **运行时动态性** 提供了强大的灵活性，但需谨慎使用以避免复杂性。

根据具体需求选择合适的方案：
- 如果需要扩展现有类，使用 **Category**。
- 如果需要定义行为规范，使用 **Protocol**。
- 如果需要私有方法或属性，使用 **Extension**。
- 如果需要动态或回调逻辑，考虑 **Block** 或 **运行时特性**。

如需更具体示例或深入探讨某一机制，请告诉我！



# NSURL

## NSURLProtocol

In the context of `WKWebView`, requests are generally **not** handled by `NSURLProtocol`, especially for custom schemes or even for `http/https` in most cases. Apple restricts `NSURLProtocol` usage in `WKWebView` for security and performance reasons.

**However, requests can be handled by `NSURLProtocol` in these scenarios:**

- When using `NSURLConnection` or `NSURLSession` **outside** of `WKWebView`, and you register a custom `NSURLProtocol` class, all matching requests (e.g., `http`, `https`, or custom schemes if registered) will be intercepted by your protocol handler.
- In `UIWebView` (deprecated), `NSURLProtocol` can intercept requests.
- In `WKWebView`, only if you use a custom `NSURLSession` (not the web view’s internal networking), and you register a protocol class on that session’s configuration, then requests made by that session (not the web view) can be intercepted.

**Summary:**  
In `WKWebView`, requests are not forwarded to `NSURLProtocol`. Only network requests made by your own `NSURLSession` or `NSURLConnection` (outside of `WKWebView`) can be intercepted by `NSURLProtocol`.

___

## WKURLSchemeHandler

- 拦截处理自定义 scheme（非 https/http） 

  > 通过实现WKURLSchemeHandler protocol，可以拦截和处理 WKWebView 发起的特定 scheme（如 http/https 以外的自定义协议）请求，实现自定义的网络请求逻辑

- apple 推荐的官方协议，用来处理自定义的 scheme

- **` https/http` 请求无法在 wkwebview 中被拦截处理**

- WKWebview 不支持使用`NSURLProtocol`来拦截请求，forward 到`NSURLSession`是官方推荐可信任的做法

___

## NSURLSessionDelegate

- `WKURLSchemeHandler` 拦截的请求，会被转发到`NSURLSession`， 并通过 NSURLSessionDelegate 进行处理。



# UIViewController

UIViewController的生命周期函数介绍：

## 主要生命周期方法

### 1. `viewDidLoad`
- **调用时机**：视图控制器的视图层次结构加载到内存中后调用
- **用途**：进行一次性初始化，如创建UI元素、设置初始状态
- **特点**：只调用一次

### 2. `viewWillAppear:`
- **调用时机**：视图即将显示前调用
- **用途**：准备显示视图，如刷新数据、重置UI状态
- **特点**：每次视图显示前都会调用

### 3. `viewDidAppear:`
- **调用时机**：视图已经显示后调用
- **用途**：启动动画、开始定时器、注册通知等
- **特点**：每次视图显示后都会调用

### 4. `viewWillDisappear:`
- **调用时机**：视图即将消失前调用
- **用途**：保存数据、暂停操作、验证输入等
- **特点**：每次视图消失前都会调用

### 5. `viewDidDisappear:`
- **调用时机**：视图已经消失后调用
- **用途**：停止定时器、取消网络请求、清理资源等
- **特点**：每次视图消失后都会调用

### 6. `viewDidUnload` (iOS 6之前)
- **调用时机**：内存不足时系统卸载视图
- **用途**：清理视图相关资源
- **特点**：iOS 6后已废弃

## 生命周期顺序

```
创建 → viewDidLoad → viewWillAppear → viewDidAppear
     ↓
显示中的视图
     ↓
viewWillDisappear → viewDidDisappear → 销毁
```

## 最佳实践

- **viewDidLoad**：创建UI、设置委托、初始化数据源
- **viewWillAppear**：刷新界面数据、重置状态
- **viewDidAppear**：开始网络请求、启动动画
- **viewWillDisappear**：保存用户输入、暂停活动
- **viewDidDisappear**：清理资源、停止后台任务



# UIApplication

## UIViewController 和 UIApplication 的关系

### 层次关系
- **UIApplication**：应用程序的单例对象，管理整个应用的生命周期
- **UIViewController**：管理单个视图的控制器，是UIApplication管理的视图层次结构的一部分

### 包含关系
```
UIApplication
├── UIWindow
    ├── Root UIViewController
        ├── Child UIViewController
        └── Presented UIViewController
```

## 生命周期函数对应关系

### UIApplication 生命周期方法（AppDelegate）

#### 1. `application:didFinishLaunchingWithOptions:`
- **对应UIViewController**：在root view controller的`viewDidLoad`之前调用
- **关系**：应用启动完成 → 创建window和root view controller

#### 2. `applicationDidBecomeActive:`
- **对应UIViewController**：当前可见view controller的`viewWillAppear:`和`viewDidAppear:`
- **关系**：应用变为活跃状态 → 视图控制器开始显示

#### 3. `applicationWillResignActive:`
- **对应UIViewController**：当前可见view controller的`viewWillDisappear:`
- **关系**：应用即将失去焦点 → 视图即将不可交互

#### 4. `applicationDidEnterBackground:`
- **对应UIViewController**：当前可见view controller的`viewDidDisappear:`
- **关系**：应用进入后台 → 视图完全不可见

#### 5. `applicationWillEnterForeground:`
- **对应UIViewController**：即将显示的view controller的`viewWillAppear:`
- **关系**：应用即将回到前台 → 视图即将重新显示

#### 6. `applicationWillTerminate:`
- **对应UIViewController**：所有view controller的清理工作
- **关系**：应用即将终止 → 所有视图控制器被销毁

## 调用顺序示例

### 应用启动
```
1. application:didFinishLaunchingWithOptions:
2. viewDidLoad (root ViewController)
3. viewWillAppear: (root ViewController) 
4. applicationDidBecomeActive:
5. viewDidAppear: (root ViewController)
```

### 应用进入后台
```
1. applicationWillResignActive:
2. viewWillDisappear: (current ViewController)
3. applicationDidEnterBackground:
4. viewDidDisappear: (current ViewController)
```

### 应用回到前台
```
1. applicationWillEnterForeground:
2. viewWillAppear: (current ViewController)
3. applicationDidBecomeActive:
4. viewDidAppear: (current ViewController)
```

## 实际应用建议

- **UIApplication级别**：处理全局状态、推送通知、应用级别的数据保存
- **UIViewController级别**：处理界面相关的逻辑、用户交互、视图状态管理
- **协调使用**：在AppDelegate中可以通知当前的view controller应用状态变化
