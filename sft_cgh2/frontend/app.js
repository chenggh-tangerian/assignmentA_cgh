/**
 * SFT 验收展示前端逻辑。
 *
 * 输入:
 *   ./data/demo-data.json  演示数据（overview / stages / experiments / repairCases 等）
 *   可选: api-endpoint 输入框中的模型修复接口 URL
 *
 * 输出:
 *   更新页面各 Tab 的 DOM（指标、实验、错误分布、修复案例、交互演示）
 *   演示模式返回占位修复代码；真实模式展示接口返回的 fixed_code
 */

/** 页面全局状态：数据、当前案例、当前 Tab */
const state = {
  data: null,
  selectedCaseIndex: 0,
  activeTab: "dashboard",
};

/** HTML 转义，防止 XSS */
const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

/** 按 id 取 DOM 元素 */
const byId = (id) => document.getElementById(id);

/** 拉取 demo-data.json */
async function loadData() {
  const response = await fetch("./data/demo-data.json");
  if (!response.ok) {
    throw new Error(`Failed to load demo data: ${response.status}`);
  }
  return response.json();
}

/** 渲染总览标题与指标卡片 */
function renderOverview(data) {
  byId("page-title").textContent = data.overview.title;
  byId("page-subtitle").textContent = data.overview.subtitle;
  byId("project-status").textContent = data.overview.status;

  byId("metric-grid").innerHTML = data.overview.metrics
    .map(
      (metric) => `
        <article class="metric-card">
          <span>${escapeHtml(metric.label)}</span>
          <strong>${escapeHtml(metric.value)}</strong>
          <p>${escapeHtml(metric.note)}</p>
        </article>
      `,
    )
    .join("");
}

/** 切换侧边导航 Tab */
function setActiveTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".nav-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });
}

