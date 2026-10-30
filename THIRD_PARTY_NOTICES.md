# 来源与第三方组件

## DNF原分发

逆向依据为 `Conformant_AIJ/dnf_planner` 原分发。本项目的新C++规划器和Python转换器是行为重建，不是对原源码文本的所有权声明。

| 原件 | SHA-256 |
|---|---|
| `dnf`（仅作原参照，不随仓库发布） | `4f0595c7b6f285495deab03d27e6a66812ef8a6104d72d55dbf2b39ee804082f` |
| `cpa.pddl2pl`（仅作原参照，不随仓库发布） | `87075cfed30f766382627498726423aea875565798f1e416602e9226a85b2163` |
| `preprocessor/original/mult5zsic.pl`（原源码） | `a572b99ceb9aa842edf2de35f733f5a643fe78f630b76afb23dd419da64c3fb8` |
| `preprocessor/original/pddl2pl.pl`（原Blocks生成实例） | `a0e40048ced331a1c39b3430a01b51acb5cdb4e13ab8556e5cafdcdcbd7b9ad4` |

`original_support/dp.pddl` 来自原分发；`converter/original_tables.json` 的词法/语法表提取自原转换器；`tests/converter_cases/` 及 `evidence/converter_oracle.json` 保留原版对照样本及输出。

当前保留材料未确认一份覆盖原分发全部文件的统一许可。因此本整理没有为第三方内容擅自添加MIT等统一许可；公开再分发前应核实原组件的授权范围。新增重建代码的许可可由维护者另行明确，不能覆盖第三方已有权利。

## SWI-Prolog / Ubuntu离线包

`runtime/linux-x64/swi-prolog-core_9.2.9+dfsg-1.1build1_amd64.deb` 来自Ubuntu官方归档。来源URL、依赖、SHA-256见 [package.json](runtime/linux-x64/package.json)，完整组件版权和许可文本见 [SWI-COPYRIGHT.txt](runtime/linux-x64/SWI-COPYRIGHT.txt)。

该包与运行器代码分别标识；解压后的运行时不进入Git仓库或源码ZIP。启动时从包离线重建。
