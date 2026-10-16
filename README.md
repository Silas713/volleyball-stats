# 🏐 排球比赛数据统计系统（Volleyball Match Stats）

一个面向排球教练员与运动员的**场边逐球采集 + 实时技术统计**工具。基于 Python + Streamlit 构建，无需数据库，浏览器打开即可使用，支持比赛数据一键导出，为赛后复盘与科研分析提供结构化数据。

> 在线体验：<https://volleyball-stats-bsu.streamlit.app/>

## ✨ 功能特性

- **📝 逐球快速录入**：场边按"环节 + 号码 + 效果"点选即可记录一整球，适配比赛节奏。
  - 环节覆盖：发球、接发球、扣球、拦网、防守、二传（组织）。
  - 支持进攻方式（4号位 / 3号位快球 / 2号位快变 / 后排攻等）、落点区域、发球轮/接发轮等维度。
- **📊 实时技术统计看板**：
  - 得分构成与失误统计；
  - 一攻（接发球进攻）阶段效果分析；
  - 进攻方式分布；
  - 按球员（号码）汇总的个人技术统计；
  - 可按"本队 / 对手"切换查看。
- **📥 数据导入导出**：支持导出 CSV（UTF-8-SIG，Excel 直接打开不乱码）与 Excel；支持清空、删除最后一行等纠错操作。
- **🏟️ 比赛与阵容设置**：自定义比赛日期、对手、双方上场号码。

## 🧮 统计口径

系统统计口径与《排球比赛统计模板》对齐，接发球效果做了规范化归并（如"一般→半到位""无攻过网→破攻"），保证不同记录者、不同场次之间数据可比。详见 `stats.py`。

## 🛠️ 技术栈

- Python 3.10+
- [Streamlit](https://streamlit.io/)（Web 界面）
- pandas（数据处理）
- openpyxl（Excel 读写）

## 🚀 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/Silas713/volleyball-stats.git
cd volleyball-stats

# 2.（建议）创建虚拟环境
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动
streamlit run app.py
```

启动后浏览器会自动打开 <http://localhost:8501>。

## ☁️ 部署到 Streamlit Community Cloud（免费）

1. 将本仓库推送到 GitHub；
2. 登录 <https://share.streamlit.io/>，使用 GitHub 账号授权；
3. 选择本仓库，主文件路径填 `app.py`，点击 Deploy；
4. 后续 `git push` 后线上应用会自动重新部署。

## 📁 项目结构

```
volleyball-stats/
├── app.py              # Streamlit 界面：逐球录入 + 技术统计看板
├── stats.py            # 统计口径与各技术环节的计算函数
├── requirements.txt    # 依赖
└── templates/
    └── 排球比赛统计模板_v3.xlsx   # 配套 Excel 统计模板
```

## 🔭 计划中（Roadmap）

- 数据持久化与多场次管理；
- 单球胜负、对阵双方等字段，支撑回合链（serve–reception chain → rally outcome）建模；
- 可视化图表与球员位置（主攻/副攻/二传/接应/自由人）维度分析。

## 👤 关于作者

北京体育大学运动训练专业本科生，男排队长、国家一级运动员。致力于用数据与科学方法提升排球训练与比赛分析水平。

## 📄 License

MIT
