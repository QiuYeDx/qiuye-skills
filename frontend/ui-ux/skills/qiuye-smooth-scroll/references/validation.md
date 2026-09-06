# 浏览器验收

根据项目实际存在的功能选择场景。类型检查与构建只证明静态集成，截图不能证明滚动连续。优先使用已有浏览器测试工具，不为执行 Skill 固定安装某个测试框架。

## 输入与位置

在可继续滚动的页面中部输入一格 wheel，记录原生 scroll 事件的时间和 scrollY：应有多个中间位置、单向时不反跳，最终距离与规范化后的输入一致。不要要求恰好 30 次事件或固定帧率；显示器刷新率、缩放、输入 deltaMode 和机器负载都会影响采样。

Playwright 示例（复用测试项目已有 page，页面足够长，鼠标位于普通内容上）：

```ts
await page.evaluate(() => window.scrollTo({ top: 200, behavior: "instant" }));
await page.waitForTimeout(100);
await page.mouse.move(200, 200);
const samplesPromise = page.evaluate(() => new Promise<number[]>((resolve) => {
  const samples: number[] = [];
  const onScroll = () => samples.push(window.scrollY);
  window.addEventListener("scroll", onScroll, { passive: true });
  setTimeout(() => {
    window.removeEventListener("scroll", onScroll);
    resolve(samples);
  }, 1000);
}));
await page.mouse.wheel(0, 120);
const samples = await samplesPromise;
// 验证多个中间位置，最终约 320px；保留设备像素舍入容差。
```

## 关键场景

| 场景 | 需要看到的结果 |
| --- | --- |
| 连续滚轮与中途反向 | 总距离合理，响应及时，可打断，无长时间漂移 |
| Motion/3D/sticky | 真实坐标连续，动画同步；不引入第二层明显延迟 |
| 惯性中原生 instant / smooth scrollTo | 外部目标生效，旧惯性不拉回或取消新动画 |
| scrollBy / 坐标重载 / scrollIntoView / root scrollTo | 保留语义、落点和作用域；容器内部 API 不误滚页面 |
| Home/End/PageDown/空格/Tab、滚动条拖动 | 原生输入能接管，焦点滚动不被拉回 |
| 锚点、已有目录 | URL/历史/焦点行为正常，scroll-margin 保持，修饰键点击不误拦截 |
| 列表分页与路由前进/返回 | 不多一次归零，恢复位置合理，实例无重复 |
| 嵌套代码块、菜单、图表 | 内部按自己的规则滚动/缩放，边界不意外滚背景 |
| 真实弹窗、图片放大、嵌套锁 | 打开即取消残余惯性；关闭最后一个锁后恢复 |
| reduced-motion 动态切换 | 停用自定义惯性；切回可恢复，不残留监听或样式 |
| 页面隐藏/恢复、resize、异步内容增高 | 无旧目标跳动；尺寸正确；恢复后能继续输入 |
| 卸载/重挂载 | 监听、observer、RAF、方法包装清理；没有多实例 |

## 性能与平台

检查空闲时控制器是否继续调度 RAF，而不是把页面其他动画的 RAF 误判为本控制器。测量实际 wheel 手感、惯性尾部、反向响应；检查多层 DOM 输入开销和滚动相关消费者的开销。

至少在任务目标浏览器验证。Windows Chromium + 自动化移动视口只能证明该环境；若交付要求覆盖 Safari/iOS、Firefox 或触控板，则单独测试这些输入与平台。明确报告尚未验证的范围，不用通过构建代替。

回归失败时先定位：输入归属、时钟、真实坐标、程序化交接、锁生命周期、路由恢复，最后才调整 lerp。不要用更长 duration 掩盖主线程卡顿或错误的滚动所有权。
