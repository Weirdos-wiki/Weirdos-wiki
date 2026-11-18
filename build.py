#!/usr/bin/env python3
"""把 content/ 里的 Markdown 生成 dist/ 里的静态网页。

只依赖 Python 标准库。修改页面内容后运行 build.bat（或 python build.py）即可。
页面骨架来自 templates/layout.html，改外观时改那个文件即可。
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "content"
ASSETS_DIR = ROOT / "assets"
TEMPLATE_DIR = ROOT / "templates"
DIST_DIR = ROOT / "dist"
LAYOUT_TEMPLATE = TEMPLATE_DIR / "layout.html"

SITE_NAME = "神人百科"
REPO_URL = "https://github.com/Weirdos-wiki/Weirdos-wiki"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")


class BuildError(Exception):
    """内容格式有问题时给出可以直接看懂的提示。"""


@dataclass
class Page:
    title: str
    order: int
    slug: str
    source: Path
    body: str
    section: "Section | None" = None


@dataclass
class Section:
    title: str
    order: int
    slug: str
    source: Path
    body: str
    pages: list[Page] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 读取内容
# ---------------------------------------------------------------------------


def parse_front_matter(raw: str, source: Path) -> tuple[dict[str, str], str]:
    text = raw.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    if not lines or lines[0].strip() != "---":
        return {}, text.strip() + "\n"

    meta: dict[str, str] = {}
    end = None
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            end = index
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            meta[key] = value

    if end is None:
        raise BuildError(f"{display_path(source)}：开头有 ---，但没有找到结尾的 ---。")

    body = "\n".join(lines[end + 1 :]).strip()
    return meta, body + "\n"


def parse_order(meta: dict[str, str], source: Path) -> int:
    raw = meta.get("order", "999").strip()
    try:
        return int(raw)
    except ValueError as exc:
        raise BuildError(f"{display_path(source)}：order 必须是数字，例如 order: 1。") from exc


def require_title(meta: dict[str, str], source: Path) -> str:
    title = meta.get("title", "").strip()
    if not title:
        raise BuildError(f"{display_path(source)}：请在开头加上 title，例如 title: 示例页面。")
    return title


def load_site() -> list[Section]:
    if not CONTENT_DIR.is_dir():
        raise BuildError("找不到 content/ 文件夹。请确认没有移动它。")

    sections: list[Section] = []
    for directory in sorted(CONTENT_DIR.iterdir(), key=lambda path: path.name):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        if not SLUG_RE.fullmatch(directory.name):
            raise BuildError(
                f"分区文件夹名「{directory.name}」不合格。请使用小写英文/拼音和连字符，例如 shenren。"
            )

        index_file = directory / "index.md"
        if not index_file.is_file():
            raise BuildError(
                f"分区 {directory.name} 缺少 index.md。每个分区文件夹里都必须有一个 index.md 作为分区首页。"
            )

        meta, body = parse_front_matter(index_file.read_text(encoding="utf-8"), index_file)
        section = Section(
            title=require_title(meta, index_file),
            order=parse_order(meta, index_file),
            slug=directory.name,
            source=directory,
            body=body,
        )

        for page_file in sorted(directory.glob("*.md")):
            if page_file.name.lower() == "index.md":
                continue
            slug = page_file.stem
            if not SLUG_RE.fullmatch(slug):
                raise BuildError(
                    f"页面文件名「{page_file.name}」不合格。请使用小写英文/拼音和连字符，"
                    f"例如 wang-laowang.md。"
                )
            page_meta, page_body = parse_front_matter(
                page_file.read_text(encoding="utf-8"), page_file
            )
            page = Page(
                title=require_title(page_meta, page_file),
                order=parse_order(page_meta, page_file),
                slug=slug,
                source=page_file,
                body=page_body,
                section=section,
            )
            section.pages.append(page)

        section.pages.sort(key=lambda page: (page.order, page.title, page.slug))
        sections.append(section)

    if not sections:
        raise BuildError("content/ 里还没有任何分区。请创建 content/分区名/index.md。")

    sections.sort(key=lambda section: (section.order, section.title, section.slug))
    return sections


# ---------------------------------------------------------------------------
# Markdown 渲染（够用、无依赖）
# ---------------------------------------------------------------------------

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+.-]*)\s*$")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
LIST_RE = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?")
CODE_RE = re.compile(r"`([^`\n]+)`")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+[\"']([^\"']*)[\"'])?\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+[\"']([^\"']*)[\"'])?\)")
STRONG_RE = re.compile(r"\*\*(.+?)\*\*")
STRONG_UNDERSCORE_RE = re.compile(r"__(.+?)__")
DEL_RE = re.compile(r"~~(.+?)~~")
EM_STAR_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
EM_UNDERSCORE_RE = re.compile(r"(?<!\w)_(?!_)(.+?)(?<!\w)_(?!\w)")


def escape_text(value: str) -> str:
    return html.escape(value, quote=False)


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)


def safe_url(value: str) -> str:
    value = html.unescape(value).strip()
    if re.match(r"(?i)^(?:javascript|vbscript|data):", value):
        return "#"
    # 让作者可以直接链接 Markdown 文件，生成时自动改成网页地址。
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value) and not value.startswith("//"):
        value = re.sub(r"\.md((?:#[^)]*)?)$", r".html\1", value, flags=re.IGNORECASE)
    return escape_attr(value)


def inline_markdown(text: str) -> str:
    code_spans: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_spans.append(escape_text(match.group(1)))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    text = CODE_RE.sub(stash_code, text)
    text = escape_text(text)

    def image(match: re.Match[str]) -> str:
        alt = escape_attr(html.unescape(match.group(1)))
        src = safe_url(match.group(2))
        title = match.group(3)
        title_attr = f' title="{escape_attr(html.unescape(title))}"' if title else ""
        return f'<img src="{src}" alt="{alt}" loading="lazy"{title_attr}>'

    def link(match: re.Match[str]) -> str:
        href = safe_url(match.group(2))
        title = match.group(3)
        title_attr = f' title="{escape_attr(html.unescape(title))}"' if title else ""
        return f'<a href="{href}"{title_attr}>{match.group(1)}</a>'

    text = IMAGE_RE.sub(image, text)
    text = LINK_RE.sub(link, text)
    text = STRONG_RE.sub(r"<strong>\1</strong>", text)
    text = STRONG_UNDERSCORE_RE.sub(r"<strong>\1</strong>", text)
    text = DEL_RE.sub(r"<del>\1</del>", text)
    text = EM_STAR_RE.sub(r"<em>\1</em>", text)
    text = EM_UNDERSCORE_RE.sub(r"<em>\1</em>", text)

    for index, code in enumerate(code_spans):
        text = text.replace(f"\x00CODE{index}\x00", f"<code>{code}</code>")

    return re.sub(r" {2,}\n", "<br>\n", text)


def is_hr(line: str) -> bool:
    return bool(
        re.fullmatch(
            r"\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})",
            line,
        )
    )


def split_table_row(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|") and not value.endswith("\\|"):
        value = value[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", value)]


def is_table_separator(line: str, columns: int) -> bool:
    if "|" not in line:
        return False
    cells = split_table_row(line)
    return len(cells) == columns and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells
    )


def table_alignment(cell: str) -> str:
    left = cell.startswith(":")
    right = cell.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    return "left"


def is_block_start(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not line.strip():
        return True
    if FENCE_RE.match(line) or HEADING_RE.match(line) or is_hr(line):
        return True
    if QUOTE_RE.match(line) or LIST_RE.match(line):
        return True
    if index + 1 < len(lines) and "|" in line:
        columns = len(split_table_row(line))
        if columns > 1 and is_table_separator(lines[index + 1], columns):
            return True
    return False


def render_list_item(parts: list[str]) -> str:
    text = "\n".join(parts).strip()
    if not text:
        return ""
    rendered = markdown_to_html(text)
    rendered = re.sub(r"^<p>(.*?)</p>", r"\1", rendered, count=1, flags=re.S)
    return rendered


def parse_list(lines: list[str], start: int) -> tuple[str, int]:
    first = LIST_RE.match(lines[start])
    assert first is not None
    base_indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start_number = int(re.match(r"\d+", first.group(2)).group(0)) if ordered else 1

    items: list[list[str]] = []
    current: list[str] | None = None
    i = start
    n = len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                next_indent = len(lines[j]) - len(lines[j].lstrip())
                next_match = LIST_RE.match(lines[j])
                next_ordered = (
                    next_match.group(2)[0].isdigit() if next_match is not None else None
                )
                if next_indent > base_indent or (
                    next_match is not None
                    and next_indent == base_indent
                    and next_ordered == ordered
                ):
                    if current is not None:
                        current.append("")
                    i += 1
                    continue
            break

        match = LIST_RE.match(line)
        indent = len(line) - len(line.lstrip())

        if match and indent == base_indent:
            item_ordered = match.group(2)[0].isdigit()
            if item_ordered != ordered:
                break
            if current is not None:
                items.append(current)
            current = [match.group(3)]
            i += 1
            continue

        if current is not None and (
            indent > base_indent or not is_block_start(lines, i)
        ):
            remove = min(len(line), base_indent + 2)
            current.append(line[remove:] if line[:remove].isspace() else line.lstrip())
            i += 1
            continue

        break

    if current is not None:
        items.append(current)

    tag = "ol" if ordered else "ul"
    start_attr = f' start="{start_number}"' if ordered and start_number != 1 else ""
    body = "\n".join(
        f"<li>{render_list_item(item)}</li>" for item in items if any(part.strip() for part in item)
    )
    return f"<{tag}{start_attr}>\n{body}\n</{tag}>", i


def markdown_to_html(source: str) -> str:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            language = fence.group(2)
            i += 1
            code: list[str] = []
            while i < n and not re.fullmatch(
                rf"\s*{re.escape(marker[0])}{{{len(marker)},}}\s*", lines[i]
            ):
                code.append(lines[i])
                i += 1
            if i < n:
                i += 1
            class_attr = f' class="language-{escape_attr(language)}"' if language else ""
            output.append(
                f"<pre><code{class_attr}>{escape_text(chr(10).join(code))}</code></pre>"
            )
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            i += 1
            continue

        if is_hr(line):
            output.append("<hr>")
            i += 1
            continue

        if i + 1 < n and "|" in line:
            columns = len(split_table_row(line))
            if columns > 1 and is_table_separator(lines[i + 1], columns):
                headers = split_table_row(line)
                alignments = [table_alignment(cell) for cell in split_table_row(lines[i + 1])]
                i += 2
                rows: list[list[str]] = []
                while i < n and lines[i].strip() and "|" in lines[i]:
                    # 表格在空行处结束；如果紧跟着标题、列表等块，也在这里停下。
                    if (
                        FENCE_RE.match(lines[i])
                        or HEADING_RE.match(lines[i])
                        or QUOTE_RE.match(lines[i])
                        or LIST_RE.match(lines[i])
                    ):
                        break
                    cells = split_table_row(lines[i])
                    cells = (cells + [""] * columns)[:columns]
                    rows.append(cells)
                    i += 1
                header_html = "".join(
                    f'<th class="align-{alignments[index]}">{inline_markdown(cell)}</th>'
                    for index, cell in enumerate(headers)
                )
                row_html = []
                for row in rows:
                    row_html.append(
                        "<tr>"
                        + "".join(
                            f'<td class="align-{alignments[index]}">{inline_markdown(cell)}</td>'
                            for index, cell in enumerate(row)
                        )
                        + "</tr>"
                    )
                output.append(
                    '<div class="table-wrap"><table><thead><tr>'
                    + header_html
                    + "</tr></thead><tbody>"
                    + "".join(row_html)
                    + "</tbody></table></div>"
                )
                continue

        if QUOTE_RE.match(line):
            quote_lines: list[str] = []
            while i < n:
                if QUOTE_RE.match(lines[i]):
                    quote_lines.append(QUOTE_RE.sub("", lines[i], count=1))
                    i += 1
                    continue
                if not lines[i].strip():
                    j = i + 1
                    while j < n and not lines[j].strip():
                        j += 1
                    if j < n and QUOTE_RE.match(lines[j]):
                        quote_lines.append("")
                        i += 1
                        continue
                break
            output.append(
                "<blockquote>\n"
                + markdown_to_html("\n".join(quote_lines))
                + "\n</blockquote>"
            )
            continue

        if LIST_RE.match(line):
            rendered_list, i = parse_list(lines, i)
            output.append(rendered_list)
            continue

        paragraph: list[str] = []
        while i < n and lines[i].strip() and not is_block_start(lines, i):
            paragraph.append(lines[i].strip())
            i += 1
        if paragraph:
            output.append(f"<p>{inline_markdown(chr(10).join(paragraph))}</p>")

    return "\n".join(output)


# ---------------------------------------------------------------------------
# 页面模板（读取 templates/layout.html）
# ---------------------------------------------------------------------------


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def make_description(text: str, limit: int = 80) -> str:
    plain = re.sub(r"[#>*`\-|\[\]()!]", " ", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit]


def layout(
    *,
    title: str,
    rel: str,
    content: str,
    body_class: str = "",
    description: str = "",
) -> str:
    full_title = SITE_NAME if title == SITE_NAME else f"{title} · {SITE_NAME}"

    if not LAYOUT_TEMPLATE.is_file():
        raise BuildError(
            "找不到 templates/layout.html。请确认模板文件没有删除或移动；"
            "它定义了整站页面的骨架。"
        )

    template = LAYOUT_TEMPLATE.read_text(encoding="utf-8")

    values = {
        "TITLE": escape_text(full_title),
        "DESCRIPTION": escape_attr(description or full_title),
        "REL": rel,
        "BODY_CLASS": body_class,
        "CONTENT": content,
        "SITE_NAME": SITE_NAME,
        "REPO_URL": REPO_URL,
    }

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise BuildError(
                f"templates/layout.html 里有未知占位符 {{{{ {key} }}}}。"
                f"可用的是：{', '.join(sorted(values))}。"
            )
        return values[key]

    return PLACEHOLDER_RE.sub(replace, template)


def render_home(sections: list[Section]) -> str:
    rows = []
    for index, section in enumerate(sections, start=1):
        rows.append(
            f"""<a class="index-row" href="{section.slug}/index.html">
          <span class="index-number">{index:02d}</span>
          <span class="index-title">{escape_text(section.title)}</span>
          <span class="index-arrow" aria-hidden="true">→</span>
        </a>"""
        )

    page_count = sum(len(section.pages) for section in sections)
    content = f"""<main id="main">
    <section class="hero shell">
      <h1>{SITE_NAME}</h1>
    </section>

    <section class="index-block shell" id="index">
      <div class="section-heading">
        <h2>页面索引</h2>
      </div>
      <div class="index-list">
        {''.join(rows)}
      </div>
    </section>
  </main>"""
    return layout(
        title=SITE_NAME,
        rel="",
        content=content,
        body_class="home",
        description=f"{SITE_NAME}：{len(sections)} 个分区，{page_count} 篇条目。",
    )


def render_page_rows(section: Section) -> str:
    if not section.pages:
        return '<p class="empty-note">暂无页面。</p>'
    rows = []
    for index, page in enumerate(section.pages, start=1):
        rows.append(
            f"""<a class="page-row" href="{page.slug}.html">
          <span class="page-number">{index:02d}</span>
          <span class="page-title">{escape_text(page.title)}</span>
          <span class="page-arrow" aria-hidden="true">→</span>
        </a>"""
        )
    return "".join(rows)


def render_section(section: Section) -> str:
    article_html = markdown_to_html(section.body).strip()
    article_block = (
        f'<article class="article">\n      {article_html}\n    </article>'
        if article_html
        else ""
    )
    child_class = "child-index" if article_html else "child-index child-index--flush"

    content = f"""<main id="main" class="shell page-shell">
    <nav class="breadcrumb" aria-label="面包屑">
      <a href="../index.html">首页</a>
      <span aria-hidden="true">/</span>
      <span aria-current="page">{escape_text(section.title)}</span>
    </nav>

    <header class="page-hero">
      <h1>{escape_text(section.title)}</h1>
    </header>

    {article_block}

    <section class="{child_class}" aria-labelledby="child-index-title">
      <div class="section-heading">
        <h2 id="child-index-title">本区页面</h2>
      </div>
      <div class="page-list">
        {render_page_rows(section)}
      </div>
    </section>

    <nav class="back-nav" aria-label="返回">
      <a href="../index.html#index">← 返回页面索引</a>
    </nav>
  </main>"""
    return layout(
        title=section.title,
        rel="../",
        content=content,
        body_class="inner",
        description=make_description(section.body) or f"{SITE_NAME} · {section.title}",
    )


def render_page(page: Page, page_index: int) -> str:
    section = page.section
    assert section is not None
    pages = section.pages
    position = page_index - 1
    previous_page = pages[position - 1] if position > 0 else None
    next_page = pages[position + 1] if position + 1 < len(pages) else None

    if previous_page:
        left_href = f"{previous_page.slug}.html"
        left_label = "上一篇"
        left_title = f"← {escape_text(previous_page.title)}"
    else:
        left_href = "index.html"
        left_label = "返回分区"
        left_title = f"← {escape_text(section.title)}"

    if next_page:
        right_href = f"{next_page.slug}.html"
        right_label = "下一篇"
        right_title = f"{escape_text(next_page.title)} →"
    else:
        right_href = "../index.html#index"
        right_label = "页面索引"
        right_title = "返回索引 ↑"

    content = f"""<main id="main" class="shell page-shell">
    <nav class="breadcrumb" aria-label="面包屑">
      <a href="../index.html">首页</a>
      <span aria-hidden="true">/</span>
      <a href="index.html">{escape_text(section.title)}</a>
      <span aria-hidden="true">/</span>
      <span aria-current="page">{escape_text(page.title)}</span>
    </nav>

    <header class="page-hero">
      <h1>{escape_text(page.title)}</h1>
    </header>

    <article class="article">
      {markdown_to_html(page.body)}
    </article>

    <nav class="page-pager" aria-label="翻页">
      <a class="pager-link" href="{left_href}">
        <span class="pager-label">{left_label}</span>
        <span class="pager-title">{left_title}</span>
      </a>
      <a class="pager-link pager-next" href="{right_href}">
        <span class="pager-label">{right_label}</span>
        <span class="pager-title">{right_title}</span>
      </a>
    </nav>
  </main>"""
    return layout(
        title=page.title,
        rel="../",
        content=content,
        body_class="inner",
        description=make_description(page.body) or f"{SITE_NAME} · {page.title}",
    )


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------


def copy_content_assets(source: Path, destination: Path) -> None:
    """把 Markdown 旁边的图片等文件复制到网页目录，保持相对路径可用。"""
    for item in source.iterdir():
        if item.name.startswith(".") or item.is_symlink():
            continue
        target = destination / item.name
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            copy_content_assets(item, target)
        elif item.suffix.lower() != ".md":
            shutil.copy2(item, target)


def build() -> None:
    if not LAYOUT_TEMPLATE.is_file():
        raise BuildError(
            "找不到 templates/layout.html。整站页面骨架由它定义，"
            "请创建该文件后再生成。"
        )

    sections = load_site()

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")

    (DIST_DIR / "index.html").write_text(render_home(sections), encoding="utf-8")

    page_count = 0
    for section in sections:
        section_dir = DIST_DIR / section.slug
        section_dir.mkdir(parents=True, exist_ok=True)
        copy_content_assets(section.source, section_dir)

        (section_dir / "index.html").write_text(
            render_section(section), encoding="utf-8"
        )

        for page_index, page in enumerate(section.pages, start=1):
            (section_dir / f"{page.slug}.html").write_text(
                render_page(page, page_index), encoding="utf-8"
            )
            page_count += 1

    print("生成完成。")
    print(f"  dist/index.html")
    print(f"  分区 {len(sections)} 个 / 页面 {page_count} 篇")
    print("  直接双击 dist/index.html 即可查看。")


def main() -> int:
    try:
        build()
    except BuildError as error:
        print(f"\n内容有误：{error}\n", file=sys.stderr)
        return 1
    except Exception as error:  # 给非技术维护者一个明确的失败提示
        print(f"\n生成失败：{error}\n", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
