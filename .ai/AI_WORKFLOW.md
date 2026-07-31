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

## 固定仓库信息

Video2Knowledge 的 GitHub 审查与发布目标固定为：

```text
Repository:
Eternal-HAC/Video2Knowledge

Repository URL:
https://github.com/Eternal-HAC/Video2Knowledge

Base branch:
main
```

生成阶段完成报告、review branch 发布结果或 Web Review Handoff 时，Codex 应直接使用这些信息，无需用户重复提供。执行任何联网或 Git 写操作前，仍须核对本地 remote、当前分支、HEAD、待发布范围和用户授权；固定信息不能替代执行前安全核验。

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

review branch 与 Pull Request 是两层流程。默认使用 `local commit -> review branch -> Web Review`，不强制每次创建 Pull Request。以下情况优先建议使用 Pull Request：

- 中大型功能。
- 多提交阶段。
- 安全边界修改。
- 网络 Provider。
- ASR 或 LLM integration。
- 跨模块改动。
- 需要长期保留 review 讨论。

小型单提交可以只使用 review branch。创建 Pull Request 仍需用户单独明确授权。

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

## 阶段完成后的固定输出

每个正式阶段完成本地 commit 和 Codex Self Review 后，必须使用以下格式返回。所有占位内容必须来自真实仓库和实际验证；未执行的验证要明确写“未执行”及原因，不能省略或推测结果。

```markdown
# V2K Development Completion

## Repository

Repository:
Eternal-HAC/Video2Knowledge

Repository URL:
https://github.com/Eternal-HAC/Video2Knowledge

## Git Baseline

Branch:
<current branch>

HEAD:
<commit hash>

Base:
origin/main <hash>

Status:
<ahead / behind>

## Stage

Stage:
<stage name>

Objective:
<one sentence>

## Commits

<按时间从旧到新列出本阶段的 hash 和 message>

## Changed Files

<列出实际修改文件>

## Implementation Summary

<只总结实际完成内容，不把未实现能力描述为已实现>

## Explicitly Not Changed

<按实际阶段列出明确未处理的内容，例如 CLI、pipeline、real-fallback、network、media download、LLM、cache>

## Validation

<列出真实执行的 unittest、targeted tests、Mock CLI、git diff --check 和其他已获批准的验证及结果>

## Git Status

git status -sb
<真实输出>

git status --short --ignored
<真实输出>

## Known Risks

<只记录有证据的已知风险；没有时写 None>

## Approval State

- local commit complete
- review branch NOT published unless separately approved
- main NOT pushed
- PR NOT created
- tag NOT created
```

如果某项已经在本阶段获得单独授权并实际执行，应按事实更新 `Approval State`，不能继续保留与真实状态冲突的默认文字。

## Review branch 发布后的固定 Web Handoff

用户明确授权创建并 push review branch 后，Codex 必须返回以下标准 handoff。已知精确 hash 时必须填写 base commit 和 head commit；没有创建 Pull Request 时，PR URL 写“未创建”。

```markdown
# V2K Web Review Handoff

## Repository

Repository:
Eternal-HAC/Video2Knowledge

Repository URL:
https://github.com/Eternal-HAC/Video2Knowledge

## Review Target

Base:
main

Review branch:
<review branch>

Review range:
main...<review branch>

Base commit:
<hash>

Head commit:
<hash>

## GitHub Review Instruction

请通过已连接的 GitHub 仓库执行真实代码审查。

Repository:
Eternal-HAC/Video2Knowledge

Repository URL:
https://github.com/Eternal-HAC/Video2Knowledge

Base:
main

Review branch:
<review branch>

Review range:
main...<review branch>

请直接检查 GitHub 上的真实：

- commits
- diff
- source code
- tests
- documentation

不要只依据 Codex 的摘要。

重点审查：

1. 阶段目标是否真正实现。
2. 是否超出范围。
3. 架构一致性。
4. 安全边界。
5. 错误处理。
6. 测试证据。
7. 文档同步。
8. 是否适合 merge 到 main。

最终给出：

A. 可以 merge
B. 需要 Bug Fix
C. 需要 Architecture & Product 重新决策
D. 证据不足

## Published State

- remote review branch: <remote branch>
- branch HEAD: <hash>
- relative base commit: <hash>
- PR URL: <URL 或未创建>
- main 是否保持不变: <真实结果>
```

handoff 只能在 review branch 实际发布成功后使用。若 push、认证或网络失败，应返回真实失败状态，不能生成暗示 GitHub 已可审查的 handoff。

## Web Review 后的交接

- A. 可以 merge：等待用户明确授权 merge 或 push main。
- B. 需要 Bug Fix：交给 Codex Desktop 的 `V2K - Bug Fix`；修复、本地验证、commit 和 Codex Self Review 完成后，经用户授权更新同一 review branch，再交回 Web Review。
- C. 需要 Architecture & Product 重新决策：停止修改，交给 Web 的 `V2K - Architecture & Product`。
- D. 证据不足：先明确缺失证据；需要本地仓库证据时交给对应 Codex Desktop 线程补充，需要外部资料时交给 Web 的 `V2K - Research`，需要隔离验证时交给 Codex Desktop 的 `V2K - Experiment`。

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