/** 渲染阶段列表 */
function renderStages(data) {
  byId("stage-list").innerHTML = data.stages
    .map(
      (stage, index) => `
        <article class="stage-card">
          <div class="stage-index">${index + 1}</div>
          <div>
            <h3>${escapeHtml(stage.name)}</h3>
            <p>${escapeHtml(stage.description)}</p>
            <div class="tag-list">
              ${stage.deliverables.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("")}
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

/** 渲染实验卡片列表 */
function renderExperiments(data) {
  byId("experiment-list").innerHTML = data.experiments
    .map(
      (experiment) => `
        <article class="experiment-card">
          <h3>${escapeHtml(experiment.model)}</h3>
          <p><strong>输入：</strong>${escapeHtml(experiment.input)}</p>
          <p><strong>目标：</strong>${escapeHtml(experiment.goal)}</p>
          <span class="status">${escapeHtml(experiment.status)}</span>
        </article>
      `,
    )
    .join("");
}

/** 渲染错误类型分布条形图 */
function renderErrorBars(data) {
  const maxCount = Math.max(...data.errorDistribution.map((item) => item.count), 1);
  byId("error-bars").innerHTML = data.errorDistribution
    .map((item) => {
      const width = Math.max((item.count / maxCount) * 100, 2);
      return `
        <div class="bar-row">
          <div>
            <div class="bar-label">${escapeHtml(item.label)}</div>
            <small>${escapeHtml(item.type)}</small>
          </div>
          <div class="bar-track" aria-label="${escapeHtml(item.label)} ${item.count}">
            <div class="bar-fill" style="width: ${width}%; background: ${escapeHtml(item.color)}"></div>
          </div>
          <div class="bar-count">${item.count}</div>
        </div>
      `;
    })
    .join("");
}

/** 渲染修复案例切换按钮，并绑定点击切换 */
function renderCaseTabs(data) {
  byId("case-tabs").innerHTML = data.repairCases
    .map(
      (item, index) => `
        <button class="case-tab ${index === state.selectedCaseIndex ? "active" : ""}" data-case-index="${index}">
          #${escapeHtml(item.taskId)} ${escapeHtml(item.errorType)}
        </button>
      `,
    )
    .join("");

  document.querySelectorAll("[data-case-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCaseIndex = Number(button.dataset.caseIndex);
      renderRepairCase(state.data);
      renderCaseTabs(state.data);
      loadSelectedCaseIntoPlayground();
    });
  });
}

/** 渲染当前选中的修复案例详情（错误码 vs 参考修复） */
function renderRepairCase(data) {
  const item = data.repairCases[state.selectedCaseIndex] ?? data.repairCases[0];
  byId("repair-case").innerHTML = `
    <div class="case-meta">
      <span>Task ID: ${escapeHtml(item.taskId)}</span>
      <span>错误类型: ${escapeHtml(item.errorType)}</span>
      <span>修复前: ${escapeHtml(item.before)}</span>
      <span>修复后: ${escapeHtml(item.after)}</span>
    </div>
    <h3>${escapeHtml(item.problem)}</h3>
    <div class="feedback-box">
      <strong>失败反馈：</strong>${escapeHtml(item.feedback)}
    </div>
    <div class="case-grid">
      <section class="code-panel">
        <h4>错误代码</h4>
        <pre><code>${escapeHtml(item.buggyCode)}</code></pre>
      </section>
      <section class="code-panel">
        <h4>参考修复代码</h4>
        <pre><code>${escapeHtml(item.fixedCode)}</code></pre>
      </section>
    </div>
  `;
}

/** 取当前选中的修复案例 */
function getSelectedCase() {
  return state.data?.repairCases?.[state.selectedCaseIndex] ?? state.data?.repairCases?.[0];
}

/** 把当前案例填进交互演示输入框 */
function loadSelectedCaseIntoPlayground() {
  const item = getSelectedCase();
  if (!item) {
    return;
  }
  byId("pg-problem").value = item.problem;
  byId("pg-buggy-code").value = item.buggyCode;
  byId("pg-feedback").value = item.feedback;
  byId("model-output").textContent = "已载入案例，点击“开始修复”查看模型输出。";
  byId("inference-status").textContent = "待推理";
}

/** 演示模式：匹配已知案例返回参考修复，否则返回占位代码 */
function buildDemoRepair(problem, buggyCode, feedback) {
  const matched = state.data.repairCases.find(
    (item) =>
      item.problem.trim() === problem.trim() ||
      item.buggyCode.trim() === buggyCode.trim() ||
      feedback.includes(String(item.taskId)),
  );

  if (matched) {
    return matched.fixedCode;
  }

  return [
    "# 演示模式：返回参考修复结果",
    buggyCode || "def solution(*args, **kwargs):\n    pass",
  ].join("\n");
}

/** 触发修复推理：无 endpoint 走演示，有则 POST 真实接口 */
async function runInference() {
  const endpoint = byId("api-endpoint").value.trim();
  const problem = byId("pg-problem").value.trim();
  const buggyCode = byId("pg-buggy-code").value.trim();
  const feedback = byId("pg-feedback").value.trim();

  byId("run-inference").disabled = true;
  byId("model-output").textContent = "正在推理，请稍候...";

  try {
    if (!endpoint) {
      await new Promise((resolve) => setTimeout(resolve, 450));
      byId("inference-status").textContent = "演示模式";
      byId("model-output").textContent = buildDemoRepair(problem, buggyCode, feedback);
      return;
    }

    byId("inference-status").textContent = "调用接口中";
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        problem,
        buggy_code: buggyCode,
        feedback,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    byId("inference-status").textContent = "真实模型输出";
    byId("model-output").textContent =
      payload.fixed_code ?? payload.output ?? payload.code ?? JSON.stringify(payload, null, 2);
  } catch (error) {
    byId("inference-status").textContent = "调用失败";
    byId("model-output").textContent = `模型接口调用失败：${error.message}\n\n请检查接口地址、跨域设置或服务是否启动。`;
  } finally {
    byId("run-inference").disabled = false;
  }
}

/** 渲染后续步骤列表 */
function renderNextSteps(data) {
  byId("next-list").innerHTML = data.nextSteps
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
}

/** 一次性渲染页面全部区块 */
function render(data) {
  renderOverview(data);
  renderStages(data);
  renderExperiments(data);
  renderErrorBars(data);
  renderCaseTabs(data);
  renderRepairCase(data);
  renderNextSteps(data);
  loadSelectedCaseIntoPlayground();
}

/** 绑定导航切换、载入案例、开始修复等事件 */
function bindEvents() {
  document.querySelectorAll(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.tab));
  });

  document.querySelectorAll(".jump-tab").forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.targetTab));
  });

  byId("load-case").addEventListener("click", loadSelectedCaseIntoPlayground);
  byId("run-inference").addEventListener("click", runInference);
}

// 启动：加载数据 → 渲染 → 绑事件
loadData()
  .then((data) => {
    state.data = data;
    render(data);
    bindEvents();
  })
  .catch((error) => {
    console.error(error);
    document.body.insertAdjacentHTML(
      "afterbegin",
      `<div style="padding:16px;background:#fee2e2;color:#991b1b;">演示数据加载失败：${escapeHtml(error.message)}</div>`,
    );
  });
