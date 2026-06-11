---
name: pymol-cap-chain
description: 在已打开的 PyMOL 会话中，通过 XML-RPC 接口给指定链的两端加上 ACE（乙酰基）和 NME（N-甲基酰胺）封端基团。当用户想给某条肽/蛋白链做封端、钝化末端、为 MD 准备结构时使用，触发语包括“给 chain B 封端”“加 ACE/NME 帽子”“封端”“acetylate N 端、amidate C 端”“cap the peptide”等。即使用户只说“封端”而没点名帽子类型也应触发，因为 ACE/NME 就是标准的中性封端。
---

# PyMOL：给指定链加 ACE / NME 封端

给所选链的 **N 端**加 **ACE**（乙酰基，`CH3-CO-`），给 **C 端**加 **NME**（N-甲基酰胺，`-NH-CH3`），
操作对象是已经加载进 PyMOL、并由 `pymol:run_pymol_command` XML-RPC 工具控制的结构。

这是 MD 准备里的标准一步：用中性帽子替换带电的自由末端，让肽链表现得像内部片段而不是两性离子。

## 开始之前

1. **先确定是哪条链。** 链 ID 是必需参数。如果用户没说，就询问，或从 PyMOL 当前显示里确认。下文所有
   `${CHAIN}` 都替换成该链 ID（例如 `B`）。
2. **PyMOL 必须已打开**且启用了 XML-RPC 服务（没开就用 `pymol:open_pymol`）。每次 `pymol:run_pymol_command`
   只发一条命令。
3. **读不回命令输出。** 该工具只返回 `Executed: ...`，拿不到 `iterate`/`print`/`count_atoms` 的结果。
   所以本流程被设计成**不需要回读**：用选择代数（`first`/`last`）定位末端，而非硬编码残基编号；
   结尾用高亮让**用户**目视确认。不要自己宣称成功——`Executed` 只代表语句执行了，不代表化学接对了，
   一定让用户看一眼帽子。

## 每一步为什么这么设计

- **ACE 接 N 端的 N**，因为乙酰基通过它的羰基碳与该氮成键；**NME 接 C 端的羰基 C**，因为甲基酰胺通过它
  自己的氮与该碳成键。选对原子，肽键几何就顺理成章。
- **必须先腾出空价。** C 端羧基多出来的氧（`OXT`）正好占着 NME 氮要去的位置——不删它，羰基碳会过配位，
  所以删掉 `OXT`（保留 `O`）。带电的 N 端（`NH3+`，即 `H1/H2/H3`）让氮没有空价给 ACE，所以先剥掉首残基的
  氢。后续质子化交给 tleap/LEaP 重新加。
- **`polymer` 过滤**避免 `first`/`last` 抓到配体、离子或水。

## 操作流程

按顺序执行下列命令，把 `${CHAIN}` 替换成链 ID。

```
/from pymol import editor
```

N 端 → ACE：
```
remove hydro and byres (first (chain ${CHAIN} and polymer and name N))
edit first (chain ${CHAIN} and polymer and name N)
editor.attach_amino_acid("pk1", "ace")
```

C 端 → NME：
```
remove chain ${CHAIN} and name OXT+OT2+OT1+OXT1+OXT2
edit last (chain ${CHAIN} and polymer and name C)
editor.attach_amino_acid("pk1", "nme")
```

清理选取状态：
```
unpick
deselect
```

高亮帽子并框住整条链，便于用户确认（新建的 ACE/NME 残基会继承所连接残基的链 ID）：
```
hide everything
show cartoon, polymer
set cartoon_side_chain_helper, 1
show sticks, chain ${CHAIN} and resn ACE+NME
color yellow, chain ${CHAIN} and resn ACE+NME
util.cnc chain ${CHAIN} and resn ACE+NME
orient chain ${CHAIN}
zoom chain ${CHAIN}, 3
```

然后告诉用户：两端的黄色 sticks 就是封端基团，请确认连接和朝向是否合理。

## 封端之后

- **几何是理想化的，没有优化。** `attach_amino_acid` 用默认 φ/ψ 和标准内坐标放置帽子，可能朝向略别扭，
  或与邻近原子轻微冲突。生产级 MD 应在 **tleap/LEaP**（或 pdb4amber / CHARMM-GUI）里重建拓扑——ACE 和 NME
  会被识别为标准封端残基，tleap 会重新加氢并给出正确质子化态，同时保留重原子坐标。把这一步当作“摆好帽子的
  重原子”，而不是“成品 MD 结构”。
- **用户需要时再导出。** 存 PDB 前先关掉 TER 记录，存完再还原（默认值为 1）：

  ```
  set pdb_use_ter_records, 0
  save /path/to/structure_capped.pdb, chain ${CHAIN}
  set pdb_use_ter_records, 1
  ```

  `save ..., chain ${CHAIN}` 只存该链，去掉 `, chain ${CHAIN}` 则存全部。先确认路径和格式。

  **为什么关 TER：** PyMOL 默认会写 TER 记录，而它常被插在 ACE/NME 帽子与相邻残基之间（或链断点处），
  导致 tleap 把帽子当成独立分子、不与主链成键。设 `pdb_use_ter_records, 0` 抑制 TER，让链保持连续；
  存完务必设回 1，避免影响同一会话里后续正常结构的导出。

## 注意事项与边界情况

- **`first`/`last` 假设链内原子按 N→C 排序**，对正常建模的结构成立。若结构排序异常，可能挑错末端——目视
  检查能发现。
- **只封最外侧的两个末端。** 若链内有断裂（缺口、多个片段），本流程不会封断点，只封最前的 N 和最后的 C。
- **多条链：** 换一个 `${CHAIN}` 把整套流程重跑一遍。
- **结尾高亮为空**通常说明帽子没继承到预期链 ID；改用 `resn ACE+NME` 单独选取（可加
  `resn ACE+NME within 5 of chain ${CHAIN}`）。
