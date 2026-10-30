# 运行指南

下列命令均在仓库根目录执行；Windows使用PowerShell，Linux使用 `python3` 和 `./dnf`。规划器编译见 [README](../README.md)。

## 完整管线

```powershell
python run_pipeline.py original_support/dp.pddl -o runs/blocks-01
python run_pipeline.py original_support/dp.pddl -o runs/blocks-repaired-01 --mode repaired
python run_pipeline.py domain.pddl problem.pddl -o runs/custom-01 --mode repaired --timeout 120
```

输入文件为UTF-8无BOM、LF换行。一个合并文件或domain/problem两个文件均可。`-o` 必须为空或不存在；失败后重试也应换目录，保留原日志。

| 参数 | 默认/作用 |
|---|---|
| `--mode` | `faithful`；`repaired` 为显式修正版 |
| `--timeout` | 60秒，分别作用于前处理及每个理论的规划阶段，并非总管线时间 |
| `--planner` | 根目录的 `dnf.exe` 或 `dnf`；可指定自己的构建产物 |
| `--runtime` | 解压的SWI根目录，应含 `usr/bin/swipl`，不是swipl文件路径 |
| `--options` | 完整替换原前处理禁用项列表，不是追加 |

默认选项为 `no_duals,no_goal_split`。其余可用项为 `noforward`、`noanalyze`、`no_oneof`。例如禁用前向简化同时保持默认两项：

```text
python run_pipeline.py original_support/dp.pddl -o runs/no-forward-01 --options no_duals,no_goal_split,noforward
```

空列表可写作 `--options=`，意味着全部可选分支启用；原dual和复杂开关组合有缺陷，不建议作为常规默认配置。

## 目标拆分演示

```text
python run_pipeline.py examples/split_goals.pddl -o runs/split-01 --mode repaired --options no_duals
```

演示生成两个理论，分别得到1步计划。`standalone/` 为后续理论补共享声明和初态；程序没有自动组合并验证联合计划。

## 分阶段运行

Windows先创建输出父目录，之后执行：

```powershell
New-Item -ItemType Directory -Path runs -Force
python converter/pddl2pl.py original_support/dp.pddl -o runs/instance.pl
python preprocessor/run_preprocessor.py runs/instance.pl -o runs/pre-01 --mode repaired
.\dnf.exe runs/pre-01/normalized/theory_0.al --timeout 120 --max-nodes 500000
```

Linux相应使用 `mkdir -p runs`、`python3` 和 `./dnf`。独立转换器只接受单个合并输入，且不会创建输出父目录；独立前处理不会生成 `standalone/`。多理论应使用完整管线为后续片段补齐共享声明和初态。

规划器输入是AL，不是PDDL。默认限制为60秒、200000节点，内部另有1000000项term限制。完整管线未暴露 `--max-nodes`，需要时单独调用规划器。

## 验证计划

新建UTF-8无BOM的 `actions.txt`，每行填写一个完整AL动作名，不带编号、banner或统计信息，然后执行：

```powershell
.\dnf.exe runs/blocks-01/standalone/theory_0.al --plan actions.txt
```

动作名示例为 `cpa_put_down(cpa_a)`；必须填写完整计划，单行动作示例并不是Blocks的完整解。也可使用 `-e` 后接动作序列，PowerShell中带括号的动作须加引号。

`is a SOLUTION!` 表示验证通过；`NOT a SOLUTION!`、`cannot be executed` 表示失败。当前执行模式验证失败也可能返回0，必须检查文本。`-t` 使用未加 `cpa_` 前缀的原计划格式，不能与 `--plan` 混用。

## 日志与故障排查

先读 `pipeline.json` 和 `preprocessed/run.json` 的返回码、stdout、stderr、load_errors；语法错误可能在JSON写出前发生，此时查看终端错误。

| 问题 | 处理 |
|---|---|
| 输出目录非空 | 使用新目录，不复用半成品 |
| 找不到 `dnf` / `dnf.exe` | 先编译，或通过 `--planner` 指定实际产物 |
| Windows的WSL无法启动 | 确认发行版已初始化；`wsl --list --verbose` 检查默认项，程序使用默认发行版 |
| `dpkg-deb` 找不到 | 默认发行版须具有该工具；检查Ubuntu环境 |
| 离线包缺失或SHA不一致 | 恢复仓库配套包，不跳过校验 |
| GLIBC / libgmp等加载错误 | 检查宿主是否满足 `runtime/linux-x64/package.json` 的依赖 |
| PDDL词法错误 | 核对LF、UTF-8无BOM及原程序的语法支持范围 |
| 未定义 `check_init_dualsRest` | 原dual缺陷；用默认禁用dual配置，或针对性测试repaired |
| 前处理半截AL | 查看日志；混合oneof/no_oneof仍存在已知缺陷 |
| `Search limit reached` | 适当调整限制后重试，不能据此判定无解 |

可提前运行 `python preprocessor/bootstrap_workspace.py` 解压离线包。完整仓库无需 `--download`。系统已有SWI时，独立前处理支持 `--swipl /usr/bin/swipl`。
