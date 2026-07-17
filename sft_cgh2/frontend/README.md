# SFT 前端演示界面

这是 `sft_cgh2` 下的 SFT 验收展示前端原型，当前使用零依赖静态页面实现。新版界面采用侧边导航 + Tab 切换面板，不再是单页长滚动展示。

## 目录

```text
frontend/
├── index.html          页面入口
├── styles.css          页面样式
├── app.js              数据渲染与交互逻辑
└── data/
    └── demo-data.json  当前演示数据
```

## 打开方式

Linux 启动（含前端 + `/repair`）：

```bash
cd /root/siton-tmp/assignment_A
GPU_ID=0 PORT=8081 bash sft_cgh2/scripts/serve.sh
```

Windows PowerShell 隧道（本机 8082 → 服务器 8081）：

```powershell
ssh -N -L 8082:localhost:8081 root@ubuntu-root
```

浏览器打开：

```text
http://localhost:8082/sft_cgh2/frontend/
```

推理台接口默认：`http://127.0.0.1:8082/repair`

## 当前展示内容

- 总览仪表盘：核心指标、项目状态、下一步计划
- 优化闭环：Baseline -> SFT 实验 -> 错误分析 -> Repair SFT
- 实验对比：Base / Best SFT / Repair SFT 的能力定位
- 错误分析：当前 Repair SFT 样本错误类型分布
- 修复案例：可切换查看不同错误样本
- 模型推理台：输入题目、错误代码和失败反馈，调用模型完成代码修复

## 模型推理台

推理台支持两种模式：

1. **演示模式**：接口地址留空，点击“开始修复”后会使用内置案例的参考修复代码进行演示。
2. **真实模型模式**：填入你的模型服务接口地址，前端会发送 POST 请求调用模型。

接口约定：

```http
POST /repair
Content-Type: application/json
```

请求体：

```json
{
  "problem": "题目描述",
  "buggy_code": "错误代码",
  "feedback": "失败测试或报错信息"
}
```

返回体支持以下任一字段：

```json
{
  "fixed_code": "修复后代码"
}
```

或：

```json
{
  "output": "模型输出"
}
```

如果前端和模型服务不是同源，需要模型服务允许浏览器跨域请求。

## 后续接入真实结果

训练完成后，可以逐步替换 `data/demo-data.json` 中的占位字段：

- Base pass@1
- Best SFT pass@1
- Repair SFT repair_pass@1
- 训练 loss 曲线
- 显存和训练时间
- 修复后真实测试结果
- 更多错误分析案例

推荐后续新增：

```text
data/
├── overview.json
├── experiments.json
├── error-analysis.json
├── repair-cases.json
└── training-logs.json
```

当前先保留单文件 `demo-data.json`，便于快速开发和验收演示。
