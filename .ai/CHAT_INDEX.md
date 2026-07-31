# AI 对话导航与索引

## 目的

本文档用于管理 Video2Knowledge 的固定 AI 对话线程，并为少量重要对话提供索引。

第一部分回答“应该在哪个线程讨论”，第二部分回答“过去的重要讨论在哪里”。它不保存完整聊天，也不替代正式项目文档和 Git 历史。

## 使用原则

- 开始讨论前先选择最匹配的固定线程。
- 一个主题尽量只在一个主线程中持续，避免产生多个互相冲突的版本。
- 临时排障不要混入长期产品或架构线程。
- 线程过长或目标发生明显变化时，创建后续线程，并记录前后关系。
- 只有对后续开发、审阅或交接确有帮助的对话才加入历史索引。
- 对话结论写入对应正式项目文档或实现提交后，才成为项目事实。

## 固定线程导航

### 一、ChatGPT Web 固定对话

#### V2K - Architecture & Product

- 所在平台：ChatGPT Web。
- 主要职责：讨论产品定位、系统架构、Roadmap、阶段设计，以及需要长期保留的重大决策候选。
- 不要处理：具体代码修改、单个 Bug 排查、临时环境问题或未经评审就直接安排实施。
- 何时交接：方案形成明确目标、范围、排除项和验收标准后，交给 Codex Desktop 的 `V2K - Main Development`；需要外部证据时交给 `V2K - Research`；`V2K - Codex Review` 发现产品、架构或阶段设计问题时，也将问题交回本线程。
- 正式记录：产品结论写入 `PRD.md`，架构结论写入 `ARCHITECTURE.md`，版本与阶段安排写入 `ROADMAP.md`，重大决策写入 `DECISIONS.md`。

#### V2K - Research

- 所在平台：ChatGPT Web。
- 主要职责：调研外部资料、GitHub 项目、竞品，以及 yt-dlp、ffmpeg、Whisper、LLM、Obsidian、MCP 等技术选型。
- 不要处理：直接修改真实工作区，或把外部项目的做法自动视为 Video2Knowledge 的正式决定。
- 何时交接：调研结果需要形成产品或架构选择时，交给 `V2K - Architecture & Product`；需要在真实仓库中验证时，交给 Codex Desktop 的 `V2K - Experiment` 或 `V2K - Main Development`；`V2K - Codex Review` 遇到需要外部资料核实的技术事实时，也将问题交给本线程。
- 正式记录：经过确认的产品影响写入 `PRD.md`，架构选择写入 `ARCHITECTURE.md`，重大选型理由写入 `DECISIONS.md`，实施阶段安排写入 `ROADMAP.md`。

#### V2K - Codex Review

- 所在平台：ChatGPT Web。
- 主要职责：独立审查已经发布到 GitHub review branch 或 Pull Request 的真实代码、commit range、完整 diff、测试或 CI 证据、文档同步和提交整洁性；低风险直接 main 流程中，可以审查用户提供的完整 commit 或 diff 材料。
- 不要处理：不把 Codex 的文字总结当作唯一证据，不声称直接读取尚未发布的本地工作区，不直接修改代码或文档，不创建 commit，不 push review branch 或 main，不 merge，不 tag，也不替用户作最终发布授权。
- 何时交接：发现具体缺陷时交给 Codex Desktop 的 `V2K - Bug Fix`；发现产品、架构或阶段设计问题时交给 `V2K - Architecture & Product`；需要外部证据时交给 `V2K - Research`；需要隔离试验时交给 Codex Desktop 的 `V2K - Experiment`；Review 通过后由用户决定是否授权 merge 或 push main。
- 正式记录：Review 证据和结论优先保留在 GitHub Pull Request、review branch、commit 或对应对话索引中；需要长期保留的产品、架构、状态或待办结论，由接收任务的线程写入职责对应的正式项目文档。

#### V2K - Debug

- 所在平台：ChatGPT Web。
- 主要职责：分析错误、解释日志、梳理可能原因，并制定可验证的排查方案。
- 不要处理：直接修改真实仓库、顺带进行无关重构，或在缺少证据时把推测当成根因。
- 何时交接：需要读取环境或执行诊断命令时，交给 Codex Desktop 的 `V2K - Bug Fix`；需要隔离验证高不确定性方案时，交给 `V2K - Experiment`。
- 正式记录：长期开发规则写入 `AGENTS.md`，架构原因写入 `ARCHITECTURE.md` 或 `DECISIONS.md`，当前缺陷状态写入 `PROJECT_STATUS.md` 或 `TODO.md`；临时排障无需写入正式文档。

