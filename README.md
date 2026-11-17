
# 重要：写作提醒

## **不要暴露个人隐私！！！**

---

# 神人百科 · 从零开始维护

这份说明写给**完全没写过网页、也没用过 Markdown** 的人。不需要懂代码，照着步骤做就能修改网站、添加页面并提交更新。

---

## 1. 先认识这个网站

- 首页：大字「神人百科」和页面索引。
- 分区页：目前只有一个分区，叫「神人们」。
- 内容页：目前只有一个示例页，叫「示例页面」。
- 所有正文都用 **Markdown** 写，保存在 `content/` 文件夹里。
- `dist/` 是自动生成的网页，**不要直接修改**，每次生成都会被覆盖。

网站的设计很简单：白底、黑字、直线和方框。没有圆角、阴影、动画和复杂装饰。

---

## 2. 文件都放在哪里

```text
神人百科/
├─ content/                  ← 你主要改这里
│  └─ shenren/               ← 一个分区（文件夹名就是网址的一部分）
│     ├─ index.md            ← 分区首页：神人们
│     ├─ example.md          ← 内容页：示例页面
│     └─ images/             ← 这个分区的图片放在这里
├─ templates/
│  ├─ page.md                ← 新建内容页时复制这个
│  └─ section.md             ← 新建分区时复制这个
├─ assets/
│  └─ style.css              ← 网站样式，不懂代码就不要改
├─ build.py                  ← 把 Markdown 生成网页的程序
├─ build.bat                 ← Windows 双击这个生成网页
├─ README.md                 ← 你正在看的说明
└─ dist/                     ← 自动生成的网页，不要手动改
```

记住一句话：**改 `content/` 里的 `.md` 文件，然后运行 `build.bat`。**

---

## 3. 三分钟改一篇页面

以修改「示例页面」为例。

