# AI 协作工作流

## 目的

本文档用于管理作者在 Video2Knowledge 开发过程中使用 ChatGPT Web、Codex Desktop 和 GitHub 的个人协作方式。

它只描述对话如何分工、上下文如何交接以及结论如何落入项目，不定义产品需求、技术架构、版本计划或开发状态。Git 仓库中的正式项目文档和提交历史始终是项目事实来源；AI 对话只是讨论与辅助上下文。

## 工具分工

### ChatGPT Web

适合需要长期讨论、发散思考或外部调研的工作：

- 澄清产品定位、用户体验和功能边界。
- 探索架构方案并比较取舍。
- 开展外部技术、开源项目和工具调研。
- 审阅阶段计划、文档表达和发布说明。
- 在交给 Codex 实施前形成目标明确的方案。
- 通过 `V2K - Codex Review` 独立审查已经发布到 GitHub review branch 或 Pull Request 的真实代码、commit diff、测试证据和文档同步情况。

ChatGPT Web 不应被视为了解尚未发布的本地工作区。讨论本地代码或文档变更时，应提供相关文件、分支、提交或完整 diff，并明确尚未验证的假设。

Web 端 `V2K - Codex Review` 的独立审查对象是 GitHub 上可读取的 review branch、Pull Request、commit、diff、CI 结果和随交接提供的本地验证证据。它不能声称直接读取或验证了尚未发布的本地 commit、Git 状态或本地测试环境。低风险任务若不使用 review branch，必须向 Web 提供完整、可核验的 commit 或 diff 材料。

### Codex Desktop

适合依赖真实仓库状态的实施、自查、修复和实验工作，并通过独立线程区分职责：

- `V2K - Main Development`：执行已经确认的阶段，修改代码和文档，运行验证，同步正式项目文档，创建本地 commit，并依据真实工作区、完整 diff、测试和 Git 状态完成 Codex 自查。
- Codex Self Review：属于 Main Development 或 Bug Fix 的阶段收尾步骤，用于发现明显实现、范围、安全、文档和提交问题；自查不能替代 ChatGPT Web 的独立 review，也不能自行授权发布、合并或 push main。
- `V2K - Bug Fix`：处理 Web Review 发现的范围明确问题，验证后创建独立修复 commit，完成 Codex 自查，并在用户授权后更新同一 review branch，再交回 Web 复审。
- `V2K - Experiment`：处理可能废弃的技术验证、benchmark 和高不确定性试验，不把实验代码直接混入 Main Development 的正式提交。

Codex 必须遵守仓库中的 `AGENTS.md`。依赖安装、认证访问、真实服务商验证、媒体下载、音频缓存保留和推送等操作，仍需要对应的明确授权。

### GitHub

适合公开协作和长期版本历史：

- 保存用户批准发布的分支和提交。
- 保存供 Web 独立审查的 review branch。
- 在用户明确要求时创建 Pull Request，并通过 Pull Request 组织代码审查。
- 查看 CI 结果和审查意见。
- 保存与具体变更相关的公开讨论。
- 在最终审查通过且用户明确授权后合并或更新 main。

GitHub Issue 和 Pull Request 可以协调工作，但不能替代仓库中的产品、架构、决策、状态和计划文档。GitHub 讨论产生的长期结论，应在合并前或单独阶段写回对应文档。

## 项目事实与对话的边界

对话中的结论只有写入对应正式文档或实现提交后，才成为项目事实：

- `PRD.md`：产品定位、范围和成功标准。
- `ARCHITECTURE.md`：系统结构、技术边界和架构设计。
- `ROADMAP.md`：版本里程碑和阶段顺序。
- `DECISIONS.md`：长期有效的设计决策及理由。
- `PROJECT_STATUS.md`：按时间记录的开发状态。
- `PROJECT_SNAPSHOT.md`：阶段边界的当前快照。
- `TODO.md`：待办事项。
- `PROGRAM_MAP.md`：代码模块和职责地图。
- `AGENTS.md`：公开的仓库 Agent 规则。