#### V2K - Ideas

- 所在平台：ChatGPT Web。
- 主要职责：讨论手机端、浏览器插件、商业化，以及尚未进入 Roadmap 的未来设想。
- 不要处理：把未经评审的想法直接加入当前范围、安排 Codex 实施，或将想法描述成已经确认的产品承诺。
- 何时交接：想法具备明确价值、边界和优先级后，交给 `V2K - Architecture & Product` 评审；需要外部证据时先交给 `V2K - Research`。
- 正式记录：确认进入产品范围后写入 `PRD.md`，进入版本计划后写入 `ROADMAP.md`，重大方向选择写入 `DECISIONS.md`；未确认想法不写入正式项目文档。

### 二、Codex Desktop 固定线程

#### V2K - Main Development

- 所在平台：Codex Desktop。
- 主要职责：执行已经确认的正式阶段，包括读取真实工作区、实施、测试、同步相关文档、创建本地 commit，并依据完整 diff、测试和 Git 状态完成 Codex Self Review。完成阶段时返回 branch、HEAD、`origin/main`、ahead/behind、commit、修改文件、实现与验证结果、diff check、ignored status、已知风险和 review branch 建议。
- 不要处理：未经确认改变产品范围或架构、把多个阶段合并实施、用 Codex 自查替代 Web 独立 review、擅自执行需要授权的操作，或未经用户确认发布 review branch、创建 Pull Request、merge、push main 或 tag。
- 何时交接：本地提交和 Codex 自查完成后，先等待用户授权发布 review branch；发布后交给 ChatGPT Web 的 `V2K - Codex Review`。遇到需要重新设计的范围或架构问题时，交给 `V2K - Architecture & Product`；发现独立缺陷时可转入 `V2K - Bug Fix`。极低风险任务经用户明确确认后，可以向 Web 提供完整 commit 或 diff，采用不发布 review branch 的短路径。
- 正式记录：实现进展写入 `PROJECT_STATUS.md`，阶段边界写入 `PROJECT_SNAPSHOT.md`，待办写入 `TODO.md`，代码职责变化写入 `PROGRAM_MAP.md`，架构或重大决策变化分别写入 `ARCHITECTURE.md` 和 `DECISIONS.md`。

#### V2K - Bug Fix

- 所在平台：Codex Desktop。
- 主要职责：处理范围明确的独立缺陷、测试失败，以及 `V2K - Codex Review` 提出的具体返工项；完成修复、验证、文档同步、独立本地 commit 和 Codex Self Review。
- 不要处理：借修复之机扩大功能范围、进行无关重构、改变正式架构、用 Codex 自查代替 Web 复审，或混入新的开发阶段。
- 何时交接：修复和 Codex 自查完成后，等待用户授权更新同一 review branch，再交回 Web 的 `V2K - Codex Review`；发现根因属于架构或产品设计时，交给 `V2K - Architecture & Product`；需要高风险验证时转入 `V2K - Experiment`。
- 正式记录：缺陷状态和验证结果写入 `PROJECT_STATUS.md`，遗留事项写入 `TODO.md`，架构性根因写入 `ARCHITECTURE.md` 或 `DECISIONS.md`，具体修复历史保留在 Git 提交和 Pull Request。

#### V2K - Experiment

- 所在平台：Codex Desktop。
- 主要职责：开展可能废弃的技术验证、原型试验和 benchmark，为正式方案提供本地证据。
- 不要处理：直接改变正式架构、把实验代码混入主开发提交、把一次 benchmark 当作普遍结论，或未经确认使用网络、认证和媒体下载。
- 何时交接：实验结果需要产品或架构判断时，交给 ChatGPT Web 的 `V2K - Architecture & Product`；需要补充外部资料时交给 `V2K - Research`；方案获批并准备正式实现时交给 `V2K - Main Development`；`V2K - Codex Review` 遇到需要隔离验证的高不确定性问题时，也将问题交给本线程。
- 正式记录：实验过程通常不写入正式项目文档；被采纳的架构结论写入 `ARCHITECTURE.md` 或 `DECISIONS.md`，形成实施阶段后写入 `ROADMAP.md` 和 `TODO.md`，benchmark 数据应保留可复现条件。

### 统一判断规则