1. 打开 `content/shenren/example.md`。
   - 右键文件 →「打开方式」→「记事本」即可。
   - 推荐安装 [VS Code](https://code.visualstudio.com/)，它更清楚地显示 Markdown。
2. 修改文件最上方 `---` 之间的信息：

   ```markdown
   ---
   title: 示例页面
   order: 1
   ---
   ```

   - `title`：页面标题，会显示成网页上的大字。
   - `order`：排序数字，越小越靠前。建议新页面用 `10`、`20`、`30`。
3. 修改 `---` 下面的正文。正文用 Markdown 写，下一节有速查表。
4. 按 `Ctrl + S` 保存。
5. 双击根目录的 `build.bat`。它会生成网页并自动打开 `dist/index.html`。
6. 在浏览器里检查。如果没有变化，按 `Ctrl + F5` 强制刷新。

> **不要**在正文第一行写 `# 标题`。网页的大标题已经由 `title` 自动生成。正文从 `##` 开始。

---

## 4. Markdown 速查

Markdown 就是“用几个符号表示格式”的纯文本。下面这些已经够写完整条目。

### 4.1 段落

空一行，就是新段落。不要在每句话后面按回车，让一段话写在同一行里，编辑器会自动换行。

```markdown
这是第一段。

这是第二段。
```

### 4.2 小标题

```markdown
## 二级标题

### 三级标题
```

网页大标题由 `title` 生成，所以正文从小标题 `##` 开始。`##` 和文字之间要有一个空格。

### 4.3 加粗、斜体、删除线

```markdown
**加粗**
*斜体*
~~删除线~~
```

效果：**加粗**、*斜体*、~~删除线~~。

### 4.4 列表

无序列表：

```markdown
- 第一条
- 第二条
- 第三条
```

有序列表：

```markdown
1. 第一步
2. 第二步
3. 第三步
```

`-` 或数字后面要有一个空格。

### 4.5 引用和原话

在段落前加 `>`：

```markdown
> “车可以坏，人不能丢。”
```

会显示成一个方框。适合放人物原话、编者按或提醒。

### 4.6 链接

```markdown
[示例页面](example.md)
[外部网站](https://example.com)
```

- 链接到站内页面时，写 `.md` 文件名即可，生成时会自动变成 `.html`。
- 链接到外部网站时，写完整的 `https://` 地址。

### 4.7 图片

1. 把图片放进 `content/shenren/images/`，例如 `content/shenren/images/lao-wang.jpg`。
2. 在 Markdown 里写：

   ```markdown
   ![老王在修车](images/lao-wang.jpg)
   ```

- 方括号里是图片说明（给看不见图片的人读的），圆括号里是路径。
- 路径相对于当前 `.md` 文件所在文件夹。
- 图片文件名建议用小写英文、数字和连字符。
- GitHub 区分大小写，`Photo.JPG` 和 `photo.jpg` 不是同一个文件。
- 上传前把图片压小一点，尽量控制在 1 MB 以内，300 KB 左右更好。

### 4.8 表格

```markdown
| 项目 | 内容 |
| --- | --- |
| 称呼 | 老王 |
| 地点 | 城南 |
```

第二行的 `| --- | --- |` 不能少。表格适合放基本信息。

### 4.9 分隔线

```markdown
---
```

单独一行写三个减号，会显示一条横线。**注意：** 如果文件第一行就是 `---`，它会被当成页面信息的开始。正文里的分隔线要和上文空一行，并且不要放在文件最开头。

### 4.10 代码

短代码用反引号包起来：

```markdown
使用 `build.bat` 生成网页。
```

多行代码用三个反引号：

````markdown
```text
第一行
第二行
```
````

写普通条目基本用不到代码块。

---

## 5. 新建一个内容页

1. 复制 `templates/page.md`。
2. 粘贴到 `content/shenren/` 里。
3. 把文件名改成小写英文或拼音，用连字符分隔，例如：

   ```text
   wang-laowang.md
   lao-li.md
   xiao-zhou.md
   ```

   文件名会成为网址的一部分：`dist/shenren/wang-laowang.html`。

4. 用记事本打开，修改开头的 `title` 和 `order`。
5. 写正文。
6. 运行 `build.bat`。

新页面会**自动出现**在「神人们」页面的“本区页面”列表里，不需要手动改索引。

如果要删除页面，删掉对应的 `.md` 文件，再运行一次 `build.bat`。如果其他页面里有指向它的链接，记得一并删掉。

### 文件名规则

只能使用：

- 小写英文字母 `a-z`
- 数字 `0-9`
- 连字符 `-`

不要使用中文、空格、下划线或大写字母。例如：

- 可以：`wang-laowang.md`
- 不可以：`王老王.md`、`Wang Lao Wang.md`、`wang_laowang.md`

---

## 6. 新建一个分区

分区就是网站首页索引里的一项。除非内容真的很多，否则不需要急着开新分区。

1. 在 `content/` 里新建文件夹，名字用小写英文或拼音，例如 `content/lao-ren/`。
2. 复制 `templates/section.md` 到该文件夹，并改名为 `index.md`。
3. 修改 `title`、`order`。
4. 按第 5 节的方法，在这个文件夹里添加内容页。
5. 运行 `build.bat`。

首页索引和分区页都会自动更新。

目录结构示例：

```text
content/
└─ lao-ren/
   ├─ index.md          ← 分区首页（必须有）
   ├─ zhang-yi.md       ← 内容页
   ├─ li-er.md          ← 内容页
   └─ images/
      └─ zhang-yi.jpg
```

---

## 7. 在电脑上生成和预览

### Windows

双击根目录的 `build.bat`。

它会：

1. 调用 Python 运行 `build.py`。
2. 重新生成 `dist/`。
3. 自动用默认浏览器打开 `dist/index.html`。

### macOS / Linux

在项目文件夹里打开终端，运行：

```bash
python3 build.py
```

然后打开 `dist/index.html`。

### 生成失败怎么办

`build.bat` 窗口会显示中文错误提示，例如：

- `缺少 index.md`：分区文件夹里必须有 `index.md`。
- `order 必须是数字`：把 `order: 十` 改成 `order: 10`。
- `页面文件名不合格`：把文件名改成小写拼音或英文。
- `请在开头加上 title`：检查文件开头的 `---` 信息区。

修好后重新运行 `build.bat`。如果看不懂，把窗口里的文字截图发给维护者。

---

## 8. 提交更新

### 方式 A：GitHub 网页版（推荐给零基础）

前提：维护者已经把这个项目放到 GitHub，并给你编辑权限；同时已经开启自动发布。

1. 在浏览器打开项目主页。
2. 点进要改的文件，例如 `content/shenren/example.md`。
3. 点右上角的铅笔图标。
4. 直接修改文字。
5. 点页面底部的 **Commit changes**。
6. 在说明框里写一句人话，例如：

   ```text
   更新：补充老王的原话
   ```

7. 再点 **Commit changes** 确认。

提交后，GitHub Actions 会自动重新生成并发布网页。通常等 1–2 分钟，刷新网站即可看到。

**新建页面**：项目主页 → **Add file** → **Create new file** → 文件名写 `content/shenren/xxx.md` → 粘贴模板内容 → 提交。

**上传图片**：进入 `content/shenren/images/` → **Add file** → **Upload files** → 选择图片 → 提交。

### 方式 B：在自己电脑上提交

如果你已经安装 Git，并且项目文件夹已经连接远程仓库：

```bash
git pull
# 修改 content/ 里的 Markdown 文件
# Windows 双击 build.bat 检查效果
git add content assets README.md build.py
git commit -m "更新：补充老王的原话"
git push
```

`dist/` 是自动生成的结果，不需要提交，已在 `.gitignore` 里忽略。

### 提交说明怎么写

推荐格式：

```text
更新：补充老王的原话
新增：城南修车铺条目
修正：改正示例页面的地点
样式：调整分区列表间距
```

一句说清“改了什么”即可。

---

## 9. 管理员一次性设置

如果要把网站发布到 GitHub Pages：

1. 在 GitHub 新建仓库，把整个项目推送到 `main` 分支。
2. 打开仓库 **Settings** → **Pages**。
3. 在 **Build and deployment** 下，把 **Source** 设为 **GitHub Actions**。
4. 推送任意一次提交，等待 `Deploy website` 工作流完成。
5. 在 **Actions** 或 **Pages** 页面查看网站地址。

项目已包含 `.github/workflows/deploy.yml`。它会在每次推送到 `main` 或 `master` 时：

1. 安装 Python。
2. 运行 `python build.py`。
3. 把 `dist/` 发布到 GitHub Pages。

如果仓库默认分支不是 `main` 或 `master`，需要改一下工作流里的分支名。


---

## 10. 常见问题

**改了文件，网页没变化？**

先运行 `build.bat`，再在浏览器按 `Ctrl + F5`。如果是在 GitHub 网页改的，等 1–2 分钟并查看 Actions 是否成功。

**新页面没有出现在列表里？**

检查：

- 文件是否在 `content/shenren/` 这类分区文件夹里。
- 开头是否有 `title`。
- `order` 是否是数字。
- 文件名是否全小写、用连字符。
- 是否重新运行了 `build.bat`。

**图片显示不出来？**

检查图片路径和文件名大小写。路径是相对于 `.md` 文件所在的文件夹。例如 `content/shenren/example.md` 里引用 `images/lao-wang.jpg`，实际文件应在 `content/shenren/images/lao-wang.jpg`。

**可以用 Word 写吗？**

不建议。Word 会带入隐藏格式，Markdown 需要纯文本。用记事本、VS Code、Typora、Obsidian 都可以。

**可以直接改 `dist/` 里的网页吗？**

不要。`dist/` 每次生成都会被清空重建。所有修改都要写在 `content/` 的 Markdown 里。

**双击 `build.bat` 后窗口闪一下就消失？**

如果网页正常打开，这是正常现象。如果网页没有打开，可能是没有安装 Python。安装 [Python](https://www.python.org/downloads/) 时勾选“Add Python to PATH”，然后重试；或者直接用 GitHub 网页方式提交。

**写坏了怎么办？**

如果已经用 Git，执行 `git checkout -- 文件名` 可以恢复上一次提交的版本。没有 Git 就找维护者从历史记录恢复。重要修改前建议先复制一份备份。

---

## 12. 一句话流程

> 打开 `.md` → 改 `title` 和正文 → 保存 → 双击 `build.bat` → 检查页面 → 提交。

网站结构保持两层：**首页 → 分区 → 页面**。这样索引最干净，读者也最容易找到内容。

??