本文件和 `CHAT_INDEX.md` 不复制这些内容，只管理个人 AI 协作过程。

## 标准协作流程

通常按以下方式协作：

1. ChatGPT Web 讨论产品、架构、调研或阶段方案。
2. 将确认后的目标、范围、排除项和验收标准交给 `V2K - Main Development`。
3. Main Development 读取真实仓库并实施、验证、同步文档和创建本地 commit。
4. Codex 根据真实工作区、完整 diff、测试和文档完成 Self Review；发现问题时先在当前阶段修正并重新验证。
5. 重要阶段等待用户明确授权后，创建或切换到 `review/<stage-name>`，将待审查提交 push 到 review branch；只有用户明确要求时才创建 Pull Request。
6. ChatGPT Web 的 `V2K - Codex Review` 独立审查 GitHub 上的真实代码、commit range、完整 diff、测试或 CI 证据和文档。
7. Web Review 发现范围明确的缺陷时，交给 `V2K - Bug Fix`；修复、验证、本地提交和 Codex 自查后，在用户授权下更新 review branch，再交回 Web 复审。
8. Web Review 通过后，等待用户对 merge 或 push main 的最终明确授权。
9. 发布到 main 后，把最新基线和结论交回 `V2K - Architecture & Product`，安排下一阶段。
10. GitHub 保存用户批准发布的分支、提交、Pull Request、CI、审查记录和长期版本历史。

完整阶段流程为：

```text
Plan
-> Review
-> Implement
-> Validate
-> Update Documentation
-> Local Commit
-> Codex Self Review
-> Publish Review Branch / PR after user approval
-> ChatGPT Web Independent Review
-> Fix if needed
-> Final Approval
-> Merge / Push main
```

小型任务可以省略 Web 端预先规划，但不能省略实现后的必要本地验证和 Codex 自查。Codex 自查不能替代 Web 独立 review。未获用户明确确认时，不得发布 review branch、创建 Pull Request、merge、push main 或 tag。

## GitHub review branch 与 Pull Request

重要阶段默认不把未经 Web Review 的提交直接 push 到 `origin/main`。推荐路径是：

```text
local main / development state
-> create review branch
-> push review branch
-> optional Pull Request
-> Web V2K - Codex Review
-> fixes
-> final approval
-> merge into main
```

- review branch 使用 `review/<stage-name>`，例如 `review/v0.5-local-asr` 或 `review/v0.5-provider-hardening`。
- 发布 review branch 前必须等待用户明确授权。
- 创建或切换 review branch 时，不得覆盖、重写或变基本地 main 历史。
- push 后应返回 branch name、remote branch、相对 `origin/main` 的 commit range 和 GitHub review target。
- Pull Request 是可选项，只在用户明确要求后创建。
- 未经用户明确要求，不直接 push 未审查代码到 `origin/main`，不 merge，不 tag。

## 低风险直接 main 例外

极小文档修正、无代码行为变化的修改、明确的小型测试补充，或能够完整提供 diff 的单提交修复，可以在用户明确确认后使用较短路径：

```text
Local Commit
-> Codex Self Review
-> Web Review using supplied diff / commit
-> user final approval
-> Push main
```

是否采用例外取决于实际风险和证据完整性。中大型功能，以及涉及网络 Provider、ASR、LLM、权限、安全边界、文件生命周期或跨模块行为的变更，优先使用 review branch 或 Pull Request。

## 阶段完成报告

每个正式阶段完成本地提交后，必须返回：

1. branch。
2. HEAD。
3. `origin/main`。
4. ahead/behind 状态。
5. commit hash。
6. commit message。
7. 修改文件。
8. 实现摘要。
9. 验证命令和真实结果。
10. `git diff --check` 结果。
11. `git status --short --ignored`。
12. 已知风险。
13. 是否建议进入 review branch。

## Web Review 后的交接