- 需要读取或修改真实工作区的任务交给 Codex Desktop。
- 产品、架构、外部研究和未来想法放在 ChatGPT Web。
- `V2K - Main Development` 和 `V2K - Bug Fix` 负责本地验证、提交与 Codex Self Review，但自查不能替代 Web 独立 review。
- GitHub review branch、Pull Request、commit diff、测试证据和文档的独立审查放在 ChatGPT Web 的 `V2K - Codex Review`。
- Web 端不直接声称验证了尚未发布的本地 diff、Git 状态或本地测试环境；其独立审查以 GitHub 上的真实内容和明确提供的验证证据为准。
- 重要阶段优先使用 `review/<stage-name>`；发布 review branch 前必须获得用户明确授权，Pull Request 只在用户明确要求后创建。
- 极低风险任务可以使用完整 commit 或 diff 进行 Web Review 后直接 push main，但仍需用户明确确认。
- Web Review 给出审查结论，最终 merge、push main 或 tag 仍需用户明确授权。
- 审查发现架构问题时返回 `V2K - Architecture & Product`，而不是由 Review 或 Bug Fix 线程自行改变架构。
- 小型修复不强制新开线程；只有主题独立、实验性强，或继续讨论会明显污染主线程时才拆分到 `V2K - Bug Fix` 或 `V2K - Experiment`。
- 对话负责讨论和交接，正式项目文档与 Git 历史负责保存项目事实。

## 对话交接摘要

需要跨线程或交给 Codex 时，使用简短摘要：

```text
来源线程：
讨论主题：
已经确认：
仍未确认：
相关正式文档：
建议下一步：
禁止扩展的范围：
```

## 历史索引收录标准

以下对话可以加入索引：

- 形成了需要交给另一个工具的具体方案。
- 解释了后续审阅仍需参考的重要取舍。
- 导致了正式文档更新或一个独立实现阶段。
- 包含必须跨线程保留的未决问题。
- 后续可能需要从 GitHub Issue 或 Pull Request 引用。

日常命令交互、短暂排障以及已经能从提交和正式文档中完整理解的对话，不必记录。

## 项目事实归属

- 产品范围属于 `PRD.md`。
- 技术结构属于 `ARCHITECTURE.md`。
- 版本顺序属于 `ROADMAP.md`。
- 长期设计理由属于 `DECISIONS.md`。
- 当前进展属于 `PROJECT_STATUS.md` 和 `PROJECT_SNAPSHOT.md`。
- 待办属于 `TODO.md`。
- 代码位置和职责属于 `PROGRAM_MAP.md`。
- 仓库 Agent 规则属于 `AGENTS.md`。
- 个人 AI 协作规则属于 `AI_WORKFLOW.md`。
- 实现历史属于 Git 提交和 Pull Request。

本索引只指向这些结果，不复制其内容。

## 隐私与安全

禁止记录：

- API Key、Token、Cookie、密码或其他认证信息。
- 签名 URL 和敏感查询参数。
- 私人媒体位置和生成的运行产物。
- 包含机密信息的完整提示词或聊天全文。
- 对项目延续没有必要的本机个人信息。

优先使用自己能够访问的稳定对话链接。没有稳定链接时填写“不可用”，并指向对应提交或正式项目文档。

## 历史索引格式

新记录按时间倒序添加到“对话记录”下：

```markdown
### YYYY-MM-DD - 简短主题

- 所属线程：V2K - Architecture & Product | Research | Codex Review | Debug | Ideas | Main Development | Bug Fix | Experiment
- 平台：ChatGPT Web | Codex Desktop | GitHub
- 引用：对话链接、任务标识、Issue/PR 编号或“不可用”
- 仓库基线：分支和/或提交 Hash
- 目的：这次对话为何需要保留
- 结论：简要结果或“没有长期变更”
- 正式记录：对应文档、提交、Issue 或 Pull Request
- 未决问题：尚未解决的事项或“无”
```

## 对话记录

<!-- 在此注释下方按时间倒序添加记录。 -->

### 2026-07-12 - Codex 下一步任务编排流程

- 所属线程：V2K - Architecture & Product
- 平台：ChatGPT Web
- 引用：不可用
- 仓库基线：以当前分支和正式项目文档为准
- 目的：沉淀跨项目可复用的 Codex 返回审查与下一任务生成流程
- 结论：已提炼为独立 Codex Skill `codex-workflow-orchestrator`
- 正式记录：个人 Codex Skills 目录中的 Skill 文件
- 未决问题：无
