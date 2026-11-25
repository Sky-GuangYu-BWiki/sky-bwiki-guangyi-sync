# 光遇 BWiki 复刻计时器与光翼查询板块同步仓库 (sky-bwiki-guangyi-sync)

> 🎮 **对应线上词条**：[复刻计时器](https://wiki.biligame.com/sky/复刻计时器)  
> 🧩 **对应核心组件**：[Widget:SynSpirit](https://wiki.biligame.com/sky/Widget:SynSpirit)  
> 🏷️ **归属组织**：[Sky-GuangYu-BWiki](https://github.com/Sky-GuangYu-BWiki)  
> 📦 **上游核心插件**：[koishi-plugin-wydashen-guangyi-query](https://github.com/VincentZyuApps/koishi-plugin-wydashen-guangyi-query) ⭐ *(光翼数据源与核心算法)*  
> 🛡️ **技术支持与 API**：[VincentZyu](https://github.com/VincentZyu233) | `https://guangyi.vincentzyu233.cn` (国内直连) / `https://cf-guangyi.vincentzyu233.cn` (CF加速)

---

## 一、 项目背景

哔哩哔哩游戏WIKI（BWiki）光遇分站上的「复刻计时器」板块用于帮助全网光遇玩家标记和统计已拥有的复刻先祖及永久光之翼。

为避免传统 MediaWiki 后台直接编辑带来的“改错难以追溯”、“缺少本地沙盒测试”、“版本回滚繁琐”等问题，本项目建立标准化 Git 资产仓库，实现：
1. **源码级版本控制**：完整追踪 Wikitext 页面结构与 Widget 原生 JS/CSS/HTML 前端代码；
2. **多重灾备与一键回滚**：支持通过 Git 历史记录秒级还原线上异常，保障攻略站稳定性；
3. **本地开发与沙盒预览**：代码在线下经过充分测试后再同步至线上。

---

## 二、 目录结构说明

```text
sky-bwiki-guangyi-sync/
├── src/                         # 原始源码区（可直接复制粘贴到 BWiki 后台编辑框）
│   ├── data/                    # 光翼与先祖中文字典（从上游 Koishi 插件仓库自动同步）
│   │   ├── wing-dict.json       # 完整版中文映射表
│   │   └── wing-dict.min.json   # 紧凑内嵌版字典 (~13KB)
│   ├── pages/                   # 词条页面源码
│   │   └── 复刻计时器.wikitext    # 复刻计时器主词条的完整 Wikitext
│   └── widgets/                 # 核心挂件源码（包含原生 JS / CSS / HTML）
│       ├── Widget_SynSpirit.html # 光翼与先祖数据自动查询同步组件 (内嵌中文映射)
│       └── Widget_复刻计时器排序.html # 复刻先祖列表动态排序展示组件
├── test/                        # 本地免安装运行沙盒
│   └── preview_sandbox.html     # 支持双线切换、中文抽屉折叠展开的本地测试页
├── snapshots/                   # 线上版本快照与元数据
│   └── rev_metadata.json        # 记录 MediaWiki 线上对应的 revid、时间戳与作者
└── scripts/                     # 自动化同步与运维工具
    ├── sync-wing-dict.py        # 从上游 koishi-plugin-wydashen-guangyi-query 提取并生成中文字典
    └── backup_from_wiki.py      # 一键拉取线上最新状态并生成本地差分
```

---

## 三、 应急回滚操作手册（灾难恢复）

若线上因误改导致页面排版错乱或脚本报错，可选择以下两种方式秒级恢复：

### 方式 1：Git 本地源码直接还原（推荐）
1. 在本仓库查阅最后一次正常工作的 Git Commit：
   ```bash
   git log --oneline
   ```
2. 打开对应版本的 `src/widgets/Widget_SynSpirit.html` 或 `src/pages/复刻计时器.wikitext`；
3. 用管理员账号登录 BWiki，打开对应编辑页：
   - [编辑 Widget:SynSpirit](https://wiki.biligame.com/sky/Widget:SynSpirit?action=edit)
   - [编辑 复刻计时器](https://wiki.biligame.com/sky/复刻计时器?action=edit)
4. 全选覆盖粘贴并点击 **「保存页面」**，线上瞬间满血恢复。

### 方式 2：MediaWiki 线上历史记录回退
1. 打开对应页面的历史记录：
   - `https://wiki.biligame.com/sky/index.php?title=Widget:SynSpirit&action=history`
2. 管理员可直接点击稳定版本右侧的 **「撤销」** 或 **「回滚」** 按钮一键切回。

---

## 四、 自动化同步命令

从线上重新拉取并校验最新内容：
```bash
python scripts/backup_from_wiki.py
```