- 发现具体缺陷：交给 Codex Desktop 的 `V2K - Bug Fix`。
- 发现产品、架构或阶段设计问题：停止修改，交给 Web 的 `V2K - Architecture & Product`。
- 需要隔离试验或 benchmark：交给 Codex Desktop 的 `V2K - Experiment`。
- 需要外部证据：交给 Web 的 `V2K - Research`。
- Review 通过：等待用户明确授权 merge 或 push main。

## 可复用任务编排 Skill

当用户提供 Codex 的计划、实现结果、测试结果或审查结论，并要求判断下一步时，可调用通用的 `codex-workflow-orchestrator` Skill。

该 Skill 用于判断任务性质、核对事实来源、选择合适的线程或工具，并生成可直接执行的下一步任务提示词。完整规则、通用模板与参考案例保存在独立 Skill 中，本文件不复制其内容。

## 交接模板

从 ChatGPT Web 向 Codex Desktop 交接任务时，尽量包含：

```text
目标：一个具体结果
范围：允许修改的文件或子系统
排除项：本阶段不能顺带处理的内容
仓库基线：分支、提交或当前版本
约束：安全、兼容性和审批边界
验收标准：怎样判断已经完成
验证方式：需要执行的命令或检查
未决问题：仍需用户选择的事项
对话引用：CHAT_INDEX 中的线程或记录
```

Codex 必须以当前仓库为准核对交接内容。对话内容与已提交文档冲突时，不应静默改变项目范围，而应先向用户说明冲突并获得方向。

## 固定线程使用原则

- 产品、架构和版本规划进入 `V2K - Architecture & Product`。
- 外部资料和技术选型进入 `V2K - Research`。
- 真实工作区中的实施、验证、本地提交和 Codex 自查进入 Codex Desktop 的 `V2K - Main Development` 或 `V2K - Bug Fix`。
- GitHub review branch、Pull Request、commit diff、测试证据和文档的独立审查进入 ChatGPT Web 的 `V2K - Codex Review`。
- 环境、测试失败和临时排障进入 `V2K - Debug`。
- 尚未进入路线图的未来想法进入 `V2K - Ideas`。
- 一个问题尽量只保留一个主线程，避免多处同时形成不同结论。
- 线程过长或主题明显变化时，创建后续线程，并在索引中互相引用。

## 审批与安全边界

AI 协作流程不会扩大任何工具的授权范围：

- 未经明确确认，不安装依赖。
- 每次真实服务商在线验证都需要单独确认。
- 未经明确确认，不使用 Cookie、登录会话或认证访问。
- 未经当前阶段确认，不下载视频、音频、字幕、缩略图或其他媒体。
- 保留音频缓存需要单独确认。
- 本地工作完成不代表可以发布 review branch、创建 Pull Request、merge、push main 或 tag。
- review branch 的 push、Pull Request 创建、merge、push main 和 tag 分别需要符合当前阶段的明确授权。
- 不在聊天索引或提交中保存 API Key、Token、Cookie、签名 URL、认证信息或私人对话全文。

## 信息冲突处理

出现冲突时按以下顺序判断：

1. 用户当前明确指令。
2. `AGENTS.md` 中的仓库规则和安全边界。
3. 各正式项目文档按照自身职责记录的当前事实。
4. 当前工作区和 Git 历史。
5. GitHub Issue 或 Pull Request 讨论。
6. ChatGPT Web 或 Codex 的历史对话。

旧对话不能覆盖更新的仓库事实。涉及产品范围或架构变化时，应获得用户确认并更新对应正式文档。

## 完成检查

一次协作任务结束前确认：

- 只解决一个明确问题，没有扩展到排除项。
- 当前差异不包含无关文件、敏感信息或运行产物。
- 验证结果真实准确，没有臆造。
- 需要明确授权的操作已经获得授权。
- 长期有效的结论已经进入对应正式项目文档。
- `CHAT_INDEX.md` 只保存导航和必要索引，没有复制项目知识库。
- 验证后已经创建本地提交。
- 已完成 Codex Self Review，并明确记录已知风险和是否建议进入 review branch。
- 未经用户确认没有发布 review branch、创建 Pull Request、merge、push main 或 tag。
