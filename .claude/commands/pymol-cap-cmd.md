---
description: 使用命令行为肽链批量添加 ACE/NME 封端。当用户想通过命令行（而非 PyMOL 图形界面）为结构文件加封端时使用此技能。
---

通过 PyMOL 命令行模式为肽链自动添加 ACE（N端）和 NME（C端）封端。

用户可传入参数（`$ARGUMENTS`），若未传入则先询问输入文件、输出文件路径，以及是否只封特定链（默认处理所有蛋白链）。

## 操作流程

1. 从 `$ARGUMENTS` 或询问用户获取：`INPUT`（输入文件）、`OUTPUT`（输出文件）、`CHAINS`（链名列表，可为空）
2. 根据 `CHAINS` 构造链处理代码（见下方模板），运行命令
3. 确认输出文件已生成

## 命令模板

用 `conda run -n d2l python -c` 调用 PyMOL 库（比 `pymol -cq -` heredoc 更可靠，stdout 不会被静默丢弃）：

```bash
conda run -n d2l python -c "
from pymol import editor, cmd
cmd.load('INPUT')
chains = CHAINS_EXPR
for chain in chains:
    if cmd.count_atoms(f'polymer.protein and chain {chain}') == 0:
        continue
    cmd.remove(f'name OXT and chain {chain}')
    editor.attach_amino_acid(f'last name C and chain {chain}', 'nme')
    editor.attach_amino_acid(f'first name N and chain {chain}', 'ace')
cmd.set('pdb_use_ter_records', 0)
cmd.save('OUTPUT')
print('Done')
"
```

INPUT/OUTPUT 若含相对路径，先用 `os.path.abspath()` 转为绝对路径。

其中 `CHAINS_EXPR` 按情况替换：
- 处理所有链：`cmd.get_chains()`
- 指定链（如 A、B）：`['A', 'B']`
